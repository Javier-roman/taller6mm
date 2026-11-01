// Texturas procedurales de La Armería: se dibujan en un canvas con una semilla fija, así que no hay
// descargas, ni dudas de licencia (CLAUDE.md, principio 5), y salen idénticas en A, en B y al hornear.
// Los colores de marca vienen de los tokens de @taller6mm/ui; los de materiales (ladrillo, hormigón)
// son físicos de la escena, no de interfaz.
import { colors, FONT_FAMILIES } from '@taller6mm/ui/tokens';
import { CanvasTexture, NoColorSpace, RepeatWrapping, SRGBColorSpace } from 'three';

/** PRNG con semilla (mulberry32): mismas texturas en cada carga y en cada horneado. */
function azar(semilla: number) {
  let s = semilla >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function lienzo(ancho: number, alto: number) {
  const canvas = document.createElement('canvas');
  canvas.width = ancho;
  canvas.height = alto;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) throw new Error('Canvas 2D no disponible');
  return { canvas, ctx };
}

function textura(canvas: HTMLCanvasElement, repetir?: readonly [number, number], datos = false) {
  const t = new CanvasTexture(canvas);
  t.colorSpace = datos ? NoColorSpace : SRGBColorSpace;
  t.anisotropy = 4;
  if (repetir) {
    t.wrapS = RepeatWrapping;
    t.wrapT = RepeatWrapping;
    t.repeat.set(repetir[0], repetir[1]);
  }
  return t;
}

/** Grano fino por píxel, para que nada parezca plástico liso. */
function grano(ctx: CanvasRenderingContext2D, ancho: number, alto: number, fuerza: number, rnd: () => number) {
  const img = ctx.getImageData(0, 0, ancho, alto);
  for (let i = 0; i < img.data.length; i += 4) {
    const n = (rnd() - 0.5) * fuerza;
    img.data[i] = (img.data[i] ?? 0) + n;
    img.data[i + 1] = (img.data[i + 1] ?? 0) + n;
    img.data[i + 2] = (img.data[i + 2] ?? 0) + n;
  }
  ctx.putImageData(img, 0, 0);
}

/**
 * Mapa de normales (convención OpenGL, +Y arriba) a partir de un mapa de alturas en gris, con
 * diferencias centrales y bordes que se repiten. Es lo que la linterna "lee" al pasar rasante.
 */
function normalesDesdeAlturas(alturas: CanvasRenderingContext2D, ancho: number, alto: number, fuerza: number) {
  const src = alturas.getImageData(0, 0, ancho, alto).data;
  const { canvas, ctx } = lienzo(ancho, alto);
  const out = ctx.createImageData(ancho, alto);
  const h = (x: number, y: number) => (src[(((y + alto) % alto) * ancho + ((x + ancho) % ancho)) * 4] ?? 0) / 255;
  for (let y = 0; y < alto; y++) {
    for (let x = 0; x < ancho; x++) {
      const dx = (h(x + 1, y) - h(x - 1, y)) * fuerza;
      const dy = (h(x, y + 1) - h(x, y - 1)) * fuerza;
      const inv = 1 / Math.hypot(dx, dy, 1);
      const i = (y * ancho + x) * 4;
      out.data[i] = (-dx * inv * 0.5 + 0.5) * 255;
      out.data[i + 1] = (dy * inv * 0.5 + 0.5) * 255;
      out.data[i + 2] = (inv * 0.5 + 0.5) * 255;
      out.data[i + 3] = 255;
    }
  }
  ctx.putImageData(out, 0, 0);
  return canvas;
}

export interface TexturaConRelieve {
  readonly mapa: CanvasTexture;
  readonly normal: CanvasTexture;
}

export function texturaLadrillo(repetir: readonly [number, number]): TexturaConRelieve {
  const rnd = azar(11);
  const [W, H] = [1024, 512];
  const color = lienzo(W, H);
  const alt = lienzo(W, H);
  color.ctx.fillStyle = '#2a2622'; // llaga (mortero oscuro)
  color.ctx.fillRect(0, 0, W, H);
  alt.ctx.fillStyle = 'rgb(70 70 70)';
  alt.ctx.fillRect(0, 0, W, H);
  const fila = 64;
  const ancho = 210;
  for (let y = 0; y < H; y += fila) {
    const desfase = (y / fila) % 2 === 0 ? 0 : ancho / 2;
    for (let x = -ancho; x < W + ancho; x += ancho) {
      const r = 92 + rnd() * 34;
      const g = 54 + rnd() * 18;
      const b = 40 + rnd() * 14;
      color.ctx.fillStyle = `rgb(${r} ${g} ${b})`;
      color.ctx.fillRect(x + desfase + 5, y + 5, ancho - 10, fila - 10);
      const a = 190 + rnd() * 40;
      alt.ctx.fillStyle = `rgb(${a} ${a} ${a})`;
      alt.ctx.fillRect(x + desfase + 6, y + 6, ancho - 12, fila - 12);
      // Desconchones y manchas: el ladrillo de una armería no está recién puesto.
      for (let k = 0; k < 6; k++) {
        const px = x + desfase + 5 + rnd() * (ancho - 30);
        const py = y + 5 + rnd() * (fila - 20);
        const pw = 6 + rnd() * 22;
        const ph = 3 + rnd() * 9;
        color.ctx.fillStyle = `rgb(${r - 24} ${g - 14} ${b - 10} / ${0.25 + rnd() * 0.3})`;
        color.ctx.fillRect(px, py, pw, ph);
        alt.ctx.fillStyle = `rgb(120 120 120 / ${0.3 + rnd() * 0.4})`;
        alt.ctx.fillRect(px, py, pw, ph);
      }
    }
  }
  grano(color.ctx, W, H, 26, rnd);
  grano(alt.ctx, W, H, 18, rnd);
  return {
    mapa: textura(color.canvas, repetir),
    normal: textura(normalesDesdeAlturas(alt.ctx, W, H, 2.2), repetir, true),
  };
}

