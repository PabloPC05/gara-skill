from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gara_workflow.common import redact, redact_data, redacted_tail
from gara_workflow.engines import (
    gate_environment,
    parse_result,
    run_session,
    stop_owned_process,
)


MARKER = '<!-- gara-result --> {"status":"completed","summary":"ok"}'


def claude_result(**fields):
    return {"type": "result", "subtype": "success", "result": MARKER, **fields}


class SecretPersistence(unittest.TestCase):
    def test_escaped_quotes_inside_secret_do_not_leave_a_tail(self):
        secret = 'fixture-before"fixture-after'
        value = json.dumps({"api_key": secret})
        for encoded in (
            value,
            json.dumps(value),
            json.dumps(json.dumps(value)),
            "diagnóstico: " + json.dumps(value),
        ):
            with self.subTest(encoded=encoded):
                clean = redact(encoded)
                self.assertNotIn("fixture-before", clean)
                self.assertNotIn("fixture-after", clean)

    def test_json_and_escaped_json_secrets_are_removed(self):
        sensitive = {
            "api_key": "fixture-secret-api",
            "accessToken": "fixture-secret-access",
            "password": "fixture-secret-password",
            "authorization": "Bearer fixture-secret-bearer",
        }
        for value in (
            json.dumps(sensitive),
            json.dumps(json.dumps(sensitive)),
            "diagnóstico: " + json.dumps({"nested": [sensitive]}),
        ):
            with self.subTest(value=value):
                clean = redact(value)
                for secret in sensitive.values():
                    self.assertNotIn(secret, clean)
                self.assertIn("[REDACTED]", clean)

    def test_assignment_and_incomplete_escaped_json_are_scrubbed(self):
        values = [
            'MY_API_KEY="fixture-api secret"',
            "password='fixture-pass secret'",
            r"\"refresh_token\": \"fixture-refresh\",",
            '"api_key": "fixture-json" trailing',
            "Authorization: Bearer fixture-auth",
        ]
        for value in values:
            with self.subTest(value=value):
                self.assertNotIn("fixture-", redact(value))

    def test_structured_fields_preserve_usage_and_mask_sensitive_values(self):
        clean = redact_data(
            {
                "input_tokens": 4,
                "cached_input_tokens": 2,
                "details": [
                    {
                        "credentials": {"username": "fixture-user"},
                        "clientSecret": "fixture-client",
                    }
                ],
                "api_key": "fixture-key",
            }
        )
        self.assertEqual(clean["input_tokens"], 4)
        self.assertEqual(clean["cached_input_tokens"], 2)
        self.assertEqual(clean["details"][0]["credentials"], "[REDACTED]")
        self.assertNotIn("fixture-", json.dumps(clean))

    def test_native_session_persists_only_scrubbed_normalized_result(self):
        event = claude_result(
            result='<!-- gara-result --> {"status":"completed","summary":{"api_key":"fixture-summary"}}',
            usage={"input_tokens": 4, "access_token": "fixture-usage"},
        )
        lines = [
            json.dumps(event),
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Bash",
                                "input": {"command": "fixture-raw-secret"},
                            }
                        ]
                    },
                }
            ),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "session.json"
            with patch(
                "gara_workflow.engines.stream_process", return_value=(0, lines, "")
            ):
                result = run_session("claude", "prompt", root, log)
            self.assertEqual(result.status, "completed")
            stored = log.read_text(encoding="utf-8")
            self.assertNotIn("fixture-", stored)
            self.assertEqual(json.loads(stored)["usage"]["input_tokens"], 4)

    def test_escaped_secret_is_fully_scrubbed_in_persisted_native_summary(self):
        value = json.dumps(json.dumps({"api_key": 'fixture-before"fixture-after'}))
        event = claude_result(result=MARKER + "\ndiagnóstico: " + value)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "session.json"
            with patch(
                "gara_workflow.engines.stream_process",
                return_value=(0, [json.dumps(event)], ""),
            ):
                result = run_session("claude", "prompt", root, log)
            self.assertEqual(result.status, "completed")
            self.assertNotIn("fixture-", log.read_text(encoding="utf-8"))


