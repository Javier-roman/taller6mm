// Reglas del hook guardián de Taller6mm (lógica pura, sin E/S: se prueba con guard-shell.test.mjs).
//   "deny": acciones catastróficas o que exponen secretos. Claude recibe el motivo.
//   "ask":  acciones arriesgadas que Javi debe confirmar.
// Es una barandilla, no una frontera de seguridad: un comando ofuscado a propósito
// (p. ej. concatenando el nombre del archivo en tiempo de ejecución) puede escapar.
// Por eso también hay reglas `deny` de lectura en .claude/settings.json.

const deny = (reason) => ['deny', reason];
const ask = (reason) => ['ask', reason];

// Separa respetando comillas y las quita: "C:\Program Files" es un solo token.
export function tokenize(s) {
  const out = [];
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  let m;
  while ((m = re.exec(s))) out.push(m[1] ?? m[2] ?? m[3]);
  return out;
}

// ── Secretos ─────────────────────────────────────────────────────────────────
const SECRET_MSG =
  'Los archivos de secretos (.env, .dev.vars) no se leen, copian ni muestran. Usa los .example y pide a Javi lo que necesites.';

// .env, .env.local, .dev.vars, .dev.vars.preview… como ruta (no process.env.X); nunca los .example.
const SECRET =
  /(?<=^|[\s'"`/\\=:(,])(?:\.dev\.vars|\.env)(?:\.(?!example\b|sample\b|template\b|dist\b)[\w-]+)?(?=$|[\s;|&)'"`,\]\\])/i;

// Nombres reales que un comodín no debe poder alcanzar.
const SECRET_CANDIDATES = [
  '.dev.vars',
  '.dev.vars.local',
  '.dev.vars.preview',
  '.dev.vars.production',
  '.env',
  '.env.local',
  '.env.development',
  '.env.production',
  '.env.test',
];

// Comandos que solo comprueban si el archivo existe o está ignorado, sin leerlo.
const SECRET_OK = /^(?:ls|dir|Get-ChildItem|gci|Test-Path|git\s+(?:check-ignore|status))\b/i;
const EXAMPLE_FILE = /(?:^|[\\/])\.(?:dev\.vars|env)\.(?:example|sample|template)$/i;
const COPY_CMD = /^(?:cp|copy|Copy-Item|cpi)$/i;

function globToRegExp(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === '*') re += '.*';
    else if (c === '?') re += '.';
    else if (c === '[') {
      const end = glob.indexOf(']', i + 1);
      if (end === -1) re += '\\[';
      else {
        const body = glob.slice(i + 1, end).replace(/^[!^]/, '^').replace(/\\/g, '\\\\');
        re += `[${body}]`;
        i = end;
      }
    } else re += c.replace(/[.+^${}()|\\\]]/g, '\\$&');
  }
  return new RegExp(`^${re}$`, 'i');
}

