#!/usr/bin/env python3
"""Initial, reviewable conversion. Refuse to regenerate existing canonical skills."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gara_workflow.common import ROOT, WorkflowError, atomic_write, save_json
from gara_workflow.packaging import header


CORE = {
    "gara-spec": (
        "Especificación Gara",
        "Define requisitos observables antes de implementar",
        "Define y documenta requisitos de una feature o incidente de Gara mediante una entrevista basada en hechos; usar antes de decidir la implementación.",
        """
Explora el checkout y las evidencias antes de preguntar. Entrevista sobre resultados de producto, fallos, recuperación y exclusiones; las decisiones técnicas corresponden a gara-plan. Agrupa de una a tres decisiones independientes por ronda, con opciones y consecuencias. Resuelve hechos mediante herramientas y usa criterio para detalles reversibles dentro del alcance.

Escribe una SPEC autocontenida en `specs/<slug>/SPEC.md`, con issue real, requisitos R1, R2 y escenarios de aceptación. Distingue observaciones de hipótesis y no infieras una causa remota de un síntoma. Para interfaz, usa el sistema visual vigente; si no existe documentación suficiente, deriva lo comprobable del código y pregunta únicamente decisiones nuevas.

Registra las decisiones materiales pendientes como bloqueos. `approved: true` solo refleja una autorización real para esa versión, incluida una autorización ya dada en la conversación. La ausencia de respuesta no aprueba. Una petición de investigar o planificar conserva ese alcance.

Para cambios pequeños, usa una especificación proporcional; no impongas una entrevista extensa. Consulta el contrato de artefactos antes de preparar una ejecución automática.
""",
    ),
    "gara-plan": (
        "Plan técnico Gara",
        "Convierte requisitos en contratos técnicos verificables",
        "Diseña la arquitectura y validación de una SPEC autorizada de Gara; usar antes de dividir el trabajo en tareas.",
        """
Lee la SPEC y el código actual: módulos afectados, tipos, consumidores, tests y configuración. Comprueba supuestos contra HEAD; un diseño basado en un baseline histórico no describe automáticamente el checkout.

Escribe exclusivamente PLAN.md: contratos literales, estados y errores, restricciones, fuera de alcance, integración y traducción de cada aceptación a una prueba o comando real. Resuelve preguntas técnicas mediante exploración o documentación primaria; una decisión material de producto vuelve al usuario.

No implementes ni dividas en tareas. Los cambios de esquema incluyen modelo y migración Alembic; los plugins respetan su SDK público. Para frontend, identifica flujos y estados que requieren comprobación visual contra los tokens existentes.

Planifica justo antes de construir. El plan queda estable durante ejecución y verificación; un cambio sustancial abre una versión nueva. Ante un supuesto falso o una autorización ausente, escribe `## Bloqueado`. Respeta el modo de conversación y sus posibilidades reales de escritura.
""",
    ),
    "gara-tasks": (
        "Tareas Gara",
        "Programa tareas con dependencias y aceptación ejecutable",
        "Transforma PLAN.md y SPEC.md de Gara en un contrato TAREAS.md ejecutable, con cobertura de requisitos, dependencias y tandas.",
        """
Lee el plan completo y copia en cada briefing los contratos que necesita su implementador. Cada tarea declara ID, requisitos, dependencias, archivos concretos, resultados, aceptación y estado. No inventes arquitectura ni modifiques el plan.

Escribe el bloque gara-tasks:v1 del contrato de artefactos. Todas las R de la SPEC quedan cubiertas por aceptación ejecutable. Usa rutas reales, argv sin shell y directorios de trabajo explícitos. No sustituyas una comprobación de comportamiento por un comando que siempre sale con éxito.

Programa contratos y pruebas de interfaz entre módulos antes que sus consumidores. Ordena por dependencias, colisiones y recursos; prioriza riesgo en tareas independientes. Cada tanda tiene hasta tres tareas, carga máxima 4 y ningún escritor sobre los mismos archivos. Adapta el paralelismo a las capacidades y límites del entorno; un entorno sin subagentes trabaja secuencialmente.

Si el plan omite una decisión necesaria, documenta el hueco y bloquea lo dependiente. Los checkpoints señalan una comprobación humana concreta. Una revisión visual cierra el bloque de frontend cuando la pantalla completa ya existe.
""",
    ),
    "gara-build": (
        "Construcción Gara",
        "Implementa tandas ya especificadas y verifica su alcance",
        "Implementa tareas de TAREAS.md de Gara siguiendo los contratos y el horario autorizado, con validación concreta y progreso reanudable.",
        """