export function texturaHormigon(repetir: readonly [number, number]): TexturaConRelieve {
  const rnd = azar(23);
  const W = 512;
  const color = lienzo(W, W);
  const alt = lienzo(W, W);
  color.ctx.fillStyle = '#4b4d50';
  color.ctx.fillRect(0, 0, W, W);
  alt.ctx.fillStyle = 'rgb(128 128 128)';
  alt.ctx.fillRect(0, 0, W, W);
  for (let k = 0; k < 140; k++) {
    const g = 60 + rnd() * 30;
    const [cx, cy, rx, ry, rot] = [rnd() * W, rnd() * W, 10 + rnd() * 70, 8 + rnd() * 50, rnd() * 3];
    color.ctx.fillStyle = `rgb(${g} ${g + 1} ${g + 3} / ${0.05 + rnd() * 0.1})`;
    color.ctx.beginPath();
    color.ctx.ellipse(cx, cy, rx, ry, rot, 0, Math.PI * 2);
    color.ctx.fill();
    const a = 100 + rnd() * 60;
    alt.ctx.fillStyle = `rgb(${a} ${a} ${a} / 0.12)`;
    alt.ctx.beginPath();
    alt.ctx.ellipse(cx, cy, rx, ry, rot, 0, Math.PI * 2);
    alt.ctx.fill();
  }
  // Poros del hormigón pulido.
  for (let k = 0; k < 900; k++) {
    const [px, py, r] = [rnd() * W, rnd() * W, 0.6 + rnd() * 1.6];
    alt.ctx.fillStyle = 'rgb(40 40 40 / 0.8)';
    alt.ctx.beginPath();
    alt.ctx.arc(px, py, r, 0, Math.PI * 2);
    alt.ctx.fill();
  }
  grano(color.ctx, W, W, 30, rnd);
  grano(alt.ctx, W, W, 22, rnd);
  return {
    mapa: textura(color.canvas, repetir),
    normal: textura(normalesDesdeAlturas(alt.ctx, W, W, 1.4), repetir, true),
  };
}

export function texturaNogal() {
  const rnd = azar(37);
  const { canvas, ctx } = lienzo(1024, 256);
  ctx.fillStyle = '#4a2f1e';
  ctx.fillRect(0, 0, 1024, 256);
  for (let k = 0; k < 90; k++) {
    const y = rnd() * 256;
    ctx.strokeStyle = `rgb(${30 + rnd() * 30} ${18 + rnd() * 16} ${10 + rnd() * 10} / ${0.25 + rnd() * 0.35})`;
    ctx.lineWidth = 1 + rnd() * 3;
    ctx.beginPath();
    ctx.moveTo(0, y);
    for (let x = 0; x <= 1024; x += 64) ctx.lineTo(x, y + Math.sin(x / (80 + rnd() * 60)) * 6 + (rnd() - 0.5) * 3);
    ctx.stroke();
  }
  grano(ctx, 1024, 256, 14, rnd);
  return textura(canvas);
}

export function texturaCorcho() {
  const rnd = azar(41);
  const { canvas, ctx } = lienzo(256, 256);
  ctx.fillStyle = '#7d5d3c';
  ctx.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) {
    const g = rnd();
    ctx.fillStyle = g > 0.5 ? 'rgb(150 116 78 / 0.5)' : 'rgb(70 50 32 / 0.55)';
    ctx.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3);
  }
  return textura(canvas, [2, 2]);
}

export function texturaTapete() {
  const { canvas, ctx } = lienzo(1024, 512);
  ctx.fillStyle = '#1d3328';
  ctx.fillRect(0, 0, 1024, 512);
  ctx.strokeStyle = 'rgb(232 228 220 / 0.18)';
  ctx.lineWidth = 1;
  for (let x = 0; x <= 1024; x += 32) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 512);
    ctx.stroke();
  }
  for (let y = 0; y <= 512; y += 32) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(1024, y);
    ctx.stroke();
  }
  // Regla en mm a lo largo del borde: el banco mide de verdad (docs/03 §3.3).
  ctx.fillStyle = 'rgb(232 228 220 / 0.55)';
  for (let x = 0; x <= 1024; x += 8) ctx.fillRect(x, 0, 1, x % 64 === 0 ? 18 : 8);
  grano(ctx, 1024, 512, 12, azar(53));
  return textura(canvas);
}

