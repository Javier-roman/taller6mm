// Fusiona un PR cuando el CI está verde: actualiza la rama si va por detrás, espera a los checks y hace squash.
// Uso: node scripts/fusionar-pr.mjs <número> [--espera-min 25] [--sin-fusionar]
// Solo usa `gh` (la sesión la inicia Javi). Nunca fusiona con checks en rojo ni con la rama bloqueada por otra razón.
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

/** Decide el siguiente paso a partir del estado del PR y de sus checks. Pura, para poder probarla. */
export function decidir({ estado, mergeState, checks }) {
  if (estado === 'MERGED') return { accion: 'hecho', motivo: 'ya estaba fusionado' };
  if (estado === 'CLOSED') return { accion: 'parar', motivo: 'el PR está cerrado' };
  const relevantes = checks.filter((c) => c.estado !== 'skipping');
  if (relevantes.some((c) => c.estado === 'fail')) {
    return { accion: 'parar', motivo: `check en rojo: ${relevantes.find((c) => c.estado === 'fail').nombre}` };
  }
  if (mergeState === 'BEHIND') return { accion: 'actualizar', motivo: 'la rama va por detrás de main' };
  if (mergeState === 'DIRTY') return { accion: 'parar', motivo: 'conflictos con main: resolver a mano' };
  if (relevantes.some((c) => c.estado === 'pending')) return { accion: 'esperar', motivo: 'checks en curso' };
  if (mergeState === 'CLEAN') return { accion: 'fusionar', motivo: 'CI verde y rama limpia' };
  return { accion: 'esperar', motivo: `estado de fusión ${mergeState}` };
}

function gh(args) {
  return execFileSync('gh', args, { encoding: 'utf8' });
}

function leer(numero) {
  const pr = JSON.parse(gh(['pr', 'view', String(numero), '--json', 'state,mergeStateStatus']));
  let checks = [];
  try {
    checks = gh(['pr', 'checks', String(numero)])
      .split('\n')
      .filter(Boolean)
      .map((linea) => {
        const [nombre, estado] = linea.split('\t');
        return { nombre, estado };
      });
  } catch (error) {
    // `gh pr checks` sale con código distinto de 0 si hay checks en rojo o pendientes: la salida sigue valiendo.
    checks = String(error.stdout ?? '')
      .split('\n')
      .filter(Boolean)
      .map((linea) => {
        const [nombre, estado] = linea.split('\t');
        return { nombre, estado };
      });
  }
  return { estado: pr.state, mergeState: pr.mergeStateStatus, checks };
}

const dormir = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function principal() {
  const args = process.argv.slice(2);
  const numero = args.find((a) => /^\d+$/.test(a));
  if (!numero) {
    console.error('Uso: node scripts/fusionar-pr.mjs <número> [--espera-min 25] [--sin-fusionar]');
    process.exit(2);
  }
  const iEspera = args.indexOf('--espera-min');
  const esperaMin = iEspera >= 0 ? Number(args[iEspera + 1]) : 25;
  const sinFusionar = args.includes('--sin-fusionar');
  const limite = Date.now() + esperaMin * 60_000;
  let actualizaciones = 0;

  while (Date.now() < limite) {
    const { accion, motivo } = decidir(leer(numero));
    if (accion === 'hecho') return console.log(`#${numero}: ${motivo}`);
    if (accion === 'parar') {
      console.error(`#${numero}: parado — ${motivo}`);
      process.exit(1);
    }
    if (accion === 'actualizar') {
      if (actualizaciones >= 3) {
        console.error(`#${numero}: parado — demasiadas actualizaciones de rama seguidas`);
        process.exit(1);
      }
      actualizaciones += 1;
      gh(['pr', 'update-branch', String(numero)]);
      console.log(`#${numero}: rama actualizada (${actualizaciones}); espero el CI`);
      await dormir(45_000);
      continue;
    }
    if (accion === 'fusionar') {
      if (sinFusionar) return console.log(`#${numero}: listo para fusionar (${motivo})`);
      try {
        gh(['pr', 'merge', String(numero), '--squash', '--delete-branch']);
      } catch (error) {
        // El borrado de la rama local falla si `main` está abierto en otro worktree; la fusión puede haberse hecho.
        console.error(String(error.stderr ?? error.message).split('\n')[0]);
      }
      const final = leer(numero);
      console.log(`#${numero}: ${final.estado}`);
      process.exit(final.estado === 'MERGED' ? 0 : 1);
    }
    await dormir(20_000);
  }
  console.error(`#${numero}: se agotó la espera de ${esperaMin} min`);
  process.exit(1);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await principal();
