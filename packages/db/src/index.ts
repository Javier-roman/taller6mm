// Esquemas y migraciones de las tres bases D1 de Taller6mm. Sin JOIN entre bases: se compone en el servicio.
export * as busqueda from './busqueda.ts';
export * as core from './core.ts';
export * as mercado from './mercado.ts';
export { BASES, type Base, BINDINGS } from './meta.ts';
