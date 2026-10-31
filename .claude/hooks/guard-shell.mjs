#!/usr/bin/env node
// Hook PreToolUse (herramientas Bash y PowerShell) de Taller6mm.
// Lee la llamada de Claude Code por stdin y aplica las reglas de guard-shell-rules.mjs.
// Si el propio hook falla, no decide nada y se aplica el flujo normal de permisos.
// Funciona igual en Windows (PowerShell y Git Bash), macOS y Linux.
import { check } from './guard-shell-rules.mjs';

// Lectura asíncrona de stdin: readFileSync(0) puede fallar con tuberías en Windows.
async function readStdin(ms = 5000) {
  const chunks = [];
  const reading = (async () => {
    for await (const chunk of process.stdin) chunks.push(chunk);
  })().catch(() => {});
  let timer;
  await Promise.race([reading, new Promise((resolve) => (timer = setTimeout(resolve, ms)))]);
  clearTimeout(timer);
  process.stdin.destroy();
  return Buffer.concat(chunks).toString('utf8');
}

let result = null;
try {
  const input = JSON.parse(await readStdin());
  result = check(input?.tool_input?.command);
} catch {
  // Sin decisión: se aplica el flujo normal de permisos.
}

if (result) {
  const [permissionDecision, permissionDecisionReason] = result;
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision, permissionDecisionReason },
    }),
  );
}