Comprueba issue, asignación y rama conforme al proceso de Gara. Lee TAREAS.md y los archivos asignados; consulta solo las secciones del plan necesarias. Un briefing incompleto se registra como hueco, no se convierte silenciosamente en una decisión nueva.

Ejecuta las tandas programadas. Pasa cada tarea íntegra a gara-implementer si la delegación nativa está disponible y autorizada. No lances otro CLI dentro de la sesión. Si no hay agentes, ejecuta las tareas en orden y declara la limitación. Evita escritores simultáneos y suites paralelas que compartan recursos.

En ejecución guiada, ejecuta aceptación y conserva salida real antes de marcar verificado. En el ejecutor automático, este realiza la aceptación, escribe estados y solicita el commit después; no anticipes esos pasos ni cambies el contrato JSON. Los estados provisionales no son evidencia.

Conserva cambios previos, no amplíes el alcance y usa gara-commit para registros autorizados. Tras una interrupción, comprueba lo construido antes de repetir; un envío HPC incierto nunca se reenvía por deducción. Detén tareas dependientes si falta una decisión o permiso y continúa lo independiente cuando sea posible.
""",
    ),
    "gara-verify": (
        "Verificación Gara",
        "Contrasta requisitos, código y evidencia de aceptación",
        "Verifica una implementación de Gara contra SPEC, PLAN y TAREAS, ejecutando criterios de aceptación y documentando desviaciones.",
        """
Comprueba qué está construido realmente; una tarea pendiente o bloqueada impide declarar completa la feature. En contexto fresco, usa gara-verifier cuando esté disponible para revisar la correspondencia requisito, contrato, código y aceptación.

Ejecuta los criterios pertinentes y conserva SHA, comandos y salida real en REVISION.md. Para UI, recorre los flujos afectados con un navegador real cuando esté disponible y explica lo que no pudo comprobarse. No atribuyas resultados locales a CI remoto ni a producción.

Corrige desviaciones del alcance autorizado y valida las rutas afectadas. No edites SPEC, PLAN ni el contrato de aceptación para adaptar la promesa al resultado. Si el requisito exige una decisión nueva o cambiar arquitectura, registra el bloqueo y prepara una versión nueva.

Reconciliar contexto significa actualizar solo documentación y memoria afectadas, manteniendo commits de mediciones no repetidas. Usa gara-commit para las correcciones. Termina listo para revisión, sujeto al proceso humano de Gara; la revisión genérica de corrección corresponde a gara-review.
""",
    ),
    "gara-review": (
        "Revisión de corrección Gara",
        "Busca fallos reproducibles en un diff con contexto fresco",
        "Revisa un diff de Gara para encontrar fallos de corrección, regresiones y pruebas ausentes, independientemente de la conformidad con el plan.",
        """
Parte del diff y sus consumidores con contexto fresco. Busca errores de comportamiento, contratos rotos, autorización, estados concurrentes y casos límite. Investiga cada candidato y reproduce cuando sea posible; no presentes sospechas como fallos confirmados.

Clasifica por impacto y aporta ubicación, desencadenante y evidencia. Si hay un revisor nativo disponible y autorizado, usa uno distinto del implementador. Si no lo hay, declara la limitación; otra sesión técnica tampoco sustituye la aprobación humana exigida por Gara.

Corrige solo fallos dentro del alcance y con autorización existente. Estilo, refactors y rendimiento no medido quedan como opcionales. Cambios de requisito, migraciones nuevas o ampliaciones materiales vuelven a planificación. Mantén estables SPEC y PLAN.

Escribe REVISION.md con SHA, hallazgos, reproducciones, pruebas realizadas, limitaciones y pendientes. Ejecuta aceptación de las correcciones antes de gara-commit. No marques Done ni publiques por el hecho de revisar.
""",
    ),
    "gara-workflow": (
        "Flujo Gara",
        "Opera el ejecutor de Codex y Claude con estado durable",
        "Opera o diagnostica el flujo Gara de requisitos, plan, tareas, construcción, verificación y revisión, en modo manual o automatizado.",
        """
El flujo guiado es gara-spec → gara-plan → gara-tasks → gara-build → gara-verify → gara-review. Ajusta su profundidad al trabajo; una corrección claramente acotada puede ejecutarse directamente con aceptación proporcional.

