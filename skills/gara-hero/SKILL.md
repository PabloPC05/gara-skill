---
name: "gara-hero"
description: "Genera variantes comparables de portada o hero para comunicar Gara a una audiencia concreta; usar solo cuando pidas explícitamente opciones de portada para comparar, no para modificar el hero de la aplicación (gara-frontend-design)."
disable-model-invocation: true
---

# Opciones de portada Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional, bajo el [contrato de delegación](references/delegation.md): usa `gara-disenador` cuando varias variantes con direcciones independientes justifiquen repartir el trabajo; para una variante pequeña o sin agentes, diseña en esta sesión y conserva direcciones y salidas comparables.

1. Fija audiencia, objetivo, hechos demostrables y libertad visual autorizada. Si falta alguno, pregúntalo; no elijas una afirmación científica o comercial no verificada para mejorar el impacto.
2. Define direcciones visuales diferentes antes de repartir, para que no converjan a una plantilla. Confirma con el usuario la carpeta de salida; si no la hay, pregúntala antes de escribir.
3. Cada variante, propia o de un `gara-disenador`, es HTML autocontenido con contenido real y recursos autorizados, en un archivo exclusivo. Al diseñador entrégale audiencia, objetivo, contenido verificado, dirección asignada, tokens/recursos autorizados y su archivo; no compartas archivos de salida entre diseñadores.
4. Revisa lo devuelto, crea el índice comparativo local y explica diferencias y tradeoffs.

Termina devolviendo rutas, índice, decisiones visuales y límites (qué no se comprobó), y espera que el usuario elija o pida cambios. No publica, no hace commit ni encadena otras skills.
