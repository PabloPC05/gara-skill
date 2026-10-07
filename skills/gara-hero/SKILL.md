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
3. Cada variante usa contenido real y recursos autorizados. Cada `gara-disenador` trabaja en su propio worktree de Git, así que puede modificar cualquier archivo sin pisar a los demás. Al diseñador entrégale audiencia, objetivo, contenido verificado, dirección asignada, tokens/recursos autorizados y qué debe producir (HTML autocontenido o cambios en la interfaz). Los worktrees parten de la rama por defecto: si la variante necesita cambios aún sin commitear, avísalo al usuario antes de lanzar.
4. Revisa lo devuelto (ruta del worktree, rama y archivos de cada variante), crea el índice comparativo local y explica diferencias y tradeoffs. No integres ninguna variante en el checkout principal: el usuario elige cuál fusionar y cuándo borrar los worktrees.

Termina devolviendo rutas, worktrees y ramas, índice, decisiones visuales y límites (qué no se comprobó), y espera que el usuario elija o pida cambios. No publica, no hace commit ni encadena otras skills.
