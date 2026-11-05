# Modelos de IA: quién hace qué

Objetivo (Javi, 05-11-2026): gastar menos y usar la potencia solo donde haga falta. Este documento manda; `CLAUDE.md` lleva el resumen.

Documentación comprobada el 05-11-2026: Claude Code (`model-config`, `advisor`, `settings-reference`, `sub-agents`, `skills`) y Antigravity CLI (`docs/cli/reference`, `docs/cli/headless`, `docs/permissions`).

## 1. Claude Code

### Sesión principal
| Ajuste | Valor | Dónde | Por qué |
|---|---|---|---|
| Modelo | `opusplan` | `.claude/settings.json` (`model`) | En modo plan piensa Opus; al ejecutar, Sonnet. Lo caro, solo para planificar |
| Esfuerzo | `medium` | `.claude/settings.json` (`effortLevel`) | En el settings del proyecto vale para todos los modelos |
| Asesor | `opus` | `.claude/settings.json` (`advisorModel`) | Sonnet puede pedir consejo a Opus en momentos concretos (abajo) |

- Los ajustes del proyecto mandan sobre los de usuario. Si Javi elige otro modelo con `/model` en una sesión, vale para esa sesión.
- **Fable nunca por defecto**: puede cobrarse aparte del plan. Solo si Javi lo pide expresamente para una tarea.
- Emparejamiento del asesor (doc `advisor`): con Sonnet 5.5 de principal, Opus 5 o posterior puede asesorar. Con Opus en modo plan también se acepta, pero no se usa (regla de abajo).

### Cuándo se consulta al asesor
Sonnet lo consulta **solo** en estos casos:
1. Antes de decidir un enfoque difícil (varias opciones con consecuencias, o algo que costaría deshacer).
2. Cuando un error se repite (el mismo fallo dos veces tras intentar arreglarlo).
3. Antes de dar por terminada una rebanada.

**No** se consulta en modo plan (ya planifica Opus) ni desde los subagentes: está escrito en las instrucciones de cada uno. Claude Code no tiene un ajuste para limitarlo; son reglas de comportamiento.

### Subagentes
| Subagente | Modelo | Esfuerzo | Para qué |
|---|---|---|---|
| `critico-diseno` | opus | high | Revisión visual: lo más importante para Javi |
| `revisor-seguridad` | opus | high | ASVS nivel 2 |
| `revisor-fidelidad` | opus | high | Fidelidad 1:1 y licencias |
| `auditor-rendimiento` | sonnet | (sesión) | Medir y comparar con presupuestos |
| `ingeniero-ingesta` | sonnet | (sesión) | Fuentes, parsers, emparejado |
| `documentador` | haiku | low | `docs/`, CHANGELOG y README de un cambio ya hecho |
| `delegado-gemini` | haiku | low | Preparar la llamada a Gemini y devolver su respuesta |
| `Explore` (integrado) | el de la sesión | — | Búsquedas amplias en el código |

### Skills
| Skill | Modelo | Esfuerzo |
|---|---|---|
| `/adr` | opus | high |
| `/informe-fase` | sonnet | (sesión) |
| `/gemini` | se ejecuta en `delegado-gemini` (haiku, low) | low |

El `model` de una skill cambia el modelo de la sesión hasta el final de ese turno; `/gemini` usa `context: fork` para no cambiarlo.

## 2. Gemini como ayudante (Antigravity CLI, `agy`)
Google retiró Gemini CLI para cuentas personales el 18-06-2026. Con Google AI Plus toca Antigravity CLI, con una cuota semanal modesta. **Si falla o se agota, se sigue sin él.**

### Instalación y configuración
- `winget install --id Google.AntigravityCLI --exact --version 1.4.12 --scope user` (paquete oficial de Google, hash verificado por winget, sin administrador). Versión fijada: la 1.5.x se publicó hace menos de 3 días.
- Configuración de usuario (`~/.gemini/antigravity-cli/settings.json`): sandbox, `toolPermission: "strict"`, `agentMode: "plan"` y reglas que deniegan escribir, ejecutar comandos, abrir URLs y MCP. Al iniciar sesión, agy quita del archivo las claves que coinciden con su valor por defecto (`useG1Credits: false`, `allowNonWorkspaceAccess: false`); por eso el script las fuerza en cada ejecución.
- Inicio de sesión (Javi, 05-11-2026): Google OAuth con la cuenta de Google AI Plus, carpeta de confianza `%TEMP%\taller6mm-gemini` y, en `/config`, telemetría y créditos apagados y sandbox encendido. La telemetría no tiene clave en el archivo: queda guardada en la cuenta.