// ¿Este token es un comodín que puede expandirse a un archivo de secretos?
function globHitsSecret(token) {
  if (!/[*?[]/.test(token)) return false;
  const base = token.replace(/\\/g, '/').split('/').pop() ?? '';
  // Un `*` a secas queda como riesgo residual: bloquearlo rompería demasiados comandos legítimos.
  if (!base || /^[*?]+$/.test(base)) return false;
  try {
    const re = globToRegExp(base);
    return SECRET_CANDIDATES.some((name) => re.test(name));
  } catch {
    return false;
  }
}

// Copia permitida solo si el ORIGEN es un .example (crear tu .dev.vars a partir de la plantilla).
// Al revés (copiar el secreto real a un .example, que sí se sube a git) queda bloqueado.
function isCopyFromExample(segment) {
  const t = tokenize(segment);
  if (!t.length || !COPY_CMD.test(t[0])) return false;
  let src = null;
  const positional = [];
  for (let i = 1; i < t.length; i++) {
    const a = t[i];
    if (/^-(?:Path|LiteralPath)$/i.test(a)) src = t[++i] ?? null;
    else if (/^-Destination$/i.test(a)) i++;
    else if (!a.startsWith('-')) positional.push(a);
  }
  if (positional.length > (src ? 1 : 2)) return false; // cp a b dir: varios orígenes
  src ??= positional[0] ?? null;
  if (!src) return false;
  return src.split(',').every((p) => EXAMPLE_FILE.test(p));
}

function checkSecrets(cmd, segments) {
  const mentions = segments.filter((seg) => SECRET.test(seg) || tokenize(seg).some(globHitsSecret));
  if (!mentions.length) return null;
  // Con tubería o sustitución de comandos, hasta un `ls` puede acabar leyendo el secreto.
  if (/(?<!\|)\|(?!\|)/.test(cmd) || /\$\(|`|<\(/.test(cmd)) return deny(SECRET_MSG);
  for (const seg of mentions) {
    if (SECRET_OK.test(seg) || isCopyFromExample(seg)) continue;
    return deny(SECRET_MSG);
  }
  return null;
}

// ── Borrados ─────────────────────────────────────────────────────────────────
const DELETE_CMD = /^(?:rm|rmdir|rd|del|erase|Remove-Item|ri)$/i;
const PREFIX_OK = /^(?:sudo|doas|xargs|exec|command|nohup|time|env|busybox|&|\w+=.*)$/i;
const isRecursiveFlag = (t) =>
  /^-(?=[a-zA-Z]{1,3}$)[a-zA-Z]*[rR][a-zA-Z]*$/.test(t) || // -r, -rf, -fr (estilo POSIX)
  /^-rec(?:u(?:r(?:s(?:e)?)?)?)?$/i.test(t) || // -Recurse (PowerShell, también abreviado)
  /^\/s$/i.test(t); // rd /s (cmd)
const CATASTROPHIC =
  /^(?:\/\*?|~\/?\*?|\$HOME\/?|\$\{HOME\}\/?|\$env:(?:USERPROFILE|HOMEDRIVE|SystemRoot|windir)\/?|%(?:USERPROFILE|SystemRoot|windir)%\/?|[a-zA-Z]:\/?\*?|[a-zA-Z]:\/(?:windows|users|program files(?: \(x86\))?|programdata)\/?|[a-zA-Z]:\/users\/[^/]+\/?)$/i;
const BUILD_DIR =
  /^(?:[a-zA-Z]:\/)?(?:\.\/)?(?:[\w .@()-]+\/)*(?:node_modules|dist|build|\.astro|\.wrangler|\.turbo|coverage|test-results|playwright-report|\.lighthouseci|\.cache|tmp)\/?$/;

function analyzeDelete(segment) {
  const tokens = tokenize(segment);
  const i = tokens.findIndex((t) => DELETE_CMD.test(t));
  if (i === -1 || !tokens.slice(0, i).every((t) => PREFIX_OK.test(t))) return null;
  const args = tokens.slice(i + 1);
  const targets = args
    .filter((t) => !t.startsWith('-') && !/^\/[a-zA-Z]$/.test(t) && !/^\d*[<>]/.test(t) && t !== '&')
    .map((t) => t.replace(/\\/g, '/'));
  if (targets.some((t) => CATASTROPHIC.test(t))) {
    return deny('Borrado de la raíz del disco, del sistema o de tu carpeta de usuario bloqueado.');
  }
  if (args.some(isRecursiveFlag) && (targets.length === 0 || targets.some((t) => !BUILD_DIR.test(t)))) {
    return ask('Borrado recursivo fuera de directorios de build: confirma qué se borra.');
  }
  return null;
}

// ── Listas de reglas ─────────────────────────────────────────────────────────
const DENY = [
  [
    /\b(?:curl|wget|iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b[^|]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|node|python3?|iex|Invoke-Expression)\b/i,
    'Ejecutar directamente código descargado (curl | sh, irm | iex) está bloqueado.',
  ],
  [
    /\b(?:iex|Invoke-Expression)\b[^;|]*\b(?:iwr|irm|Invoke-WebRequest|Invoke-RestMethod|DownloadString|curl|wget)\b/i,
    'Ejecutar código descargado de internet está bloqueado.',
  ],
  [
    /\bgit\s+push\b(?=.*(?:--force\b|--force-with-lease\b|\s-f\b))(?=.*\b(?:main|master)\b)/i,
    'Push forzado a main/master bloqueado.',
  ],
  [/\b(?:npm|pnpm|yarn|bun)\s+publish\b/i, 'Publicar paquetes está bloqueado en este proyecto.'],
  [/\bgh\s+repo\s+delete\b/i, 'Borrar repositorios está bloqueado.'],
  [
    /\bwrangler\s+(?:d1\s+delete|r2\s+bucket\s+delete|kv\s+namespace\s+delete|queues\s+delete|delete)\b/i,
    'Borrar recursos de Cloudflare está bloqueado: pídeselo a Javi.',
  ],
  // Cubre `wrangler secret put`, `wrangler versions secret put` y `wrangler preview [base-config] secret put`.
  [/\bwrangler\b[^;|&]*\bsecret\s+(?:put|bulk)\b/i, 'Los secretos los introduce Javi: dile el comando exacto y lo ejecuta él.'],
  [/\bgh\s+secret\s+set\b/i, 'Los secretos de GitHub los introduce Javi: dile el comando exacto y lo ejecuta él.'],
  [
    /\b(?:mkfs|diskpart|Format-Volume|Clear-Disk|Initialize-Disk)\b|\bdd\s+[^;|&]*\bof=\/dev\/|\bformat(?:\.com)?\s+[a-z]:/i,
    'Operación de disco bloqueada.',
  ],
  [/\b(?:Set-MpPreference|Add-MpPreference)\b/i, 'Cambiar la configuración de Microsoft Defender está bloqueado.'],
];

const ASK = [
  [/\bgit\s+push\b.*\b(?:main|master)\b/i, 'Push a main/master: confirma que quieres publicar en la rama principal.'],
  [/\bgit\s+(?:reset\s+--hard|clean\s+-[a-zA-Z]*f)/i, 'Operación git destructiva: confirma.'],
  [/\bwrangler\s+d1\s+(?:execute|migrations\s+apply)\b(?=.*--remote)/i, 'Operación sobre una base de datos remota: confirma.'],
  // El entorno de Cloudflare se elige al compilar (CLOUDFLARE_ENV), así que el hook no puede saber
  // si un deploy va a preview o a producción: todo deploy real se confirma.
  [/\bwrangler\s+deploy\b(?!.*--dry-run)/i, 'Despliegue a Cloudflare: confirma el entorno (preview o producción).'],
  [/\bwrangler\s+(?:rollback|versions\s+deploy)\b/i, 'Cambio de versión en Cloudflare: confirma.'],
  [/\bwrangler\s+preview\s+delete\b/i, 'Borrar una Preview de Cloudflare: confirma cuál.'],
  [
    /\bwrangler\s+(?:r2\s+object\s+delete|kv\s+(?:key|bulk)\s+delete|queues\s+purge)\b/i,
    'Borrado de datos en Cloudflare: confirma.',
  ],
  [/\bpnpm\b[^;|&]*?\s(?:run\s+)?deploy\b/i, 'Despliegue: confirma.'],
  [/\bcrawl\b.*--live\b/i, 'Petición real a una tienda (--live): confirma la fuente, el número de páginas y el ritmo.'],
  [/\b(?:sudo|doas|runas)\b|\bStart-Process\b[^;|]*-Verb\s+RunAs\b/i, 'Comando con privilegios elevados: confirma.'],
  [/\bgh\s+pr\s+merge\b/i, 'Fusionar un PR: confirma.'],
  [/\bgh\s+repo\s+(?:create|edit)\b|\bgh\s+api\b[^;|]*-X\s*(?:PUT|PATCH|POST|DELETE)\b/i, 'Cambio en GitHub (repo o ajustes): confirma.'],
  [
    /\bSet-ExecutionPolicy\b|\breg(?:\.exe)?\s+(?:add|delete|import)\b|\b(?:New|Set|Remove)-ItemProperty\b[^;|]*\bHK(?:LM|CU)\b|\bschtasks(?:\.exe)?\s+\/create\b|\bRegister-ScheduledTask\b|\bNew-Service\b|\bsc(?:\.exe)?\s+create\b|\bnetsh\b/i,
    'Cambio de configuración del sistema (registro, tareas programadas, servicios, red o ejecución de scripts): confirma.',
  ],
];

/** Devuelve ['deny'|'ask', motivo] o null si el comando sigue el flujo normal de permisos. */
export function check(rawCmd) {
  const cmd = String(rawCmd ?? '')
    .replace(/\s+/g, ' ')
    .trim();
  if (!cmd) return null;
  const segments = cmd
    .split(/&&|\|\||;|\|/)
    .map((s) => s.trim())
    .filter(Boolean);

  const secret = checkSecrets(cmd, segments);
  if (secret) return secret;

  const deletes = segments.map(analyzeDelete).filter(Boolean);
  const deniedDelete = deletes.find(([d]) => d === 'deny');
  if (deniedDelete) return deniedDelete;

  for (const [re, reason] of DENY) if (re.test(cmd)) return deny(reason);
  if (deletes.length) return deletes[0];
  for (const [re, reason] of ASK) if (re.test(cmd)) return ask(reason);
  return null;
}
