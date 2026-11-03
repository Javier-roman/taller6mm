# Runbook · Activar Cloudflare (S3): unos 20 minutos de Javi

> Para Javi. Todo lo que pide credenciales lo haces **tú**, en tu terminal: Claude Code nunca ve tus tokens
> ni tu sesión. Motivos y riesgos: [ADR-0008](../adr/0008-entornos-previews-despliegue.md). Coste previsto:
> 0 €/mes. La revisión de seguridad del 03-11-2026 alargó la receta original de 15 minutos: el token de las
> Previews de PR ya no convive con el código del PR, y hay pruebas negativas antes de encender nada.

**Antes de empezar**
- Verificación en dos pasos (2FA) activa en Cloudflare y en GitHub.
- Una terminal **normal** (no «Ejecutar como administrador») en `C:\dev\bancada`, con `main` al día.
- Desactiva el historial del portapapeles de Windows (Configuración → Sistema → Portapapeles) mientras
  copias tokens, o vacíalo al terminar: un token pegado se queda ahí.

## Paso 0 · Decide en qué cuenta vive Taller6mm (2 min)
En el panel de Cloudflare, mira qué hay ya en tu cuenta (Workers, D1, R2, KV y Pages). Dentro de una misma
cuenta, un Worker con permiso de despliegue puede enlazar las bases y buckets de otros proyectos.
- **Si tiene otros proyectos o datos**: crea una cuenta nueva (gratis) solo para Taller6mm y sigue con ella.
- **Producción** irá en otra cuenta distinta de la de preview (decisión propuesta en el ADR-0008).

## Paso 1 · Iniciar sesión (2 min)
```powershell
cd C:\dev\bancada
pnpm --filter @taller6mm/web exec wrangler login     # abre el navegador (OAuth)
pnpm --filter @taller6mm/web exec wrangler whoami    # apunta el «Account ID»
```
La sesión de wrangler tiene permisos muy amplios y se guarda en tu perfil: al final del paso 3, `logout`.

## Paso 2 · Activar R2 y los avisos de facturación (2 min)
- **R2 Object Storage → Activar**. Pide un método de pago aunque el plan gratuito (10 GB) no cobre. No crees
  buckets todavía: llegan con el código que los use (Fase 3–5).
- **Billing → Notifications**: activa los avisos de uso y de facturación.

## Paso 3 · Bases de preview, base canario y primer despliegue (6 min)
Crear un Worker necesita permisos que el token del CI no tendrá: lo crea tu sesión.

```powershell
cd C:\dev\bancada\apps\web
pnpm exec wrangler d1 create taller6mm-core-preview
pnpm exec wrangler d1 create taller6mm-mercado-preview
pnpm exec wrangler d1 create taller6mm-busqueda-preview
pnpm exec wrangler d1 create taller6mm-canario       # nunca entra en ningún token: sirve para las pruebas negativas
```

1. Copia los tres `database_id` de las bases `*-preview` (no son secretos) en lugar de
   `PENDIENTE_ID_D1_*_PREVIEW` en `apps/web/wrangler.jsonc` y `apps/jobs/wrangler.jsonc`. O pásamelos: los
   pongo yo y los subo en un PR.
2. Migraciones y primer despliegue. Cada línea solo sigue si la anterior fue bien (`if ($?)`), y antes de
   desplegar se comprueba que la build es del Worker de preview:

```powershell
cd C:\dev\bancada\apps\web
foreach ($db in 'CORE','MERCADO','BUSQUEDA') { pnpm exec wrangler d1 migrations apply $db --env preview --remote; if (-not $?) { break } }
cd C:\dev\bancada
$env:CLOUDFLARE_ENV = 'preview'; pnpm --filter @taller6mm/web build; $ok = $?; Remove-Item Env:CLOUDFLARE_ENV
if ($ok) { node scripts/validar-preview.mjs apps/web/dist/server/wrangler.json }
if ($ok -and $?) { pnpm --filter @taller6mm/web exec wrangler deploy }
if ($ok -and $?) { pnpm --filter @taller6mm/jobs exec wrangler deploy --env preview }
pnpm --filter @taller6mm/web exec wrangler logout
```

Apunta la URL que imprime el despliegue de `web`: `https://taller6mm-web-preview.<tu-subdominio>.workers.dev`.