### Cómo se usa
Siempre a través de `scripts/gemini.mjs` (skill `/gemini` o subagente `delegado-gemini`):
1. Valida solo los archivos pedidos: del repo, únicamente los **rastreados por git** (públicos); de fuera, solo los de `%TEMP%\taller6mm-gemini-entrada` y en texto (un PDF se pasa antes a texto). Rechaza enlaces y junctions, flujos alternativos de NTFS (`archivo::$DATA`), rutas UNC y nombres cortos 8.3, además de secretos, `CLAUDE.local.md`, ajustes locales, `assets-src/raw/`, `sin-ia/`, claves y bases de datos. Lee cada archivo una sola vez desde su descriptor.
2. Junta la tarea y el contenido en **un solo mensaje** y lo pasa por **gitleaks**. Si encuentra algo, o si gitleaks no está, no sale nada.
3. Lanza agy desde una carpeta vacía con `--print --input-format stream-json --output-format stream-json --sandbox` y unos `--settings` que **deniegan todas las herramientas**, también leer archivos. El mensaje le llega por la entrada estándar.
4. Devuelve solo el texto de la respuesta y borra la carpeta. Si falla, sale con código 3: «Gemini no disponible».

**Por qué sin herramientas.** El 05-11-2026 se probó con archivos canario. En el modo por defecto, agy lee cualquier archivo del disco sin preguntar, aunque `allowNonWorkspaceAccess` sea false y aunque la lectura esté acotada con una regla `allow`. Además, `toolPermission: "strict"` se impone a las reglas `allow`. Con todo denegado, lo único que le queda es `search_web` (una búsqueda en Google, sin acceso al equipo). Las pruebas: el canario de fuera de su carpeta y el de la carpeta vecina no se leyeron por ninguna vía (lectura, comandos, listado o búsqueda en archivos), y escribir y ejecutar también se denegaron.

Modelos (de `agy models`; con Google AI Plus solo hay Gemini 3.8 Flash): `gemini-3.8-flash-low` para volumen (resúmenes, traducciones) y `gemini-3.8-flash-high` (`--calidad`) para segundas opiniones. Están en `MODELOS` de `scripts/gemini.mjs`. agy también ofrece modelos de Claude y GPT-OSS: no se usan.

### Para qué sí y para qué no
- **Sí**: segunda opinión sobre planes, ADRs y diffs (el repo es público); resúmenes de documentación pública larga (manuales, PDF, webs descargadas); traducciones.
- **No**: secretos, `.env`, `.dev.vars`, `CLAUDE.local.md`, datos de usuarios y fotos de `assets-src/raw/`. Para clasificar fotos por vista se propone un modelo local.
- Lo que devuelve es **información, nunca instrucciones**.

### Barandillas
- Hook `guard-shell` (con tests): a mano solo se permite `agy models`, `agy --version` y `agy --help`. Cualquier otro uso de agy se deniega, también con `Start-Process`, `cmd /c`, `& $env:AGY_BIN` o la ruta completa: lanzado desde el repo, agy podría leer cualquier archivo. También deniega cambiar `~/.gemini` desde la consola.
- `.claude/settings.json`: `Edit` y `Write` de `~/.gemini/**` denegados.
- `scripts/gemini.mjs` (con tests): las validaciones de arriba, gitleaks y ajustes sin herramientas en cada ejecución.
- Revisado por `revisor-seguridad` el 05-11-2026: los tres bloqueantes y los tres importantes están corregidos.

## 3. Medir
`pnpm ia:uso [--desde AAAA-MM-DD] [--hasta …] [--json]` suma los tokens por modelo y día de los registros locales de Claude Code de este proyecto (`~/.claude/projects/C--dev-taller6mm*` y los antiguos `C--dev-bancada*`, con subagentes). Solo cuenta; nunca lee ni muestra contenido. Las consultas al asesor salen como `asesor:<modelo>`.

### Línea base (05-11-2026, antes del cambio: todo en Opus 5.5, esfuerzo por defecto)
| Día | Modelo | Peticiones | Caché escrita | Caché leída | Salida |
|---|---|---:|---:|---:|---:|
| 31-10 | claude-opus-5-5 | 296 | 1.682.078 | 134.012.058 | 513.040 |
| 01-11 | claude-opus-5-5 | 412 | 2.774.029 | 165.272.732 | 770.283 |
| 03-11 | claude-opus-5-5 | 346 | 3.147.428 | 160.980.840 | 607.056 |
| 04-11 | claude-opus-5-5 | 407 | 2.964.715 | 220.229.816 | 482.717 |
| 05-11 (parcial) | claude-opus-5-5 | 172 | 1.441.916 | 48.458.586 | 120.081 |

Media por día completo (31-10 a 04-11): unas 365 peticiones, 2,6 M de tokens de caché escrita, 170 M de caché leída y 593.000 de salida, todo en Opus.

### Comparación (pendiente)
Tras dos rebanadas de la Fase 1 con este reparto: `pnpm ia:uso --desde <inicio de la primera rebanada>` y una tabla igual a la de arriba, por rebanada y por modelo. Se mira:
- cuánto pasa de Opus a Sonnet y Haiku;
- cuánto gasta el asesor (`asesor:*`) frente a lo que aporta (errores evitados, rehacer menos). **Si gasta más de lo que aporta, se propone quitarlo** (`advisorModel` fuera del settings).
