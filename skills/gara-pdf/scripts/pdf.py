"""Offline HTML-to-PDF rendering with configurable Gara identity."""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class PdfError(Exception):
    """A reported failure, rather than an unhandled exception."""


def find_browser(explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        if candidate.is_file():
            return candidate.resolve()
        raise PdfError("El navegador configurado no existe.")
    candidates = []
    for name in ("chrome", "chromium", "chromium-browser", "google-chrome", "msedge"):
        if found := shutil.which(name):
            candidates.append(Path(found))
    for base in (
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
    ):
        if base:
            candidates += [
                Path(base) / "Google/Chrome/Application/chrome.exe",
                Path(base) / "Microsoft/Edge/Application/msedge.exe",
            ]
    candidates += [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    ]
    caches = [
        Path.home() / "AppData/Local/ms-playwright",
        Path.home() / ".cache/ms-playwright",
        Path.home() / "Library/Caches/ms-playwright",
    ]
    for cache in caches:
        for pattern in (
            "chromium_headless_shell-*/chrome-headless-shell-win*/chrome-headless-shell.exe",
            "chromium_headless_shell-*/chrome-linux*/headless_shell",
            "chromium-*/chrome-win*/chrome.exe",
            "chromium-*/chrome-linux*/chrome",
        ):
            candidates += sorted(cache.glob(pattern), reverse=True)
    return next((p.resolve() for p in candidates if p.is_file()), None)


def data_url(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def document(body: str, meta: dict, assets: Path) -> str:
    if not isinstance(meta.get("title"), str) or not meta["title"].strip():
        raise PdfError("Los metadatos necesitan un título.")
    stylesheet = (assets / "gara-style.css").read_text(encoding="utf-8")
    footer = json.dumps(
        str(meta.get("footer", "Gara · Investigación y análisis estructural")),
        ensure_ascii=False,
    )
    stylesheet = stylesheet.replace(
        "__FOOTER__", footer.replace("<", "\\3c ").replace(">", "\\3e ")
    )
    fonts = ""
    for weight in (400, 700):
        font = assets / "fonts" / f"Lato-{weight}.ttf"
        if font.is_file():
            fonts += f"@font-face{{font-family:Lato;font-weight:{weight};src:url('{data_url(font, 'font/ttf')}')}}"
    logo = data_url(assets / "gara-logo.png", "image/png")
    fields = "".join(
        f"<dt>{html.escape(label)}</dt><dd>{html.escape(str(meta[key]))}</dd>"
        for key, label in (
            ("project", "Proyecto"),
            ("author", "Autoría"),
            ("date", "Fecha"),
            ("reference", "Referencia"),
            ("client", "Destinatario"),
        )
        if meta.get(key)
    )
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:">
<title>{html.escape(meta["title"])}</title><style>{fonts}{stylesheet}</style></head><body>
<header><img src="{logo}" alt="Gara"><span>Gara · Análisis estructural</span></header>
<section class="cover"><p class="eyebrow">{html.escape(str(meta.get("eyebrow", "DOCUMENTO DE PROYECTO")))}</p>
<h1>{html.escape(meta["title"])}</h1><dl>{fields}</dl></section>
<main>{body}</main><footer>{html.escape(str(meta.get("footer", "Gara · Investigación y análisis estructural")))}</footer>
</body></html>"""


def render(
    body: str,
    meta: dict,
    output: Path,
    assets: Path,
    *,
    browser: str | None = None,
    keep_html: bool = False,
) -> Path:
    executable = find_browser(browser)
    if not executable:
        raise PdfError(
            "No se encontró un navegador para PDF. Usa --browser con Chrome, Chromium o Edge."
        )
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    content = document(body, meta, assets)
    with tempfile.TemporaryDirectory(prefix="gara-pdf-") as temporary:
        root = Path(temporary)
        source = root / "document.html"
        source.write_text(content, encoding="utf-8")
        rendered = root / "document.pdf"
        command = [
            str(executable),
            "--headless",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--disable-background-networking",
            "--timeout=20000",
            f"--user-data-dir={root / 'profile'}",
            f"--print-to-pdf={rendered}",
            source.as_uri(),
        ]
        code = subprocess.run(
            command,
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=60,
        ).returncode
        if (
            code
            or not rendered.is_file()
            or not rendered.read_bytes().startswith(b"%PDF-")
        ):
            raise PdfError("El navegador no generó un PDF válido.")
        shutil.copyfile(rendered, output)
    if keep_html:
        output.with_suffix(".html").write_text(content, encoding="utf-8")
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera un PDF autocontenido con marca Gara."
    )
    parser.add_argument("--content", type=Path, required=True)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--browser")
    parser.add_argument("--keep-html", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.keep_html and args.out.with_suffix(".html").resolve() == (
            args.content.resolve()
        ):
            raise PdfError(
                "--keep-html sobrescribiría el contenido de entrada; cambia --out o --content."
            )
        render(
            args.content.read_text(encoding="utf-8"),
            json.loads(args.meta.read_text(encoding="utf-8")),
            args.out,
            args.assets,
            browser=args.browser,
            keep_html=args.keep_html,
        )
        print(args.out.resolve())
        return 0
    except (PdfError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Error: {error}")
        return 1