Para automatización, lee la referencia de operación y el contrato de artefactos. Resuelve `scripts/gara_workflow.py` respecto a esta skill. Empieza por doctor y un dry-run; run ejecuta la SPEC autorizada desde una rama de issue. No interpretes una petición de explicar o preparar como una orden de lanzar el flujo.

Un estado completed corresponde a una ejecución local validada. Publicación y entrega se añaden con --publish explícito. Status, metrics, sessions y watch observan el progreso; resume reconcilia hashes y trabajo interrumpido. Usa --ack-checkpoint solo tras una comprobación humana real.

Los clientes, modelos y permisos se heredan de la configuración vigente. No añadas bypasses, servidores, tokens ni modelos fijos. Ante infraestructura fallida después de cambios, reconcilia antes de repetir. Un requisito material pendiente produce un bloqueo documentado.
""",
    ),
    "gara-deliver": (
        "Entrega Gara",
        "Publica una rama autorizada y prepara su revisión en Linear",
        "Publica una rama verificada de Gara y entrega PR y evidencias a In Review cuando el usuario pide explícitamente publicar o utiliza --publish.",
        """
Comprueba autorización concreta de publicación, issue y rama, commits, documentación, aceptación y estado del CI. Reutiliza la PR de la rama si existe; no dupliques entregas al reanudar.

Con las herramientas autenticadas disponibles, publica la rama y abre o actualiza la PR, vinculando el issue según el proceso canónico. Si usas gh, proporciona el cuerpo mediante un archivo UTF-8 con nuevas líneas reales. Distingue gates locales de checks remotos vivos para el mismo SHA.

Entrega el issue a In Review y deja evidencia del alcance, comandos, resultados y limitaciones mediante las capacidades de Linear disponibles. Si faltan credenciales o conectores, prepara la descripción y registra el bloqueo; no inventes una actualización externa.

