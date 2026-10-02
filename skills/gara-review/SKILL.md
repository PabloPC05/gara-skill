---
name: "gara-review"
description: "Revisa un diff de Gara para encontrar fallos de corrección, regresiones y pruebas ausentes, independientemente de la conformidad con el plan."
---

# Revisión de corrección Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional: selecciona una instancia nueva de `gara-verifier` en modo `correccion`, sin participación en la implementación, cuando la capacidad nativa esté disponible y autorizada. Entrega diff/código bruto, baseline/SHA, consumidores, contratos y aceptaciones; evita incluir las conclusiones esperadas del implementador. El verifier devuelve fallos reproducibles o una revisión sin hallazgos, ubicaciones, checks y límites; no edita código ni el informe.

El coordinador incorpora la sección `review` del registro de `REVISION.md` definido en artifacts.md y conserva `verification`, con autor y sesión reales. Si corrige código, repite aceptación y las revisiones afectadas para el nuevo SHA. Comprueba el [contrato de delegación](references/delegation.md). Sin agentes, revisa en esta sesión y declara la ausencia de contexto independiente; un autoinforme no acredita independencia.

Parte del diff y sus consumidores con contexto fresco. Busca errores de comportamiento, contratos rotos, autorización, estados concurrentes y casos límite. Investiga cada candidato y reproduce cuando sea posible; no presentes sospechas como fallos confirmados.

Clasifica por impacto y aporta ubicación, desencadenante y evidencia. Si delegas, usa gara-verifier en modo correccion en una instancia distinta del implementador. Si no hay delegación, declara la limitación; otra sesión técnica tampoco sustituye la aprobación humana exigida por Gara.

Corrige solo fallos dentro del alcance y con autorización existente. Estilo, refactors y rendimiento no medido quedan como opcionales. Cambios de requisito, migraciones nuevas o ampliaciones materiales vuelven a planificación. Mantén estables SPEC y PLAN.

Escribe REVISION.md como el bloque `gara-review:v1` de artifacts.md: SHA real, requisitos y aceptaciones cubiertos, hallazgos con estado `resolved` o `accepted` y limitaciones. Un hallazgo sin resolver ni aceptar no cabe en el contrato: registra el bloqueo en lugar de cerrar la revisión. Ejecuta la aceptación de las correcciones antes de gara-commit y commitea solo con autorización vigente. No marques Done ni publiques por el hecho de revisar.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
