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
| `.mcp.json` | Navegador Playwright (con Edge) para que Claude Code vea lo que construye, y la documentación de Claude Code |
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
- `/context` muestra qué memoria y reglas tiene cargadas. `/agents` y `/skills` listan los de este kit.
- **pnpm**: si `pnpm -v` no responde, instálalo con `npm install -g pnpm` desde la terminal normal. `corepack enable` suele pedir permisos de administrador en Windows.
- **GitHub**: antes de que Claude Code suba el CI, ejecuta tú `gh auth refresh -h github.com -s workflow`.
- `.mcp.json` viene preparado para Windows (`cmd /c npx`). En macOS o Linux, cambia `"command"` a `"npx"` y quita `"/c"` y `"npx"` de `args`.
- Avanza una fase cada vez y lee el informe de fase antes de dar el OK a la siguiente.
- Las capturas de `docs/referencias/` son de terceros (videojuegos y una fotografía). Úsalas solo como referencia interna. Ya están en `.gitignore`.
