---
name: "gara-pdf"
description: "Genera PDFs de informes, memorias, propuestas o presupuestos de Gara con recursos gráficos embebidos y metadatos proporcionados."
---

# Documentos PDF Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe contenido, citas, metadatos y destino; entrega PDF renderizado, comprobación visual y límites. Si falta el renderer o un dato obligatorio, prepara lo disponible y registra lo pendiente. No requiere delegación.

Reúne contenido y metadatos, sin inventar datos fiscales o institucionales. Usa scripts/build_pdf.py con --content body.html --meta meta.json --out documento.pdf; las rutas del script y assets se resuelven respecto a esta skill. El renderer usa Lato y el logo de Gara, embedidos, y Chrome, Chromium o Edge local; --browser permite configurarlo. Todos los metadatos salvo title son opcionales. Conserva cifras y citas, comprueba el PDF renderizado y los saltos de página, tablas y caracteres españoles. Usa --keep-html para diagnosticar. Consulta la referencia de documento y estilos antes de componer.

## Referencias

- [document.md](references/document.md)