class BroaderRedaction(unittest.TestCase):
    def test_other_authorization_schemes_hide_the_credential(self):
        for scheme in ("Token", "Basic", "Digest", "Bearer"):
            with self.subTest(scheme=scheme):
                clean = redact(f"Authorization: {scheme} fixture-credential-123")
                self.assertNotIn("fixture-credential-123", clean)

    def test_secret_key_assignments_and_known_token_shapes_are_removed(self):
        values = {
            "SECRET_KEY=django-fixture-secret": "django-fixture-secret",
            "STRIPE_SECRET_KEY: fixture-stripe": "fixture-stripe",
            "token ghp_" + "a" * 36: "a" * 36,
            "aws AKIA" + "B" * 16: "B" * 16,
            "jwt eyJhbGciOiJI.eyJzdWIiOiIx.c2lnbmF0dXJl": "c2lnbmF0dXJl",
            "db postgres://user:fixture-pass@host/app": "fixture-pass",
        }
        for text, secret in values.items():
            with self.subTest(text=text):
                self.assertNotIn(secret, redact(text))

    def test_private_key_blocks_are_removed_even_when_truncated(self):
        body = "-----BEGIN RSA PRIVATE KEY-----\nfixture-key-material\n"
        self.assertNotIn("fixture-key-material", redact(body))
        self.assertNotIn(
            "fixture-key-material", redact(body + "-----END RSA PRIVATE KEY-----")
        )

    def test_ordinary_keys_are_kept(self):
        self.assertIn("primary_key", redact("primary_key=id"))

    def test_scrubbing_happens_before_truncation(self):
        text = "x" * 50 + "\nAPI_TOKEN=fixture-tail-secret\n" + "y" * 20
        clean = redacted_tail(text, 40)
        self.assertNotIn("fixture-tail-secret", clean)
        # A cut that separates the key from its value must not leak the value.
        cut = redacted_tail("x\nAPI_TOKEN=fixture-tail-secret", 18)
        self.assertNotIn("fixture-tail-secret", cut)


class ClientResultParsing(unittest.TestCase):
    def codex(self, *messages):
        lines = [json.dumps({"type": "thread.started", "thread_id": "t"})]
        for text in messages:
            lines.append(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": text},
                    }
                )
            )
        lines.append(json.dumps({"type": "turn.completed", "usage": {}}))
        return parse_result("codex", 0, lines, "")

    def test_quoted_completed_marker_cannot_override_the_final_result(self):
        result = self.codex(
            '<!-- gara-result --> {"status":"completed"}',
            '<!-- gara-result --> {"status":"blocked","summary":"falta decisión"}',
        )
        self.assertEqual(result.status, "blocked")

    def test_completed_result_may_quote_a_login_message(self):
        result = self.codex(
            'La UI muestra "Please run /login". <!-- gara-result --> {"status":"completed"}'
        )
        self.assertEqual(result.status, "completed")

    def test_real_authentication_failure_still_blocks(self):
        result = self.codex("Not logged in. Please run /login")
        self.assertEqual(result.status, "blocked")

    def test_status_codes_inside_numbers_are_not_quota_errors(self):
        lines = [
            json.dumps({"type": "turn.failed", "error": {"message": "4290 failed"}})
        ]
        self.assertFalse(parse_result("codex", 1, lines, "").infrastructure)
        lines = [json.dumps({"type": "turn.failed", "error": {"message": "HTTP 429"}})]
        self.assertTrue(parse_result("codex", 1, lines, "").infrastructure)


class GateProcesses(unittest.TestCase):
    def test_gate_environment_drops_credentials_and_git_redirection(self):
        with patch.dict(
            "os.environ",
            {
                "GH_TOKEN": "fixture",
                "OPENAI_API_KEY": "fixture",
                "GIT_DIR": "elsewhere",
                "PATH": "fixture-path",
            },
        ):
            environment = gate_environment()
        self.assertEqual(environment["PATH"], "fixture-path")
        for name in ("GH_TOKEN", "OPENAI_API_KEY", "GIT_DIR"):
            self.assertNotIn(name, environment)

    def test_stopping_an_exited_or_vanished_process_does_not_raise(self):
        class Gone:
            pid = 2**22 + 12345
            returncode = None

            def poll(self):
                return None

            def wait(self, timeout=None):
                return 0

            def kill(self):
                raise ProcessLookupError

        stop_owned_process(Gone())


