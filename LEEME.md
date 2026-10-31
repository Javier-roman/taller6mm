# Kit de arranque de Taller6mm para Claude Code

> El proyecto se llamaba BANCADA hasta el 31-10-2026. La carpeta local `C:\dev\bancada` conserva el nombre antiguo.

Este kit es el "mega prompt" en el formato que Claude Code mejor aprovecha. Contiene un mensaje inicial y una memoria permanente. A eso se suman una especificación por áreas y la configuración de Claude Code. Así nada se pierde aunque el proyecto dure meses y muchas sesiones.

## Qué hay dentro
| Ruta | Para qué sirve |
|---|---|
| `PROMPT_INICIAL.md` | El mensaje que pegas en Claude Code para empezar (Fase 0) y plantillas para las fases siguientes |
| `CLAUDE.md` | Memoria permanente del proyecto: Claude Code la lee al empezar cada sesión |
| `CLAUDE.local.md` | El perfil de tu equipo (Windows 11, herramientas, GPU). Se carga junto a `CLAUDE.md` y no se sube al repositorio |
| `docs/` | Especificación completa (visión, diseño, configurador, mercado, assets, comunidad, arquitectura, calidad, legal y roadmap), ADRs, tus tiendas y marcas, y referencias visuales |
| `.claude/` | Skills (`/verify`, `/revisar-ui`…), subagentes revisores, reglas que se cargan según la carpeta y tres hooks: guardián de comandos (Bash y PowerShell), formateador y aviso de entorno al iniciar |
| `.mcp.json` | Navegador Playwright para que Claude Code vea lo que construye (Edge en Windows, Chromium en macOS y Linux, mediante `.claude/mcp/playwright.mjs`), y la documentación de Claude Code |
| `.gitignore` | Deja fuera del repositorio los secretos, los builds, `CLAUDE.local.md` y las capturas de referencia |

## Arrancar en Windows
1. Crea la carpeta `C:\dev\bancada`. Tiene que estar fuera de OneDrive, que bloquea archivos de `node_modules` mientras sincroniza.
2. Pon dentro **todo** el contenido del kit, incluidas la carpeta `.claude` y los archivos `.mcp.json`, `.gitignore` y `CLAUDE.local.md`. Con el zip, en PowerShell:
   `Expand-Archive -Path "$HOME\Downloads\bancada.zip" -DestinationPath C:\dev\bancada`
3. Abre una terminal **normal**: Windows Terminal o PowerShell, **sin** «Ejecutar como administrador».
4. Ejecuta `cd C:\dev\bancada` y después `claude`.
5. Acepta el diálogo de confianza de la carpeta y aprueba los servidores MCP de `.mcp.json` cuando te lo pida. Sin eso no funcionan los hooks ni el navegador.
6. Abre `PROMPT_INICIAL.md`, copia el bloque entre las líneas `=====` y pégalo.

Si algo del entorno está mal (sesión de administrador, carpeta dentro de OneDrive o Node antiguo), el aviso de inicio te lo dirá en cuanto arranques.

## Consejos
- `/context` muestra qué memoria y reglas tiene cargadas. `/skills` lista las skills de este kit. El asistente `/agents` ya no existe en Claude Code: los subagentes se ven en `.claude/agents/` y se gestionan pidiéndoselo a Claude o editando esos archivos.
- **pnpm**: si `pnpm -v` no responde, instálalo con `npm install -g pnpm` desde la terminal normal. `corepack enable` suele pedir permisos de administrador en Windows.
- **GitHub**: antes de que Claude Code suba el CI, ejecuta tú `gh auth refresh -h github.com -s workflow`.
- **MCP de Playwright** (el navegador de Claude Code): `.mcp.json` arranca `node .claude/mcp/playwright.mjs`, que funciona igual en Windows, macOS y Linux sin tocar nada. El lanzador:
  - abre **Edge** en Windows (ya viene con el sistema) y el **Chromium de Playwright** en macOS y Linux, en Linux con el sandbox de Chromium forzado (salvo como root);
  - ejecuta `@playwright/mcp` con la versión fijada (`0.0.83`), con el npx del mismo Node (nada de `cmd /c`), sin scripts de instalación y desde una carpeta de trabajo fuera del repo, para que no encuentre nada plantado en el proyecto;
  - valida `.claude/playwright-mcp.json` con una **lista blanca estricta** (perfil aislado, orígenes permitidos y acceso a archivos restringido; cualquier otra clave impide arrancar) e ignora las variables `PLAYWRIGHT_MCP_*` que podrían relajarla (salvo `PLAYWRIGHT_MCP_EXECUTABLE_PATH` y `PLAYWRIGHT_MCP_HEADLESS`).

  Además, el hook `guard-mcp` limita las rutas de archivo de las herramientas del MCP (capturas, PDF, trazas, subidas…) a `.playwright-mcp/` y `docs/informes/capturas/`, y `browser_run_code_unsafe` está denegada: ejecuta código en Node y saltaría todas las demás barreras. **No apruebes nunca el servidor `playwright` completo** con «no volver a preguntar».

  En macOS o Linux, la primera vez descarga el navegador con `npx -y @playwright/mcp@0.0.83 install-browser chromium`. Si tu distribución no admite el sandbox de Chromium (sin espacios de nombres de usuario), arranca Claude Code con `TALLER6MM_MCP_NO_SANDBOX=1`. Para ver qué ejecutaría, sin arrancar nada: `node .claude/mcp/playwright.mjs --print`. Sus tests: `node --test ".claude/**/*.test.mjs"` (con `TALLER6MM_MCP_E2E=1` añade una prueba real con el navegador y un entorno hostil).
- Avanza una fase cada vez y lee el informe de fase antes de dar el OK a la siguiente.
- Las capturas de `docs/referencias/` son de terceros (videojuegos y una fotografía). Úsalas solo como referencia interna. Ya están en `.gitignore`.
