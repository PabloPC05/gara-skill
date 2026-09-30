from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gara_workflow.common import redact, redact_data
from gara_workflow.engines import parse_result, run_session


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
