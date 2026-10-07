# Perfil Gara

Esta guía se aplica a Gara. Las instrucciones del checkout utilizado prevalecen sobre esta fotografía; no congeles inventarios, estados de Linear, cifras de auditorías ni comandos.

## Orientación

Lee `AGENTS.md`, `.ai/state.json`, `.ai/README.md`, `README.md`, `CONTRIBUTING.md` y las secciones pertinentes de `docs/LINEAR_WORKFLOW.md`. Comprueba HEAD y la relación con los commits de las evidencias reutilizadas. Una propuesta en `docs/adr/` o `docs/architecture/` no es una decisión adoptada.

Gara combina React/Vite/TypeScript, Zustand y Molstar en `frontend/`, con FastAPI, SQLAlchemy, Alembic e integraciones HPC en `python/`. Contrasta los detalles con el código. La interfaz ya tiene temas claro, oscuro y de sistema; reutiliza sus tokens y componentes.

## Autoridades y validación

`frontend/package.json`, `python/pyproject.toml` y el CI vigente determinan los comandos. Para cambios frontend, considera Vitest, ESLint, typecheck y build según alcance. Para backend, usa pytest y la selección de mypy del CI cuando corresponda. Ejecuta primero aceptación acotada; la verificación integrada cubre el conjunto afectado. No cambies thresholds, dependencias ni configuración de workers para ocultar un fallo.

Los cambios de esquema requieren modelos y migraciones Alembic coherentes. `sql/migrations/` es histórico. Para paquetes de plugins first-party, consulta el SDK público vigente y sus pruebas de contrato.

## Entrega

Antes de implementar, acredita asignación del issue e `In Progress` conforme al proceso actual. Usa la rama sugerida por Linear y una PR para integrar. Si las herramientas no permiten consultar Linear, pide al usuario que confirme asignación y estado, o registra el bloqueo; una confirmación suya cuenta como acreditación, pero no inventes estados.

Usa `gara-commit` para commits atómicos y narrativos en español. El rechazo del validador se corrige; no se elude. La entrega incluye documentación afectada y evidencias. La revisión de un agente no equivale a la revisión humana exigida para `Done`; respeta las excepciones explícitas vigentes, sin ampliarlas.

## Contexto persistente y alcance

Conserva cambios previos. Distingue hechos observados, mediciones e inferencias. Actualiza únicamente la memoria afectada y conserva el commit de mediciones no repetidas. Los documentos del flujo representan requisitos, diseño y ejecución; no sustituyen a `.ai/` ni al estado de Linear.

Una autorización para adaptar o probar skills no autoriza trabajos HPC reales, acceso a datos científicos privados ni cambios en producción. Para desarrollo y pruebas de la herramienta, usa fallos simulados y repositorios temporales. Nunca incluyas credenciales o contenidos de `.env` en prompts, logs o documentos.