Escribe ENTREGA.md con URL de PR, SHA y estado observado de Linear. La revisión de agentes no permite autoaprobar el trabajo, hacer merge o moverlo a Done; aplica excepciones solo mediante instrucciones explícitas vigentes del propietario. La invocación de esta skill no autoriza un despliegue.
""",
    ),
}

OTHER = {
    "gara-diseno": (
        "Diseño Gara",
        "Documenta el sistema visual real de la interfaz Gara",
        "Define o documenta un sistema visual comprobable para Gara, derivado de sus tokens, componentes, temas y decisiones de producto.",
        "Lee el CSS, Tailwind, ThemeProvider y componentes actuales. --default documenta lo observado en Gara, no impone el monocromo de OSIX. Escribe DISENO.md con tipografía Lato y fallbacks reales, colores por tema, espaciados medibles, foco, estados y movimiento reducido. Distingue valores existentes de propuestas nuevas. Mantén colores científicos de Molstar separados de colores decorativos. Pregunta solo decisiones visuales materiales y limita cambios al alcance autorizado.",
    ),
    "gara-workflow-setup": (
        "Preparación del flujo Gara",
        "Detecta comandos y prepara artefactos sin duplicar memoria",
        "Prepara un checkout Gara para el flujo documentado: detecta comandos, verifica configuración y propone integración con las instrucciones existentes.",
        "Lee los manifests, lockfiles, CI y reglas del checkout. Detecta comandos disponibles y configura un índice de specs y artefactos versionados cuando se haya autorizado la preparación. Usa doctor para capacidades. Conserva AGENTS.md, CLAUDE.md y la memoria canónica; propone mejoras concretas si son necesarias, sin reemplazarlos. No copies hooks de Claude a Codex ni ejecutes suites completas tras cada edición. Una integración con hooks requiere una necesidad concreta y el formato y confianza del motor real. No cambies dependencias, thresholds o workers incidentalmente.",
    ),
    "gara-workflow-health": (
        "Salud del flujo Gara",
        "Mide ejecución y trazabilidad a partir de evidencia real",
        "Audita la salud del flujo Gara usando sus estados, tareas y resúmenes de sesiones reales; usar para diagnosticar fallos de proceso.",
        "Usa scripts/health.py con el checkout y slug para medir cobertura de requisitos, estados, gates registrados y sesiones normalizadas. Revisa una muestra de briefings y PLAN contra código; una aceptación vacía o una marca verified no demuestran calidad. Distingue contadores observados de conclusiones inferidas y datos ausentes de cero. Informa huecos, tiempos y límites sin proyectar métricas históricas sobre otro HEAD. No alteres automáticamente el proceso ni clasifiques como fallo una espera legítima en In Review.",
    ),
    "gara-retro": (
        "Retrospectiva Gara",
        "Propone mejoras del flujo respaldadas por datos medidos",
        "Analiza métricas y correcciones del flujo Gara para proponer cambios concretos a sus skills, prompts o automatizaciones.",
        "Lee metrics, fixes y revisiones del mismo periodo y configuración. Contrasta ejemplos reales de tareas con reintentos, aceptación fallida, coste disponible y calidad final. No supongas precios, límites o modelos vigentes: consulta fuentes oficiales si necesitas compararlos. Propón un diff acotado con evidencia, coste esperado y forma de evaluar el resultado. No autoedites skills ni traslades un incidente aislado a una regla universal sin autorización. Los datos de sesiones de Codex y Claude se comparan explicando las diferencias de medición.",
    ),
    "gara-investigar": (
        "Investigación Gara",
        "Produce un dosier con fuentes trazables y contraste",
        "Investiga una pregunta científica, técnica o de negocio de Gara y produce un dosier con fuentes trazables y revisión crítica.",
        "Define la pregunta, periodo y decisión que debe informar. Reparte recogida por clase de fuente y perspectivas, no por subtemas solapados. Usa fuentes primarias y fichas con autor, fecha, URL, extracto y límites. Si hay delegación, el coordinador encarga rastreadores y un contrastador con contexto fresco; no dependas de subagentes que puedan lanzar otros subagentes. Sintetiza sobre las fichas y distingue resultados científicos de hipótesis. Verifica vigencia y fuentes realmente independientes. --rapido reduce profundidad y explicita incertidumbre; no inventa citas ni conclusiones.",
    ),
    "gara-convocatoria": (
        "Convocatorias Gara",
        "Evalúa propuestas científicas contra criterios reales",
        "Analiza una convocatoria de financiación o ayuda para Gara y prepara una propuesta trazable a sus requisitos y criterios de evaluación.",
        "Lee bases oficiales completas, elegibilidad, plazo, presupuesto permitido y rúbrica con pesos. Investiga ediciones anteriores con fuentes identificadas. Formula candidatas distintas, ligadas a capacidades reales de Gara; no inventes resultados científicos, personalidad jurídica, datos fiscales, socios o compromiso institucional. Un evaluador en contexto fresco puntúa criterio a criterio; un incumplimiento duro descarta, no se disimula como nota baja. Redacta la memoria contra la rúbrica y usa gara-pdf si se pide PDF. Preparar no equivale a presentar ni enviar la solicitud.",
    ),
    "gara-grilling": (
        "Entrevista crítica Gara",
        "Resuelve decisiones materiales mediante rondas breves",
        "Somete a examen un plan, decisión o idea de Gara mediante preguntas dependientes y contraste de sus supuestos.",
        "Modela el asunto como árbol de decisiones y resuelve primero hechos mediante exploración. Pregunta de una a tres decisiones independientes por ronda, con recomendación y consecuencias. Distingue decisiones bloqueantes de detalles reversibles y pregunta según dependencias. Registra respuestas y pendientes; silencio no acepta. Contrasta riesgos con escenarios concretos y concluye cuando el objetivo y las decisiones materiales están claros. No conviertas una entrevista en autorización de implementación, publicación o gasto.",
    ),
    "gara-pdf": (
        "Documentos PDF Gara",
        "Genera documentos con identidad Gara y recursos locales",
        "Genera PDFs de informes, memorias, propuestas o presupuestos de Gara con recursos gráficos embebidos y metadatos proporcionados.",
        "Reúne contenido y metadatos, sin inventar datos fiscales o institucionales. Usa scripts/build_pdf.py con --content body.html --meta meta.json --out documento.pdf; las rutas del script y assets se resuelven respecto a esta skill. El renderer usa Lato y el logo de Gara, embedidos, y Chrome, Chromium o Edge local; --browser permite configurarlo. Todos los metadatos salvo title son opcionales. Conserva cifras y citas, comprueba el PDF renderizado y los saltos de página, tablas y caracteres españoles. Usa --keep-html para diagnosticar. Consulta la referencia de documento y estilos antes de componer.",
    ),
    "gara-frontend-design": (
        "Interfaz Gara",
        "Diseña interfaces científicas coherentes con el producto",
        "Diseña o mejora interfaces web de Gara con jerarquía, contenido y comportamiento intencionales, respetando su sistema visual existente.",
        "Grounda el diseño en investigadores, secuencias, estructuras, motores y resultados reales de la feature. Sigue los tokens y decisiones vigentes; una nueva dirección visual requiere un encargo de rediseño. Planifica jerarquía, layout, tipografía y una interacción que sirva al objetivo; no copies una landing genérica. Usa contenido comprensible para quien investiga, sin exponer detalles internos como si fueran acciones de producto. Verifica escritorio/móvil, claro/oscuro, foco, errores y vacío. La complejidad visual y el movimiento deben corresponder a la necesidad, no a una obligación estética.",
    ),
    "gara-hero": (
        "Opciones de portada Gara",
        "Explora propuestas diferenciadas de presentación de Gara",
        "Genera variantes comparables de portada o hero para comunicar Gara a una audiencia concreta.",
        "Fija audiencia, objetivo, hechos demostrables y libertad visual autorizada. Define direcciones diferentes antes de repartir variantes; evita que todas converjan a una plantilla. Cada disenador devuelve HTML autocontenido con contenido real y recursos autorizados. El coordinador genera un índice comparativo local. Explica diferencias y tradeoffs; no elijas una afirmación científica o comercial no verificada para mejorar el impacto. No publiques variantes sin una petición de publicación.",
    ),
    "gara-theme-switcher": (
        "Temas de interfaz Gara",
        "Mejora los temas web claro, oscuro y de sistema",
        "Implementa o corrige cambios de tema en la interfaz web de Gara, usando ThemeProvider y los tokens actuales.",
        "Inspecciona ThemeProvider, persistencia de preferencia y la clase dark real. Reutiliza light, dark y system; no añadas un segundo proveedor o una receta de Kotlin/React Native. Comprueba sincronización con el tema del sistema, carga inicial y contraste de paneles, controles y visor. Una revelación animada es opcional y sigue reduced motion; la operación y el foco no dependen de ella. Prueba temas y persistencia en navegador con aceptación pertinente.",
    ),
    "gara-keyboard-avoidance": (
        "Teclado y formularios Gara",
        "Mantiene visibles formularios y acciones con teclado móvil",
        "Corrige formularios web de Gara cuyos inputs o acciones quedan ocultos por el teclado, viewport móvil o contenedores con scroll.",
        "Reproduce con los formularios y layout actuales en navegador móvil. Considera viewport visual, unidades dinámicas, scroll del contenedor, safe areas y foco; no traduzcas KeyboardAvoidingView literalmente a React web. Mantén visibles campo activo y acciones sin saltos ni listeners duplicados, y restaura el comportamiento al cerrar teclado. Comprueba orientación, textarea, diálogo, navegación por teclado y escritorio. Si solo hay emulación de viewport, declara que no se verificó un teclado físico móvil.",
    ),
    "gara-view-transitions": (
        "Transiciones de vistas Gara",
        "Coordina cambios de paneles, pestañas y diálogos web",
        "Implementa o corrige transiciones entre vistas de la SPA de Gara respetando sus paneles, pestañas y diálogos existentes.",
        "Identifica el mecanismo real de navegación antes de modificarlo. No instales Expo Router, un native stack ni un router nuevo para animar paneles existentes. Decide qué transición comunica un cambio real y evita animar el render molecular sin necesidad. Coordina entrada/salida, foco, estado y cancelación ante cambios rápidos. Respeta reduced motion y degrada a un cambio inmediato cuando una API no esté disponible. Prueba navegación repetida, cierres, errores y persistencia del contexto del visor.",
    ),
    "gara-logger-system": (
        "Logging Gara",
        "Integra registros útiles preservando redacción y privacidad",
        "Implementa o corrige logging frontend o backend de Gara usando la infraestructura existente y registros adecuados al entorno.",
        "Inspecciona la infraestructura actual antes de crear otra. En backend usa logging y conserva filtros de redacción, especialmente tickets y credenciales; en frontend sigue los patrones del cliente API y el entorno de Vite. Acota cada cambio a la petición: retirar logging anterior o sustituir todos los console no es automático. No registres secuencias privadas, tokens, payloads sensibles o .env. Verifica desarrollo/producción y eventos de error; cubre redacción y niveles con pruebas de comportamiento.",
    ),
    "gara-find-skills": (
        "Descubrir skills para Gara",
        "Busca capacidades útiles y evita instalaciones duplicadas",
        "Localiza skills pertinentes para una necesidad concreta de Gara y prepara su integración cuando se solicita.",
        "Empieza por las skills instaladas y el catálogo del paquete; no instales una equivalente solo por cambiar de nombre. Para fuentes externas, comprueba repositorio, instrucciones completas, recursos, licencia y compatibilidad con el motor. Recomienda una opción sustentada en la necesidad, no en popularidad. Usa la capacidad de instalación disponible si el usuario autoriza instalar; conserva versiones y configuraciones existentes y registra procedencia. No supongas herramientas llamadas literalmente Skill ni permisos de publicación.",
    ),
}

COPIED_UI = {
    "baseline-ui": (
        "gara-baseline-ui",
        "Acabado de interfaz Gara",
        "Revisa el acabado visual y los estados de la interfaz",
    ),
    "fixing-accessibility": (
        "gara-fixing-accessibility",
        "Accesibilidad Gara",
        "Verifica foco, teclado, contraste y semántica accesible",
    ),
    "fixing-motion-performance": (
        "gara-fixing-motion-performance",
        "Rendimiento de animación Gara",
        "Diagnostica tirones de movimiento con evidencia",
    ),
    "fixing-metadata": (
        "gara-fixing-metadata",
        "Metadatos web Gara",
        "Corrige metadatos HTML del alcance publicado",
    ),
    "ui-animation": (
        "gara-ui-animation",
        "Animación de interfaz Gara",
        "Diseña y analiza movimiento útil y accesible",
    ),
}


def create() -> None:
    if (ROOT / "skills").exists() or (ROOT / "catalog.json").exists():
        raise WorkflowError(
            "Las fuentes adaptadas ya existen; edita las skills y recompila, sin regenerarlas."
        )
    catalog = {"version": "0.1.0", "skills": [], "agents": [], "mapping": []}
    profile = (ROOT / "profiles/gara.md").read_text(encoding="utf-8")
    all_entries = {**CORE, **OTHER}
    for old, (name, title, short) in COPIED_UI.items():
        source = (ROOT / f"export/skills/{old}/SKILL.md").read_text(encoding="utf-8")
        body = source.split("---", 2)[2].strip()
        body = body.replace("/frontend-design", "gara-frontend-design").replace(
            "/ui-animation", "gara-ui-animation"
        )
        body = (
            "Aplica estos criterios al alcance pedido en Gara y a su sistema visual existente. No introduzcas dependencias o un rediseño incidental.\n\n"
            + body
        )
        all_entries[name] = (
            title,
            short,
            f"{short} en la interfaz web de Gara; usar para el comportamiento concreto descrito.",
            body,
        )
    explicit = {
        name
        for name in all_entries
        if name in CORE
        or name
        in {
            "gara-diseno",
            "gara-workflow-setup",
            "gara-workflow-health",
            "gara-retro",
            "gara-investigar",
            "gara-convocatoria",
            "gara-hero",
        }
    }
    for name, (title, short, description, body) in all_entries.items():
        folder = ROOT / "skills" / name
        folder.mkdir(parents=True)
        entry = f"\n# {title}\n\nLee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.\n\n{body.strip()}\n"
        references = ["gara.md"]
        (folder / "references").mkdir()
        atomic_write(folder / "references/gara.md", profile)
        if name in CORE:
            for filename in ("artifacts.md", "runtime.md"):
                shutil.copyfile(
                    ROOT / "references" / filename, folder / "references" / filename
                )
                references.append(filename)
        if name == "gara-pdf":
            references.append("document.md")
        if len(references) > 1:
            entry += (
                "\n## Referencias\n\n"
                + "\n".join(
                    f"- [{filename}](references/{filename})"
                    for filename in references[1:]
                )
                + "\n"
            )
        atomic_write(
            folder / "SKILL.md",
            header({"name": name, "description": description}) + entry,
        )
        catalog["skills"].append(
            {
                "name": name,
                "title": title,
                "short": short,
                "explicit_only": name in explicit,
            }
        )
    for old, (name, _, _) in COPIED_UI.items():
        folder = ROOT / "export/skills" / old
        for source in folder.iterdir():
            if source.name != "SKILL.md":
                target = ROOT / "skills" / name / source.name
                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                elif source.name != "README.md":
                    shutil.copyfile(source, target)
    workflow = ROOT / "skills/gara-workflow/scripts"
    workflow.mkdir()
    driver = """#!/usr/bin/env python3
