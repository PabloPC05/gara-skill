# Herramientas de navegador para probar Gara

Revisado en octubre de 2026 a partir de las fuentes oficiales enlazadas. Comprueba la versión vigente antes de instalar: estas herramientas cambian rápido.

## Elección

| Herramienta | Para qué | Coste y datos | Estado |
| --- | --- | --- | --- |
| **browser-harness** (Browser Use), Chrome local | Opción por defecto: el agente controla Chrome por CDP, hace clics, rellena formularios y saca capturas | Gratis en local, sin API key; la página no sale de tu máquina | Estable, MIT |
| **jev-ultrafast** (Browser Use + modelo Jev) | Escenarios de formularios, botones y navegación, en segundos y sin gastar tokens de Claude | Con tu plan GOAT de Command Code: una sola API key para Jev y el modelo de texto. Envía el texto y los controles de la página a Command Code | MVP experimental, MIT |
| Browser Use Cloud | Varias pruebas en paralelo o máquina sin Chrome | De pago; para `localhost` exige un túnel público hacia tu app | Solo con orden expresa |

Reparto por defecto, cuando jev-ultrafast está configurado:

| Escenario | Herramienta |
| --- | --- |
| Formularios, navegación, tablas, filtros, mensajes de error | **jev-ultrafast** |
| Visor Molstar (canvas), subidas de archivos, iframes, pestañas emergentes, scroll anidado | **browser-harness**: jev no los soporta |
| Comprobar que un escenario que jev marcó `done` salió bien | Su última captura; si no basta, browser-harness |

Si jev no está configurado, todo va con browser-harness. El contenido de las páginas que prueba jev sale a Command Code: úsalo solo en entornos de desarrollo sin datos privados.

## Instalar browser-harness (una vez)

