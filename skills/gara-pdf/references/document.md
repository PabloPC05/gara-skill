# Composición y renderizado

Prepara un fragmento HTML semántico con el cuerpo, sin `html`, `head`, scripts ni una portada adicional. El renderer añade portada, cabecera y pie. Usa h2/h3, párrafos, listas y tablas con thead. `.page-break` inicia otra página; `.callout` destaca un dato. Revisa las tablas largas, los bloques mayores que una página y los caracteres acentuados.

Los metadatos JSON requieren `title`; `project`, `author`, `date`, `reference`, `client`, `eyebrow` y `footer` son opcionales. `client` es un destinatario proporcionado, no una entidad fiscal inferida. Las imágenes del cuerpo deben ser URLs data; los recursos remotos y JavaScript están deshabilitados. No incluyas credenciales.

```powershell
py scripts/build_pdf.py --content body.html --meta meta.json --out informe.pdf --keep-html
```

Resuelve el script desde el directorio de esta skill. Para otro navegador, añade `--browser C:/ruta/chrome.exe`. Necesita Python 3.11+ y Chrome, Chromium o Edge; no necesita ReportLab ni acceso de red. Lato regular/negrita y el logo están embebidos. El CSS de impresión usa la tipografía y paleta neutral del checkout de Gara; no cambia el diseño de la aplicación.

Los [ejemplos](../assets/examples/body.html) contienen un informe ficticio identificado como tal. Sustituye su contenido y [metadatos](../assets/examples/meta.json) por hechos proporcionados. Comprueba texto extraído y todas las páginas renderizadas antes de entregar.

Consulta la [procedencia](../assets/PROVENANCE.md) antes de redistribuir recursos.