import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here if (here / "gara_workflow").is_dir() else here.parents[2]))
from gara_workflow.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
"""
    atomic_write(workflow / "gara_workflow.py", driver)
    # Existing policy is reused; its executable is bundled for Claude and portable installations.
    original_commit = Path.home() / ".codex/skills/gara-commit"
    commit = ROOT / "skills/gara-commit"
    shutil.copytree(
        original_commit,
        commit,
        ignore=shutil.ignore_patterns("__pycache__", "agents", "README.md"),
    )
    commit_body = """\n# Commits Gara\n\nLee el [perfil Gara](references/gara.md). Usa `scripts/gara_commit.py`, resuelto respecto a esta skill, en lugar de invocar git commit directamente.\n\nInspecciona el staging, identifica una única intención lógica y elige el tipo semántico. El título comienza en mayúscula, no lleva punto final y admite hasta 50 caracteres. Proporciona --why y uno o más --how basados en el diff real; el script construye PORQUÉ, CÓMO y DOCUMENTACIÓN. Usa --dry-run para validar sin crear commit.\n\nUn rechazo se corrige en el staging o la documentación; no uses bypass ni git commit manual. Conserva archivos ajenos y añade selectivamente. El ejecutable comprueba identidad Gara, categorías, intención explícita para código y documentación cuando cambian contratos públicos, configuración o arquitectura.\n"""
    (commit / "references").mkdir(exist_ok=True)
    atomic_write(commit / "references/gara.md", profile)
    atomic_write(
        commit / "SKILL.md",
        header(
            {
                "name": "gara-commit",
                "description": "Valida y genera commits Git atómicos y narrativos exclusivamente para Gara, usando su política y documentación staged.",
            }
        )
        + commit_body,
    )
    catalog["skills"].append(
        {
            "name": "gara-commit",
            "title": "Commits Gara",
            "short": "Valida staging y crea commits atómicos narrativos",
            "explicit_only": False,
        }
    )
    original_license = ROOT / "export/skills/frontend-design/LICENSE.txt"
    shutil.copyfile(original_license, ROOT / "skills/gara-frontend-design/LICENSE.txt")
    old_names = {
        "osix-build": "gara-workflow",
        "osix-pdf": "gara-pdf",
        "android-theme-switcher": "gara-theme-switcher",
    }
    for source in (ROOT / "export/skills").glob("*/SKILL.md"):
        old = source.parent.name
        name = old_names.get(old, "gara-" + old)
        catalog["mapping"].append(
            {
                "original": source.relative_to(ROOT / "export").as_posix(),
                "target": name,
                "status": "adapted",
            }
        )
    command_names = {
        "osix-commit": "gara-commit",
        "rn-theme-switcher": "gara-theme-switcher",
        "rn-keyboard-avoidance": "gara-keyboard-avoidance",
        "rn-stack-transitions": "gara-view-transitions",
        "logger-system": "gara-logger-system",
        "find-skills": "gara-find-skills",
    }
    for source in (ROOT / "export/commands").glob("*.md"):
        if source.name != "README.md":
            catalog["mapping"].append(
                {
                    "original": source.relative_to(ROOT / "export").as_posix(),
                    "target": command_names[source.stem],
                    "status": "consolidated"
                    if source.stem == "rn-theme-switcher"
                    else "adapted",
                }
            )
    role_bodies = {
        "scout": (
            "Localiza código y fuentes canónicas de Gara con contexto mínimo.",
            True,
            "Read, Glob, Grep, Bash",
            "Recibe la lista completa de preguntas. Lee índices antes de buscar, ubica rutas y símbolos y devuelve evidencia breve. No edites ni rediseñes. Distingue el código actual de inventarios históricos.",
        ),
        "implementer": (
            "Implementa una tarea ya especificada de Gara con aceptación real.",
            False,
            "Read, Write, Edit, Glob, Grep, Bash",
            "Recibe un briefing completo, archivos y contratos. Implementa el alcance asignado con el estilo existente. No decidas requisitos ni arquitectura. Ejecuta la aceptación acotada, devuelve salida real y declara rutas adicionales imprescindibles. En flujo automático, el coordinador decide el estado y el commit. No lances otro CLI ni publiques.",
        ),
        "verifier": (
            "Contrasta código, requisitos y evidencia sin haber implementado.",
            True,
            "Read, Glob, Grep, Bash",
            "Revisa SPEC, PLAN, tareas, diff y consumidores. Comprueba requisito a requisito y contrasta las evidencias con las pruebas. Reporta hallazgos reproducibles y limitaciones; no edites. Si tu entorno no permite ejecutar una aceptación, no afirmes que pasó. Tu revisión no es aprobación humana en Linear.",
        ),
        "revisor-visual": (
            "Recorre flujos web de Gara y comprueba su acabado.",
            False,
            "Read, Write, Edit, Glob, Grep, Bash",
            "Recorre la interfaz construida con las herramientas de navegador disponibles, en escritorio/móvil y claro/oscuro. Mide contra tokens actuales, foco, contraste, movimiento reducido y estados vacíos/de error. Corrige acabado del alcance asignado y reporta cambios estructurales. Si no hay navegador, documenta el límite y no inventes capturas.",
        ),
        "researcher": (
            "Responde una pregunta técnica de Gara con fuentes primarias.",
            True,
            "Read, Glob, Grep, WebSearch, WebFetch",
            "Investiga una pregunta acotada fuera del repositorio. Usa documentación oficial y fuentes primarias, verifica fechas y versiones. Devuelve conclusión breve, URLs y límites. No instales dependencias, edites código o afirmes hechos a partir de snippets no leídos.",
        ),
        "investigador": (
            "Organiza y sintetiza un ámbito de investigación sobre Gara.",
            False,
            "Read, Write, Glob, Grep, WebSearch, WebFetch",
            "Define ángulos por clase de fuente y sintetiza fichas trazables. Si hacen falta rastreadores, solicita al coordinador que los lance: no asumas delegación anidada. Separa hechos e inferencias y devuelve un dosier parcial con fuentes, fechas y pendientes.",
        ),
        "rastreador": (
            "Recoge fuentes de un ángulo concreto sin sintetizar conclusiones.",
            False,
            "Read, Write, Glob, Grep, WebSearch, WebFetch",
            "Recoge fuentes del ángulo asignado y escribe fichas en la ruta y prefijo exclusivos proporcionados. Cada ficha identifica autor, fecha, URL, extracto y alcance. No concluyas ni confundas copias del mismo origen con fuentes independientes.",
        ),
        "contrastador": (
            "Intenta refutar un informe mediante sus fuentes reales.",
            True,
            "Read, Glob, Grep, WebSearch, WebFetch",
            "Con contexto fresco, comprueba cifras y afirmaciones contra extractos reales; detecta fuentes dependientes y datos caducados expresados como presentes. Busca evidencia contraria. Reporta sustentado, contradicho o no acreditado por afirmación. No edites el informe ni rellenes huecos por memoria.",
        ),
        "evaluador": (
            "Puntúa propuestas de Gara contra una rúbrica explícita.",
            True,
            "Read, Glob, Grep",
            "Lee elegibilidad y rúbrica con pesos antes de evaluar. Descarta incumplimientos duros con su razón. Puntúa cada candidata por criterio y evidencia; no inventes requisitos o puntuaciones. Sin rúbrica, solicita al coordinador el dato y registra el bloqueo.",
        ),
        "disenador": (
            "Produce una variante visual de Gara dentro de una dirección asignada.",
            False,
            "Read, Write, Glob, Grep, Bash",
            "Recibe audiencia, contenido, dirección visual y archivos propios. Diseña una variante de hero o interfaz coherente con el encargo, diferenciada de las otras y con recursos autorizados. Para interfaz existente conserva sus tokens; devuelve HTML autocontenido cuando corresponda. No inventes afirmaciones científicas ni publiques.",
        ),
    }
    for name, (description, read_only, tools, body) in role_bodies.items():
        role = "gara-" + name
        relative = f"roles/{role}.md"
        atomic_write(
            ROOT / relative,
            f"# {role}\n\n{body}\n\nAplica las instrucciones del checkout Gara y el alcance recibido. Conserva permisos, modelos y autorización del entorno.\n",
        )
        catalog["agents"].append(
            {
                "name": role,
                "description": description,
                "read_only": read_only,
                "claude_tools": tools,
                "source": relative,
            }
        )
        catalog["mapping"].append(
            {"original": f"agents/{name}.md", "target": role, "status": "adapted"}
        )
    scripts = {
        "osix-build": ("run", "adapted"),
        "osix-build-2": ("export/scripts/osix-build-2", "historical"),
        "osix-forge": ("export/scripts/osix-forge", "historical"),
        "osix-reanudar": ("resume", "adapted"),
        "osix-metricas": ("metrics", "adapted"),
        "osix-fixes": ("fixes", "adapted"),
        "claude-sesiones": ("sessions", "adapted"),
        "vigilar-agenda": ("watch", "adapted"),
    }
    for name, (target, status) in scripts.items():
        catalog["mapping"].append(
            {"original": f"scripts/{name}", "target": target, "status": status}
        )
    save_json(ROOT / "catalog.json", catalog)
    print(f"Creadas {len(catalog['skills'])} skills y {len(catalog['agents'])} roles.")


if __name__ == "__main__":
    create()