## Paso 4 · Dos tokens con el mínimo privilegio (4 min)
Panel de Cloudflare → **Manage Account → Account API Tokens → Create Token → Custom token**. Caducidad: 6 meses.

| Token | Para qué | Permisos | Entorno de GitHub |
|---|---|---|---|
| `taller6mm-ci-preview` | Despliegue desde `main` y migraciones | **Editor** de los Workers `taller6mm-web-preview` y `taller6mm-jobs-preview`. **D1: Editor** solo de las tres bases `*-preview` si el panel deja elegir bases; si no, a nivel de producto (por eso el paso 0). | `preview` |
| `taller6mm-ci-preview-pr` | Previews de PR | **Editor** solo del Worker `taller6mm-web-preview`. **Sin D1** ni nada más. | `preview-pr` |

Sin permisos de cuenta, DNS ni rutas. El token de producción se crea en el lanzamiento, en la cuenta de
producción y cuando existan sus Workers (solo se puede acotar a Workers que ya existen).

## Paso 5 · GitHub: entornos, secretos y variables (4 min)
1. **Settings → Environments**: crea `preview-pr`. En `preview` y en `preview-pr`, **Deployment branches and
   tags → Selected branches → `main`**. Así ningún workflow de un PR puede usar sus secretos.
2. Secretos (te pide el valor y no queda en el historial; no lo pegues en ningún chat):
   ```powershell
   cd C:\dev\bancada
   gh secret set CLOUDFLARE_API_TOKEN --env preview       # el token taller6mm-ci-preview
   gh secret set CLOUDFLARE_API_TOKEN --env preview-pr    # el token taller6mm-ci-preview-pr
   ```
3. Variables:
   ```powershell
   gh variable set CLOUDFLARE_ACCOUNT_ID --body "<tu Account ID>"
   gh variable set ZAP_TARGET_URL --body "https://taller6mm-web-preview.<tu-subdominio>.workers.dev"
   ```
4. Vacía el portapapeles.

## Paso 6 · Pruebas negativas y encendido (3 min)
Con el token de PR en una variable de la sesión (no se escribe en pantalla ni en el historial):
```powershell
$t = Read-Host "Token taller6mm-ci-preview-pr" -AsSecureString
$env:CLOUDFLARE_API_TOKEN = [System.Net.NetworkCredential]::new('', $t).Password
$env:CLOUDFLARE_ACCOUNT_ID = "<tu Account ID>"
cd C:\dev\bancada\apps\web
pnpm exec wrangler d1 execute taller6mm-canario --remote --command "select 1"            # debe fallar (403)
pnpm exec wrangler d1 execute taller6mm-core-preview --remote --command "select 1"        # debe fallar (sin D1)
Remove-Item Env:CLOUDFLARE_API_TOKEN, Env:CLOUDFLARE_ACCOUNT_ID
```
Si alguna **no** falla, para y cuéntamelo antes de seguir. Si todo falla como debe:
```powershell
gh variable set CLOUDFLARE_PREVIEWS --body activas
```
Después, en cualquier PR abierto: **Actions → Previews → Re-run jobs**. El bot comenta
`Preview de este PR: https://pr-<n>-taller6mm-web-preview.<subdominio>.workers.dev` y el humo comprueba que las
tres bases responden y que lleva `noindex`. Al cerrar el PR, la Preview se borra (y un recolector diario borra
las que se escapen).

## Si algo va mal (incidente)
Apagar la variable **no** contiene un incidente: un PR puede ignorarla. En este orden:
1. Panel de Cloudflare → Account API Tokens → **Roll** (o Delete) del token afectado.
2. `gh secret delete CLOUDFLARE_API_TOKEN --env preview-pr` (o `--env preview`).
3. Borra las Previews: `wrangler preview delete --env preview --name pr-<n>` (o el recolector a mano).
4. Revisa **Audit Logs** de la cuenta y, si hubo escrituras, **D1 Time Travel** para volver atrás.
5. `gh variable set CLOUDFLARE_PREVIEWS --body apagadas` y cuéntamelo para revisar los workflows.

## Qué queda fuera de esta receta
- Producción: cuenta, recursos, dominio, token y workflow manual con tu aprobación, en el lanzamiento.
- Cloudflare Access para las Previews (son públicas con `noindex`, que no es privacidad): antes de que haya
  inicio de sesión o datos reales en preview (Fase 2).
- e2e y Lighthouse contra la preview: cuando esté encendida.
