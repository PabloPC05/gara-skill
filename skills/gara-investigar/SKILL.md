---
name: "gara-investigar"
description: "Investiga una pregunta científica, técnica o de negocio de Gara y produce un dosier con fuentes trazables y revisión crítica."
---

# Investigación Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional según el tamaño del dosier y la independencia de sus ángulos. El coordinador selecciona `gara-rastreador` para recoger fuentes por ángulo con prefijo y rutas propios; recibe pregunta, periodo, clases de fuentes y contrato de fichas, y devuelve fichas, índice y huecos. Selecciona `gara-investigador` cuando un ámbito necesita síntesis separada: recibe pregunta y fichas reales, escribe su dosier parcial en una ruta propia y devuelve hechos, inferencias y pendientes. Selecciona `gara-contrastador` para contrastar informe y fichas con contexto fresco; recibe esos archivos y fecha de referencia, devuelve afirmaciones sustentadas, contradichas o no acreditadas y evidencia, sin editar el informe.

Lee el [contrato de delegación](references/delegation.md) antes de repartir. Ningún investigador lanza rastreadores: solicita al coordinador los encargos necesarios. El coordinador integra `INFORME.md`. Sin agentes, recoge, sintetiza y contrasta secuencialmente e indica que faltó contraste independiente; `--rapido` conserva su límite explícito sin contraste. Si falta acceso a fuentes, declara la cobertura pendiente.

Define la pregunta, periodo y decisión que debe informar. Reparte recogida por clase de fuente y perspectivas, no por subtemas solapados. Usa fuentes primarias y fichas con autor, fecha, URL, extracto y límites. Si hay delegación, el coordinador selecciona gara-rastreador, gara-investigador y gara-contrastador según el contrato anterior; no dependas de delegación anidada. Sintetiza sobre las fichas y distingue resultados científicos de hipótesis. Verifica vigencia y fuentes realmente independientes. --rapido reduce profundidad y explicita incertidumbre; no inventa citas ni conclusiones.

Antes de recoger, lee el [método y contrato de fichas](references/method.md). Reanuda desde archivos existentes y entrega INFORME.md con citas, cobertura, contradicciones y límites.
