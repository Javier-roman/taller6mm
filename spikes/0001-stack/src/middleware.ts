// Etiqueta cada petición para la medida de CPU con `wrangler tail`: id del isolate, número de
// petición dentro del isolate (n = 1 es arranque en frío) y escenario (`?m=`). Una línea JSON por
// petición, sin datos personales. El id se crea en la primera petición: en el ámbito global de un
// Worker no se pueden generar valores aleatorios.
import { defineMiddleware } from 'astro:middleware';

let isolate: string | undefined;
let count = 0;

export const onRequest = defineMiddleware((context, next) => {
  isolate ??= crypto.randomUUID().slice(0, 8);
  count += 1;
  const scenario = context.url.searchParams.get('m') ?? context.url.pathname;
  console.log(JSON.stringify({ spike: 'req', iso: isolate, n: count, m: scenario }));
  return next();
});
