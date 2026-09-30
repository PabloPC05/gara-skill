# Investigación trazable y reanudable

## Delimitar y conservar

Registra pregunta, decisión que informa, periodo, ámbito y fecha de consulta. Usa `<slug>/fuentes/` e `<slug>/INFORME.md` en el directorio de trabajo autorizado. Si ya existen, inspecciona el estado y conserva fichas: una petición de continuar permite ampliar; iniciar otra pregunta material requiere otro slug o una decisión del usuario.

## Recoger

Elige clases de fuentes pertinentes: artículos y repositorios científicos, documentación técnica primaria, datos oficiales, sector, prensa especializada y perspectivas discrepantes. Explica ausencias relevantes. Si compensa separar la recogida, el coordinador encarga ángulos independientes a gara-rastreador con prefijos y rutas propios, ajustando las tandas a las capacidades reales. Comprueba el [contrato de delegación](delegation.md). Sin delegación disponible o autorizada, usa el mismo método secuencialmente.

Cada ficha `01-<fuente>.md` registra identificador, autor/organización, publicación, URL o DOI, fecha consultada, extracto breve, afirmación sustentada y límites. Respeta los límites de citas y licencias. Los prefijos evitan colisiones. `gara-rastreador` recibe pregunta, periodo, clase/perspectiva de fuente y este contrato; devuelve un índice de fichas y huecos. La síntesis lee los archivos, no resúmenes sucesivos de agentes.

Revisa actores ausentes, ángulos vacíos y afirmaciones centrales con una sola fuente. Dirige otra ronda a esos huecos; detente cuando no aporte información o el alcance autorizado se agote, explicando lo pendiente.

## Sintetizar y contrastar

INFORME.md abre con respuesta directa y método utilizado. Cada afirmación material enlaza su ficha y fuente; las deducciones propias están marcadas. No promedies contradicciones: explica qué evidencia resulta más fiable y por qué. Separa resultados científicos publicados, mediciones de Gara e hipótesis sin evaluar.

`gara-contrastador` recibe únicamente informe, fichas y fecha de referencia en una instancia nueva con contexto fresco. Devuelve por afirmación su estado y evidencia sin editar. El coordinador corrige problemas que cambian conclusiones y conserva límites irresolubles. Sin agentes, contrasta directamente y declara que faltó contexto independiente. `--rapido` hace una ronda de reconocimiento sin contraste y lo indica expresamente. Los dosieres destinados a propuestas o decisiones económicas requieren contraste proporcional a su importancia.

Cierra con respuesta, número de fichas, cobertura, huecos y rutas. HTML o PDF son vistas opcionales cuando se solicitan; INFORME.md conserva la fuente. Cuando un ámbito justifica síntesis separada, gara-investigador recibe pregunta y fichas reales, escribe un dosier parcial en una ruta propia y devuelve fuentes, inferencias y pendientes. Solicita al coordinador los encargos de gara-rastreador necesarios; no lanza agentes. El coordinador integra el informe final o realiza toda la síntesis directamente si no hay delegación.
