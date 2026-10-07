---
name: "gara-probar"
description: "Prueba de punta a punta una feature de Gara en un navegador real, recorriendo los escenarios de su SPEC con browser-harness (Browser Use) y, si se autoriza, jev-ultrafast; usar cuando quieras comprobar que una feature construida funciona de verdad en la app, no para revisar acabado visual (gara-revisor-visual en gara-verify)."
disable-model-invocation: true
---

# Pruebas en navegador Gara

Lee el [perfil Gara](references/gara.md) y la [guía de herramientas](references/navegador.md). Esta skill prueba comportamiento; no corrige código ni escribe artefactos del flujo salvo que el usuario lo pida.

## Ejecución

Coordinación condicional, bajo el [contrato de delegación](references/delegation.md): con tu autorización, encarga la prueba a `gara-probador`, que la hace con contexto fresco y sin haber implementado. Sin agentes, o para una comprobación corta, pruébala en esta sesión siguiendo las mismas instrucciones que el agente `gara-probador`.

## Pasos

1. **Qué probar.** Lee `specs/<slug>/SPEC.md` (y `TAREAS.md` si existe) y lista los escenarios a recorrer con su `R#`, incluidos los de fallo. Si no hay SPEC, pide al usuario los flujos y el resultado esperado.
2. **Entorno.** Pide o confirma la URL. Si la app no está arrancada, propón los comandos de `frontend/package.json` y `python/pyproject.toml` y arráncala solo si el usuario lo autoriza. Usa datos de prueba; nada de datos científicos privados ni trabajos HPC reales.
3. **Herramienta.** Comprueba que el navegador dedicado (puerto 9333, sin ventana) responde y solo tiene páginas locales, que `browser-harness` funciona con `BU_NAME=gara-pruebas`, y si jev-ultrafast está configurado con Command Code (existe su `.env`; pregunta la ruta si no la conoces). Reparte los escenarios como indica la [guía](references/navegador.md): jev para formularios y navegación; browser-harness para el visor, las subidas y lo que jev no soporta. Si falta algo, muestra al usuario los pasos y espera: no instales, no uses la nube ni abras túneles sin su orden.
4. **Prueba.** Delega en `gara-probador` o prueba aquí. Al agente pásale URL, escenarios, datos permitidos, sesión, directorio para capturas, la herramienta de cada escenario y, si usa jev, la ruta de jev-ultrafast y la de `scripts/jev_run.py` de esta skill.
5. **Revisa la devolución.** Comprueba que cada escenario tiene evidencia real; un "pasa" sin captura o resultado observado cuenta como `no comprobado`.

## Parada

Devuelve la puntuación, el resultado por escenario con su evidencia, los fallos con pasos de reproducción y lo que no se pudo probar, y espera. No corrijas los fallos ni encadenes otra fase: el usuario decide si vuelve a `/gara-build`, lo registra en `/gara-verify` o lo acepta. Si te lo pide, añade el resultado a la sección Verificación de `REVISION.md` como evidencia de aceptación.

## Referencias

- [navegador.md](references/navegador.md)
- [jev-commandcode.patch](references/jev-commandcode.patch)
- [delegation.md](references/delegation.md)
