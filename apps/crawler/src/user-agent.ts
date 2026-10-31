// User-Agent identificado del rastreador (docs/04 §3): `Taller6mmBot/<versión> (+https://<dominio>/bot)`.
// La página /bot explica qué rastreamos y cómo excluirse. Todavía no hay dominio: se pasa siempre
// de forma explícita, nunca se inventa uno por defecto (principio 2, datos honestos).
import { BRAND } from '@taller6mm/ui/brand';
import pkg from '../package.json' with { type: 'json' };

const SEMVER = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/;

export interface UserAgentOptions {
  /** Versión del rastreador; por defecto, la de apps/crawler/package.json. */
  version?: string;
  /** URL pública de la página /bot, en https y sin parámetros. */
  infoUrl: string;
}

export function buildUserAgent({ version = pkg.version, infoUrl }: UserAgentOptions): string {
  if (!SEMVER.test(version)) throw new Error(`Versión no válida para el User-Agent: ${version}`);
  let url: URL;
  try {
    url = new URL(infoUrl);
  } catch {
    throw new Error(`URL de /bot no válida: ${infoUrl}`);
  }
  if (url.protocol !== 'https:') throw new Error('La URL de /bot debe ir en https');
  if (url.pathname !== '/bot' || url.search || url.hash || url.username || url.password) {
    throw new Error('La URL de /bot debe ser https://<dominio>/bot, sin parámetros ni credenciales');
  }
  return `${BRAND.botName}/${version} (+${url.origin}/bot)`;
}
