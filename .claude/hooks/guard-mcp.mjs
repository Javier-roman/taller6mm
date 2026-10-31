#!/usr/bin/env node
// Hook PreToolUse de las herramientas del MCP de Playwright (matcher `mcp__playwright__.*`).
// Aplica guard-mcp-rules.mjs. Si el propio hook falla, deniega: con rutas de archivo en juego,
// fallar cerrado es lo prudente (la herramienta se puede reintentar).
import { checkMcp } from './guard-mcp-rules.mjs';

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

let result;
try {
  const input = JSON.parse(await readStdin());
  const root = process.env.CLAUDE_PROJECT_DIR || input.cwd || process.cwd();
  result = checkMcp(input.tool_name, input.tool_input, root);
} catch {
  result = ['deny', 'El hook guardián del MCP no pudo analizar la llamada.'];
}

if (result) {
  const [permissionDecision, permissionDecisionReason] = result;
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision, permissionDecisionReason },
    }),
  );
}