class DelegationEvidence(unittest.TestCase):
    def parse(self, engine, events):
        close = {"type": "turn.completed"} if engine == "codex" else claude_result()
        if engine == "codex":
            events = [
                *events,
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": MARKER},
                },
            ]
        return parse_result(
            engine, 0, [json.dumps(event) for event in [*events, close]], ""
        )

    def test_agent_names_in_prose_and_init_are_not_observed_delegation(self):
        result = self.parse(
            "claude",
            [
                {"type": "system", "subtype": "init", "agents": ["gara-verifier"]},
                claude_result(result=MARKER + " He usado gara-verifier"),
            ],
        )
        self.assertEqual(result.delegations, [])

    def test_codex_tool_success_does_not_imply_agent_completion(self):
        event = {
            "type": "item.completed",
            "item": {
                "id": "call-1",
                "type": "collab_tool_call",
                "tool": "spawn_agent",
                "receiver_thread_ids": ["child-1"],
                "status": "completed",
                "agents_states": {
                    "child-1": {
                        "status": "running",
                        "message": "fixture-private-result",
                    }
                },
                "prompt": "fixture-private-prompt",
            },
        }
        result = self.parse("codex", [event])
        self.assertEqual(result.delegations[0]["status"], "running")
        self.assertEqual(result.delegations[0]["tool_status"], "completed")
        self.assertNotIn("role", result.delegations[0])
        self.assertNotIn("fixture-private", json.dumps(result.delegations))

    def test_codex_wait_records_observed_agent_completion(self):
        event = {
            "type": "item.completed",
            "item": {
                "id": "wait-1",
                "type": "collab_tool_call",
                "tool": "wait",
                "receiver_thread_ids": ["child-1"],
                "status": "completed",
                "agents_states": {
                    "child-1": {
                        "status": "completed",
                        "message": "fixture-private-result",
                    }
                },
            },
        }
        result = self.parse("codex", [event])
        self.assertEqual(result.delegations[0]["agent_id"], "child-1")
        self.assertEqual(result.delegations[0]["status"], "completed")

    def test_claude_request_activity_and_return_are_distinct(self):
        request = {
            "type": "assistant",
            "session_id": "main-session",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool-1",
                        "name": "Agent",
                        "input": {
                            "subagent_type": "gara-verifier",
                            "prompt": "fixture-private-prompt",
                        },
                    }
                ]
            },
        }
        activity = {
            "type": "assistant",
            "parent_tool_use_id": "tool-1",
            "session_id": "child-session",
            "message": {
                "content": [{"type": "text", "text": "fixture-private-result"}]
            },
        }
        returned = {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool-1",
                        "content": "fixture-private-result\nagentId: child-1",
                    }
                ]
            },
        }
        result = self.parse("claude", [request, activity, returned])
        self.assertEqual(result.session_id, "main-session")
        self.assertEqual(
            [entry["status"] for entry in result.delegations],
            ["requested", "running", "returned"],
        )
        self.assertEqual(result.delegations[-1]["agent_id"], "child-1")
        self.assertNotIn("fixture-private", json.dumps(result.delegations))

    def test_unrelated_tool_return_cannot_fabricate_agent_observation(self):
        event = {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "unknown-tool",
                        "content": "agentId: fake-agent",
                    }
                ]
            },
        }
        self.assertEqual(self.parse("claude", [event]).delegations, [])

    def test_quoted_agent_id_is_not_confused_with_return_metadata(self):
        request = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool-1",
                        "name": "Agent",
                        "input": {"subagent_type": "gara-verifier"},
                    }
                ]
            },
        }
        for body, expected in [
            (
                "El test contiene `agentId: fixture-code`.\nagentId: actual-child",
                "actual-child",
            ),
            ("agentId: first-child\nagentId: second-child", ""),
        ]:
            returned = {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tool-1",
                            "content": body,
                        }
                    ]
                },
            }
            with self.subTest(body=body):
                result = self.parse("claude", [request, returned])
                self.assertEqual(result.delegations[-1]["agent_id"], expected)
                self.assertEqual(result.delegations[-1]["status"], "returned")

    def test_subagent_close_does_not_complete_main_session(self):
        result = parse_result(
            "claude", 0, [json.dumps(claude_result(parent_tool_use_id="tool-1"))], ""
        )
        self.assertEqual(result.status, "failed")

    def test_malformed_provider_fields_do_not_crash_parser(self):
        events = [
            {"type": []},
            {"type": "result", "usage": [], "result": []},
            {"type": "item.completed", "item": {"type": "agent_message", "text": {}}},
            {
                "type": "item.completed",
                "item": {
                    "type": "collab_tool_call",
                    "tool": [],
                    "receiver_thread_ids": [{}],
                },
            },
        ]
        for engine in ("codex", "claude"):
            with self.subTest(engine=engine):
                result = parse_result(
                    engine, 0, [json.dumps(event) for event in events], ""
                )
                self.assertIn(result.status, {"failed", "blocked"})


if __name__ == "__main__":
    unittest.main()
