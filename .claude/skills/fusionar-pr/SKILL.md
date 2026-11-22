---
name: fusionar-pr
description: Fusiona un PR con squash cuando el CI está verde, actualizando la rama si va por detrás. Úsala cuando haya que cerrar un PR ya revisado; no la uses para PR con OK visual pendiente de Javi.
---

# Fusionar un PR

Argumento: el número del PR (`/fusionar-pr 59`).

1. Comprueba que el PR **no** necesita el OK visual de Javi (cambios de interfaz o hitos visuales: CLAUDE.md exige su OK antes de fusionar). Si lo necesita, no lo fusiones y dilo.
2. Ejecuta `node scripts/fusionar-pr.mjs <número>`. El script actualiza la rama si va por detrás, espera a los checks (hasta 25 min; cambia con `--espera-min`) y hace `squash` solo con CI verde y la rama limpia. Con `--sin-fusionar` solo comprueba que está listo.
3. Si el script se para por un check en rojo, **no lo fuerces**: lee solo el job que falla (`gh run view <run> --log-failed`, recortando la salida), arregla la causa en el PR y repite.
4. Si sale «no se pudo borrar la rama local», es normal cuando `main` está abierto en otro worktree: la fusión sí se hizo (comprueba `MERGED`).
5. Los avisos de OSV y `pnpm audit` no bloquean hasta el deploy (issue #52). No pares a preguntar por ellos.
6. Informa en una línea: «#N fusionado» o el motivo por el que no.

Nunca uses `--admin` ni saltes los checks.