Necesita [uv](https://docs.astral.sh/uv/getting-started/installation/) y Python 3.12.

```bash
uv tool install --python 3.12 --upgrade --force browser-harness
browser-harness recordings disable   # no guardar capturas y trazas por defecto
```

No hace falta instalar su skill: `gara-probar` y `gara-probador` ya explican cómo usarlo. Si instalas también la skill oficial `browser-harness`, se activará sola en cualquier tarea web; tenlo en cuenta.

## Navegador dedicado para pruebas

browser-harness se conecta a un navegador por su puerto de depuración (CDP) y lo controla entero. **Nunca uses el navegador personal del usuario**: tiene sus sesiones iniciadas y sus pestañas abiertas. Tres trampas comprobadas en la práctica:

- **El puerto 9222 suele estar ocupado** por el navegador personal (Chrome, Helium u otro Chromium con la depuración remota activada). Si arrancas el de pruebas en ese puerto, no podrá usarlo y te conectarás al personal sin darte cuenta. Usa **9333**.
- **El daemon `default` de browser-harness puede estar ya conectado** a otro navegador (por ejemplo, el de tu propia instalación de browser-use) e ignorará `BU_CDP_URL`. Usa siempre un daemon con nombre propio: `BU_NAME=gara-pruebas`.
- **En una pestaña en segundo plano Chromium deja de pintar** y las capturas se bloquean. Arranca el navegador de pruebas sin ventana (`--headless=new`).

Sirve cualquier Chromium separado. Si no tienes Chrome, el Chromium de Playwright vale (`npx playwright install chromium`):

```powershell
$chromium = "$env:LOCALAPPDATA\ms-playwright\chromium-1234\chrome-win64\chrome.exe"   # o la ruta de tu Chrome
Start-Process $chromium -ArgumentList '--headless=new','--remote-debugging-port=9333',"--user-data-dir=$env:TEMP\gara-chrome-pruebas",'--no-first-run','about:blank'
```

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --remote-debugging-port=9333 --user-data-dir=/tmp/gara-chrome-pruebas --no-first-run about:blank &
```

**Antes de cada sesión, comprueba que es el navegador correcto**: `curl -s http://127.0.0.1:9333/json/list` solo debe mostrar `about:blank` o páginas de `localhost`. Si aparece cualquier otra web, no es el de pruebas: para.

Luego usa browser-harness siempre con estas dos variables:

```bash
export BU_CDP_URL=http://127.0.0.1:9333 BU_NAME=gara-pruebas
browser-harness <<'PY'
print(page_info())
PY
```

Si falla, `browser-harness --doctor` diagnostica la conexión. Las acciones del navegador deben ir de una en una: dos agentes usando el mismo navegador a la vez se pisan las pestañas.

## jev-ultrafast con Command Code (GOAT)

jev-ultrafast llama por defecto a la API de TypeSafe. El plan GOAT de [Command Code](https://commandcode.ai/docs/provider) ofrece el mismo modelo (`typesafe/jev`) en su Provider API. El [parche](jev-commandcode.patch) de esta skill hace dos cambios pequeños, comprobados sobre el commit `1231850` de jev-ultrafast:

- la dirección de TypeSafe, que estaba escrita en el código, pasa a ser configurable (`TYPESAFE_BASE_URL`);
- la pestaña en segundo plano pasa a ser opcional (`JEV_BACKGROUND_TAB=0`), porque en segundo plano las capturas tras un clic se bloquean.

1. Clona jev-ultrafast **fuera** del checkout de Gara y aplica el parche:

   ```bash
   git clone https://github.com/browser-use/jev-ultrafast.git ~/jev-ultrafast
   cd ~/jev-ultrafast
   git apply <ruta-de-esta-skill>/references/jev-commandcode.patch
   uv sync
   ```

2. Crea `~/jev-ultrafast/.env` con tu API key de Command Code (Studio → API keys). La misma key sirve para las dos partes. `.env` ya está en el `.gitignore` de jev-ultrafast; no lo copies a ningún repositorio.

   ```bash
   TYPESAFE_BASE_URL=https://api.commandcode.ai/provider/v1
   TYPESAFE_API_KEY=<tu key de Command Code>
   TYPESAFE_MODEL=typesafe/jev
   TEXT_MODEL_BASE_URL=https://api.commandcode.ai/provider/v1
   TEXT_MODEL_API_KEY=<tu key de Command Code>
   TEXT_MODEL=deepseek/deepseek-v4.1-flash
   ```

   `TEXT_MODEL` solo escribe el texto de los campos. Con el plan GOAT funcionan `deepseek/deepseek-v4.1-flash` (el elegido) y `deepseek/deepseek-v4-flash`. Los nombres exactos se consultan en `GET /models` de la Provider API: `z-ai/glm-5.3-flash` lleva punto, no guion. Las variantes `-fast` responden antes, pero en las pruebas escribieron texto inventado, y `google/gemini-3.5-flash-lite` no entra en GOAT. No pongas `TEXT_MODEL_REASONING=none`: envía un parámetro propio de OpenRouter.

3. Lanza cada escenario con el script de la skill. Comprueba que el navegador de `--cdp-url` solo tiene páginas locales y se niega a ejecutar si no. También usa su propio daemon (`gara-pruebas`) y lo cierra al terminar, y carga el `.env` con prioridad: `uv run --env-file` no sobrescribe variables ya definidas, y una `TYPESAFE_API_KEY` antigua en el entorno de Windows haría fallar las llamadas con un 401. Limita los pasos, guarda capturas y devuelve un JSON con el estado, la URL final, las acciones, el texto visible, la última captura y los tokens.

   ```bash
   uv run --project ~/jev-ultrafast python <ruta-de-esta-skill>/scripts/jev_run.py \
     --env-file ~/jev-ultrafast/.env --cdp-url http://127.0.0.1:9333 \
     --url http://localhost:5173 \
     --goal "Abre Resultados y filtra por estado Completado. Para cuando la tabla solo muestre filas Completado." \
     --record-dir "$TMP/gara-pruebas/R1"
   ```

   Escribe el objetivo con una condición de parada observable. Sale con 0 si Jev marcó `done` y con 2 en cualquier otro caso (`blocked`, `max-steps`, `error`). `done` significa que Jev cree haber terminado: contrástalo con `page_text` y `last_capture`.

**Comprobado el 7 de octubre de 2026** con el plan GOAT, en un formulario local de prueba:

- *crear un proyecto con nombre y tipo*: 3 acciones, 4,3 s y unos 9.300 tokens de Jev;
- *enviarlo sin nombre y ver el error*: 2 acciones, 2,8 s.

En los dos el resultado coincidió con la captura. Aún no se ha probado contra Gara.

## Qué no hacer sin orden expresa del usuario

- Usar Browser Use Cloud, iniciar sesión (`browser-harness auth login`) o crear una API key.
- Abrir un túnel público hacia `localhost`: expondría una versión no publicada de Gara.
- Conectarse al Chrome personal del usuario o reutilizar sus sesiones.
- Activar las grabaciones (`browser-harness recordings enable`), que guardan capturas con posible contenido sensible.

La skill comunitaria `qa` de Browser Use hace varias de estas cosas automáticamente (navegador en la nube, túnel a localhost y alta de API key sin intervención), así que no se instala tal cual. De ella se toma la escala de puntuación 1–5 que usa `gara-probador`.

## Fuentes

- [browser-use/browser-harness, `install.md`](https://github.com/browser-use/browser-harness/blob/main/install.md).
- [Skill `browser-use`](https://github.com/browser-use/browser-use/blob/main/skills/browser-use/SKILL.md) y [skill `qa`](https://github.com/browser-use/browser-use/blob/main/skills/qa/SKILL.md) de Browser Use.
- [Skills de Browser Use](https://docs.browser-use.com/open-source/examples/skills/overview).
- [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast).
- [Provider API de Command Code](https://commandcode.ai/docs/provider), [plan GOAT](https://commandcode.ai/docs/plans/goat) y [modelo Jev](https://commandcode.ai/models/jev).
- [Skill `webapp-testing` de Anthropic](https://github.com/anthropics/skills/tree/main/skills/webapp-testing), alternativa con Playwright.
