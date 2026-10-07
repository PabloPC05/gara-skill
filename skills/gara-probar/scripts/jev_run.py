#!/usr/bin/env python3
"""Ejecuta un escenario con jev-ultrafast en el navegador de pruebas y devuelve un resumen JSON.

Se lanza dentro del entorno de jev-ultrafast:
uv run --project <jev> python jev_run.py --env-file <jev>/.env --cdp-url http://127.0.0.1:9333 \
    --url URL --goal "..." --record-dir DIR
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

DAEMON = "gara-pruebas"
LOCAL = {"localhost", "127.0.0.1", "[::1]", "::1"}

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument(
    "--env-file",
    type=Path,
    required=True,
    help="Configuración de jev; sus valores prevalecen sobre el entorno.",
)
parser.add_argument(
    "--cdp-url",
    required=True,
    help="Endpoint CDP del navegador dedicado a pruebas, p. ej. http://127.0.0.1:9333.",
)
parser.add_argument("--url", required=True)
parser.add_argument(
    "--goal",
    action="append",
    required=True,
    help="Objetivo con su condición de parada; repetir para una lista ordenada.",
)
parser.add_argument("--record-dir", type=Path, required=True)
parser.add_argument("--max-steps", type=int, default=40)
args = parser.parse_args()


def fail(message):
    json.dump({"status": "error", "error": message}, sys.stdout, ensure_ascii=False)
    print()
    sys.exit(2)


# Un navegador con páginas no locales abiertas no es el de pruebas: puede ser el
# personal del usuario, con sus sesiones. No se usa.
try:
    with urllib.request.urlopen(
        args.cdp_url.rstrip("/") + "/json/list", timeout=5
    ) as r:
        targets = json.load(r)
except OSError as exc:
    fail(f"No responde el navegador de pruebas en {args.cdp_url}: {exc}")
foreign = [
    t["url"]
    for t in targets
    if t.get("type") == "page"
    and urlparse(t["url"]).scheme in {"http", "https"}
    and urlparse(t["url"]).hostname not in LOCAL
]
if foreign:
    fail(
        f"{args.cdp_url} tiene páginas no locales abiertas ({len(foreign)}); "
        "no parece el navegador dedicado a pruebas. Usa otro puerto."
    )

# `uv run --env-file` no sobrescribe variables ya definidas: una TYPESAFE_API_KEY
# antigua en el entorno se usaría en lugar de la del .env.
for line in args.env_file.read_text(encoding="utf-8").splitlines():
    key, sep, value = line.strip().partition("=")
    if sep and key and not key.startswith("#"):
        os.environ[key.strip()] = value.strip().strip("'\"")
# Daemon propio: el "default" puede estar ya conectado a otro navegador.
# browser_harness lee estas variables al importarse.
os.environ["BU_CDP_URL"] = args.cdp_url
os.environ["BU_NAME"] = DAEMON
# Con el parche, pestaña en primer plano: en segundo plano Chromium deja de pintar
# y las capturas tras un clic se bloquean. En el navegador de pruebas no molesta.
os.environ["JEV_BACKGROUND_TAB"] = "0"

from browser_harness.admin import restart_daemon  # noqa: E402
from jev_ultrafast import Agent  # noqa: E402

status, state, error = "max-steps", None, None
try:
    with Agent(args.url, args.goal, record_dir=args.record_dir) as agent:
        try:
            for step, state in enumerate(agent.run(), start=1):
                if state["status"] in {"done", "blocked"}:
                    status = state["status"]
                    break
                if step >= args.max_steps:
                    break
        except Exception as exc:  # el navegador o el modelo fallaron a mitad
            status, error = "error", f"{type(exc).__name__}: {exc}"
            state = agent.snapshot()
except Exception as exc:
    status, error = "error", f"{type(exc).__name__}: {exc}"
finally:
    try:
        restart_daemon(DAEMON)
    except Exception:
        pass

page = state["page"] if state else {}
captures = sorted(args.record_dir.glob("*.jpg")) if args.record_dir.is_dir() else []
usage = [d.get("usage", {}) for d in (state or {}).get("decisions", [])]
summary = {
    # "done" solo significa que Jev cree haber terminado; hay que comprobarlo.
    "status": status,
    "error": error,
    "url": page.get("url"),
    "title": page.get("title"),
    "steps": len((state or {}).get("history", [])),
    "elapsed_ms": (state or {}).get("elapsed_ms"),
    "actions": [
        {k: h.get(k) for k in ("action", "kind", "text", "page_changed")}
        for h in (state or {}).get("history", [])
    ],
    "page_text": (page.get("text") or "")[:3000],
    "last_capture": str(captures[-1]) if captures else None,
    "input_tokens": sum(u.get("input_tokens", 0) for u in usage),
}
json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
print()
sys.exit(0 if status == "done" else 2)