/** Tira de ranuras numeradas del armero, como las etiquetas de ref-08. */
export function texturaTiraNumerada(desde: number, cuantos: number) {
  const { canvas, ctx } = lienzo(1024, 64);
  ctx.fillStyle = '#d9d6cf';
  ctx.fillRect(0, 0, 1024, 64);
  ctx.fillStyle = '#16181b';
  ctx.font = `700 34px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const paso = 1024 / cuantos;
  for (let i = 0; i < cuantos; i++) {
    ctx.fillText(String(desde + i).padStart(2, '0'), paso * (i + 0.5), 34);
    ctx.fillRect(paso * i, 0, 2, 64);
  }
  grano(ctx, 1024, 64, 14, azar(61));
  return textura(canvas);
}

export interface OpcionesRotulo {
  readonly ancho?: number;
  readonly alto?: number;
  /** Texto pequeño bajo el título (el dato vivo). */
  readonly dato?: string;
  /** Marca «DEMO» en la esquina: los datos son de ejemplo. */
  readonly demo?: boolean;
  readonly tinta?: string;
  readonly fondo?: string;
}

/**
 * Rótulo a plantilla sobre una chapa (docs/02 §4.5): título en Big Shoulders Stencil y dato en
 * JetBrains Mono. Sirve de mapa de color y de emisión: al encender el tubo, el rótulo se ilumina.
 */
export function texturaRotulo(texto: string, opciones: OpcionesRotulo = {}) {
  const ancho = opciones.ancho ?? 1024;
  const alto = opciones.alto ?? 256;
  const { canvas, ctx } = lienzo(ancho, alto);
  ctx.fillStyle = opciones.fondo ?? '#15171a';
  ctx.fillRect(0, 0, ancho, alto);
  // Remaches de la chapa.
  ctx.fillStyle = 'rgb(232 228 220 / 0.22)';
  for (const [x, y] of [
    [18, 18],
    [ancho - 18, 18],
    [18, alto - 18],
    [ancho - 18, alto - 18],
  ] as const) {
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fill();
  }
  const tinta = opciones.tinta ?? colors['laton-claro'];
  ctx.fillStyle = tinta;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'center';
  const tamTitulo = Math.round(alto * (opciones.dato ? 0.46 : 0.62));
  ctx.font = `700 ${tamTitulo}px ${FONT_FAMILIES.rotulo}`;
  ctx.letterSpacing = `${Math.round(tamTitulo * 0.06)}px`;
  ctx.fillText(texto.toUpperCase(), ancho / 2, opciones.dato ? alto * 0.38 : alto / 2, ancho - 60);
  if (opciones.dato) {
    ctx.letterSpacing = '0px';
    ctx.fillStyle = colors.hueso;
    ctx.font = `400 ${Math.round(alto * 0.17)}px ${FONT_FAMILIES.datos}`;
    ctx.fillText(opciones.dato, ancho / 2, alto * 0.78, ancho - 60);
  }
  if (opciones.demo) {
    ctx.textAlign = 'right';
    ctx.fillStyle = colors['estado-aviso'];
    ctx.font = `700 ${Math.round(alto * 0.11)}px ${FONT_FAMILIES.datos}`;
    ctx.fillText('DEMO', ancho - 34, alto * 0.16);
  }
  grano(ctx, ancho, alto, 10, azar(texto.length * 97));
  return textura(canvas);
}

/** Pantalla del tablón: bajadas de precio de ejemplo en señal naranja. */
export function texturaPantalla() {
  const { canvas, ctx } = lienzo(512, 320);
  ctx.fillStyle = '#07090b';
  ctx.fillRect(0, 0, 512, 320);
  ctx.fillStyle = colors.niebla;
  ctx.font = `400 26px ${FONT_FAMILIES.datos}`;
  ctx.fillText('BAJADAS · DEMO', 24, 44);
  const filas = [
    ['Bocacha 14 mm CCW', '−12 %'],
    ['Óptica 1-4×24', '−8 %'],
    ['Cargador mid-cap', '−15 %'],
  ];
  filas.forEach(([pieza, bajada], i) => {
    const y = 110 + i * 70;
    ctx.fillStyle = colors.hueso;
    ctx.font = `400 28px ${FONT_FAMILIES.datos}`;
    ctx.fillText(pieza ?? '', 24, y);
    ctx.fillStyle = colors['naranja-senal'];
    ctx.font = `700 34px ${FONT_FAMILIES.datos}`;
    ctx.textAlign = 'right';
    ctx.fillText(bajada ?? '', 488, y);
    ctx.textAlign = 'left';
  });
  return textura(canvas);
}
