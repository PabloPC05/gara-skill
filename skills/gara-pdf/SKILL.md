---
name: "gara-pdf"
description: "Genera un PDF de marca Gara (informe, memoria, propuesta o presupuesto) a partir de contenido y metadatos que aportas; usar cuando necesites el documento renderizado, no para redactar su contenido."
---

# Documentos PDF Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibes contenido, citas, metadatos y destino; entregas el PDF renderizado, su comprobación visual y los límites. Si falta el navegador o un dato obligatorio, prepara lo disponible y señala lo pendiente. Al terminar, devuelve la ruta del PDF y espera instrucciones: no lo envía, publica ni commitea.

## Helper autónomo

`scripts/build_pdf.py` importa `scripts/pdf.py` y usa solo la biblioteca estándar de Python 3.11+ más un Chrome, Chromium o Edge local (`--browser` fija el ejecutable). No depende de ningún otro paquete del repositorio, no usa red y deshabilita JavaScript y recursos remotos. Fuentes (Lato) y logo salen de `assets/`, y el script ya los localiza; ejecútalo desde el directorio de esta skill o con su ruta completa.

```powershell
py scripts/build_pdf.py --content body.html --meta meta.json --out documento.pdf
```

## Pasos

1. Reúne contenido y metadatos proporcionados. No inventes datos fiscales, institucionales ni cifras; conserva citas y números tal cual.
2. Consulta [document.md](references/document.md) para el formato del fragmento HTML y los metadatos (`title` obligatorio; el resto opcional).
3. Si `--out` ya existe, el script se niega a reemplazarlo. Pregunta al usuario: si lo confirma, repite con `--overwrite`; si no, usa otro nombre.
4. Renderiza. `--keep-html` deja un `.html` junto al PDF para diagnosticar; no lo uses con una entrada que se llame igual.
5. Comprueba el PDF renderizado, no el HTML: todas las páginas, saltos de página, tablas largas, caracteres españoles y texto extraíble. Informa de lo que no pudiste mirar.

## Referencias

- [document.md](references/document.md)
