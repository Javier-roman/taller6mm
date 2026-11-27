// Texturas procedurales de La Armería: se dibujan en un canvas con una semilla fija, así que no hay
// descargas, ni dudas de licencia (CLAUDE.md, principio 5), y salen idénticas en A, en B y al hornear.
// Los colores de marca vienen de los tokens de @taller6mm/ui; los de materiales (ladrillo, hormigón)
// son físicos de la escena, no de interfaz.
import { colors, FONT_FAMILIES } from '@taller6mm/ui/tokens';
import { CanvasTexture, NoColorSpace, RepeatWrapping, SRGBColorSpace } from 'three';

/** PRNG con semilla (mulberry32): mismas texturas en cada carga y en cada horneado. */
export function azar(semilla: number) {
  let s = semilla >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function lienzo(ancho: number, alto: number) {
  const canvas = document.createElement('canvas');
  canvas.width = ancho;
  canvas.height = alto;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) throw new Error('Canvas 2D no disponible');
  return { canvas, ctx };
}

export function textura(canvas: HTMLCanvasElement, repetir?: readonly [number, number], datos = false) {
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
export function grano(ctx: CanvasRenderingContext2D, ancho: number, alto: number, fuerza: number, rnd: () => number) {
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
  // Ladrillo arena y desaturado, como el de ref-08: el rojo chocaba con el verde oliva (critico-diseno).
  color.ctx.fillStyle = '#3f3b35'; // llaga (mortero)
  color.ctx.fillRect(0, 0, W, H);
  alt.ctx.fillStyle = 'rgb(70 70 70)';
  alt.ctx.fillRect(0, 0, W, H);
  const fila = 64;
  const ancho = 210;
  for (let y = 0; y < H; y += fila) {
    const desfase = (y / fila) % 2 === 0 ? 0 : ancho / 2;
    for (let x = -ancho; x < W + ancho; x += ancho) {
      // ~35 % menos saturación (critico-diseno, 3.ª revisión): con la luz cálida de A el ladrillo salía naranja
      // y el póster, que sale de B, lo enseña gris.
      const r = 112 + rnd() * 15;
      const g = 107 + rnd() * 12;
      const b = 98 + rnd() * 10;
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
  color.ctx.fillStyle = '#3a3c3f';
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

/** Contrachapado de abedul claro: tablero de banco y baldas de exposición (sustituye al nogal barnizado). */
export function texturaContrachapado() {
  const rnd = azar(37);
  const { canvas, ctx } = lienzo(1024, 512);
  ctx.fillStyle = '#b99a6c';
  ctx.fillRect(0, 0, 1024, 512);
  for (let k = 0; k < 160; k++) {
    const y = rnd() * 512;
    const t = 150 + rnd() * 40;
    ctx.strokeStyle = `rgb(${t} ${t * 0.8} ${t * 0.55} / ${0.12 + rnd() * 0.22})`;
    ctx.lineWidth = 0.6 + rnd() * 2.2;
    ctx.beginPath();
    ctx.moveTo(0, y);
    for (let x = 0; x <= 1024; x += 48) ctx.lineTo(x, y + Math.sin(x / (110 + rnd() * 80)) * 5 + (rnd() - 0.5) * 2);
    ctx.stroke();
  }
  // Un par de nudos claros y alguna veta oscura: el abedul de un taller no es una lámina lisa.
  for (let k = 0; k < 5; k++) {
    ctx.fillStyle = 'rgb(120 84 48 / 0.18)';
    ctx.beginPath();
    ctx.ellipse(rnd() * 1024, rnd() * 512, 12 + rnd() * 18, 4 + rnd() * 6, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  grano(ctx, 1024, 512, 16, rnd);
  return textura(canvas);
}

export function texturaCorcho() {
  const rnd = azar(41);
  // 1024 px y granos de 2–7 px: a 1440 px el corcho se lee como corcho y no como una pasta naranja lisa.
  const { canvas, ctx } = lienzo(1024, 1024);
  ctx.fillStyle = '#7a5a3a';
  ctx.fillRect(0, 0, 1024, 1024);
  for (let k = 0; k < 14000; k++) {
    const g = rnd();
    ctx.fillStyle = g > 0.55 ? 'rgb(160 124 84 / 0.65)' : g > 0.2 ? 'rgb(62 44 28 / 0.7)' : 'rgb(104 78 50 / 0.6)';
    ctx.fillRect(rnd() * 1024, rnd() * 1024, 2 + rnd() * 5, 2 + rnd() * 5);
  }
  return textura(canvas, [2, 2]);
}

/**
 * Hueco de una ranura del armero, dibujado como en un plano: contorno discontinuo de la caja máxima de la réplica
 * y marcas de nivel arriba y abajo. Es el «aquí irá una réplica» de la sala sin siluetas de relleno (Javi,
 * 22-11-2026): lo grabado se apaga cuando el socket recibe su imagen real, que se pinta encima.
 */
export function texturaHuecoArmero() {
  const [W, H] = [128, 640];
  const { canvas, ctx } = lienzo(W, H);
  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = colors['trazo-fuerte'];
  // Tenue (20–30 %): reserva el hueco sin competir con los rótulos; a plena fuerza parecía una estantería con fallo de luz.
  ctx.globalAlpha = 0.28;
  ctx.lineWidth = 3;
  ctx.setLineDash([16, 12]);
  ctx.strokeRect(10, 10, W - 20, H - 20);
  ctx.setLineDash([]);
  ctx.strokeStyle = colors.cota;
  ctx.lineWidth = 4;
  for (const y of [10, H - 10]) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.moveTo(W / 2, 40);
  ctx.lineTo(W / 2, H - 40);
  ctx.stroke();
  for (const y of [40, H - 40]) {
    ctx.beginPath();
    ctx.moveTo(W / 2 - 14, y);
    ctx.lineTo(W / 2 + 14, y);
    ctx.stroke();
  }
  return textura(canvas);
}

/**
 * Tapete de corte del banco: lámina azul pizarra con retícula de 10 mm y regla en milímetros en el borde
 * (docs/03 §3.3: el banco mide de verdad). Los colores son los tokens del plano de cotas.
 */
export function texturaTapete() {
  const { canvas, ctx } = lienzo(1536, 672);
  ctx.fillStyle = colors.carbon;
  ctx.fillRect(0, 0, 1536, 672);
  // 1536 px = 1,5 m: 1 px ≈ 1 mm. Retícula fina cada 10 mm y gruesa cada 50 mm.
  for (let x = 0; x <= 1536; x += 10) {
    ctx.strokeStyle = x % 50 === 0 ? 'rgb(156 195 208 / 0.34)' : 'rgb(156 195 208 / 0.13)';
    ctx.lineWidth = x % 50 === 0 ? 1.6 : 1;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 672);
    ctx.stroke();
  }
  for (let y = 0; y <= 672; y += 10) {
    ctx.strokeStyle = y % 50 === 0 ? 'rgb(156 195 208 / 0.34)' : 'rgb(156 195 208 / 0.13)';
    ctx.lineWidth = y % 50 === 0 ? 1.6 : 1;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(1536, y);
    ctx.stroke();
  }
  // Regla en el borde superior, con cifras cada 100 mm.
  ctx.fillStyle = colors.cota;
  ctx.font = `500 15px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'left';
  for (let x = 0; x <= 1536; x += 10) ctx.fillRect(x, 0, 1.4, x % 100 === 0 ? 24 : x % 50 === 0 ? 15 : 8);
  for (let x = 100; x < 1500; x += 100) ctx.fillText(String(x / 10), x + 4, 40);
  // Marcas de registro en las esquinas.
  ctx.strokeStyle = colors.cota;
  ctx.lineWidth = 3;
  for (const [x, y, dx, dy] of [
    [16, 64, 1, 1],
    [1520, 656, -1, -1],
  ] as const) {
    ctx.beginPath();
    ctx.moveTo(x, y + dy * 36);
    ctx.lineTo(x, y);
    ctx.lineTo(x + dx * 36, y);
    ctx.stroke();
  }
  grano(ctx, 1536, 672, 9, azar(53));
  return textura(canvas);
}

/** Tira de ranuras numeradas del armero, como las etiquetas de ref-08 pero en papel de plano. */
export function texturaTiraNumerada(desde: number, cuantos: number) {
  // Misma proporción que la placa de la sala (2,5 m × 0,066 m): antes el lienzo era 16:1 y la placa 50:1, y las
  // cifras salían aplastadas y de 6 px a 1440 px (critico-diseno, 24-11-2026).
  const [W, H] = [3072, 81];
  const { canvas, ctx } = lienzo(W, H);
  ctx.fillStyle = colors.papel;
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = colors['tinta-papel'];
  ctx.font = `700 56px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const paso = W / cuantos;
  for (let i = 0; i < cuantos; i++) {
    ctx.fillText(String(desde + i).padStart(2, '0'), paso * (i + 0.5), 46);
    ctx.fillRect(paso * i, 0, 4, H);
    // Marcas de cota en el borde superior de cada ranura.
    for (let t = 1; t < 5; t++) ctx.fillRect(paso * i + (paso * t) / 5, 0, 3, t === 2 ? 14 : 8);
  }
  grano(ctx, W, H, 12, azar(61));
  return textura(canvas);
}

export interface OpcionesRotulo {
  readonly ancho?: number;
  readonly alto?: number;
  /** Cota bajo el título (p. ej. «2 700 mm»): una línea de cota con sus topes y la medida en el centro. */
  readonly cota?: string;
  /** Tamaño relativo del título (1 = el de las placas de zona). */
  readonly escala?: number;
}

/** Marca de registro: una L de esquina, como las de las placas del sistema (ADR-0010). */
function marcaRegistro(ctx: CanvasRenderingContext2D, x: number, y: number, dx: 1 | -1, dy: 1 | -1, largo: number) {
  ctx.beginPath();
  ctx.moveTo(x, y + dy * largo);
  ctx.lineTo(x, y);
  ctx.lineTo(x + dx * largo, y);
  ctx.stroke();
}

/**
 * Rótulo de la sala en «Plano de cotas» (ADR-0010): lámina azul pizarra, marco de trazo, marcas de registro
 * arriba a la izquierda y abajo a la derecha, título en Plex Sans Condensed y una línea de cota con su medida en
 * Plex Mono. Devuelve el mapa de color (la chapa entera) y un mapa de emisión aparte: al encender el tubo solo
 * luce lo grabado (título, cota y marcas) y la lámina sigue oscura, como un rótulo retroiluminado de verdad.
 */
export function texturaRotulo(texto: string, opciones: OpcionesRotulo = {}) {
  const ancho = opciones.ancho ?? 1024;
  const alto = opciones.alto ?? 256;
  const dibujar = (emision: boolean) => {
    const { canvas, ctx } = lienzo(ancho, alto);
    ctx.fillStyle = emision ? '#000000' : colors.carbon;
    ctx.fillRect(0, 0, ancho, alto);
    const m = Math.round(alto * 0.06);
    if (!emision) {
      ctx.strokeStyle = colors.acero;
      ctx.lineWidth = Math.max(3, alto * 0.018);
      ctx.strokeRect(m, m, ancho - 2 * m, alto - 2 * m);
    }
    ctx.strokeStyle = colors.cota;
    ctx.lineWidth = Math.max(4, alto * 0.026);
    marcaRegistro(ctx, m * 1.7, m * 1.7, 1, 1, alto * 0.14);
    marcaRegistro(ctx, ancho - m * 1.7, alto - m * 1.7, -1, -1, alto * 0.14);
    const escala = opciones.escala ?? 1;
    const tam = Math.round(alto * (opciones.cota ? 0.4 : 0.52) * escala);
    ctx.fillStyle = colors.hueso;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = `700 ${tam}px ${FONT_FAMILIES.rotulo}`;
    ctx.letterSpacing = `${Math.round(tam * 0.05)}px`;
    ctx.fillText(texto.toUpperCase(), ancho / 2, opciones.cota ? alto * 0.38 : alto / 2, ancho - m * 6);
    ctx.letterSpacing = '0px';
    if (opciones.cota) {
      // La cota se lee a 1440 px: ~0,25 del alto de la lámina, en peso 600 y con el trazo más grueso.
      const y = alto * 0.79;
      const x0 = m * 3.4;
      const x1 = ancho - m * 3.4;
      ctx.strokeStyle = colors.cota;
      ctx.lineWidth = Math.max(3.5, alto * 0.026);
      ctx.font = `700 ${Math.round(alto * 0.3)}px ${FONT_FAMILIES.datos}`;
      const medida = ctx.measureText(opciones.cota).width;
      const mitad = medida / 2 + alto * 0.07;
      for (const [a, b] of [
        [x0, ancho / 2 - mitad],
        [ancho / 2 + mitad, x1],
      ] as const) {
        ctx.beginPath();
        ctx.moveTo(a, y);
        ctx.lineTo(b, y);
        ctx.stroke();
      }
      for (const x of [x0, x1]) {
        ctx.beginPath();
        ctx.moveTo(x, y - alto * 0.09);
        ctx.lineTo(x, y + alto * 0.09);
        ctx.stroke();
      }
      ctx.fillStyle = colors.cota;
      ctx.fillText(opciones.cota, ancho / 2, y + 2);
    }
    if (!emision) grano(ctx, ancho, alto, 7, azar(texto.length * 97));
    return textura(canvas);
  };
  return { mapa: dibujar(false), emision: dibujar(true) };
}

/**
 * Pantalla del tablón: solo la maqueta de la interfaz (cabecera y filas vacías). Sin cifras: un precio horneado en
 * una imagen no tendría fecha de comprobación ni se actualizaría (principio 2); el dato vivo va en HTML.
 */
export function texturaPantalla() {
  const { canvas, ctx } = lienzo(640, 400);
  ctx.fillStyle = colors['negro-pavonado'];
  ctx.fillRect(0, 0, 640, 400);
  ctx.strokeStyle = colors.acero;
  ctx.lineWidth = 3;
  ctx.strokeRect(8, 8, 624, 384);
  ctx.fillStyle = colors.cota;
  ctx.font = `500 28px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'left';
  ctx.fillText('BAJADAS', 28, 52);
  ctx.fillRect(28, 66, 120, 3);
  for (let i = 0; i < 3; i++) {
    const y = 110 + i * 88;
    ctx.fillStyle = colors.acero;
    ctx.fillRect(28, y, 330 - i * 40, 16);
    ctx.fillStyle = colors['trazo-fuerte'];
    ctx.fillRect(28, y + 30, 190 - i * 20, 9);
    ctx.fillStyle = colors.acero;
    ctx.fillRect(470, y, 140, 16);
  }
  return textura(canvas);
}

/** Diana de papel: hoja blanca con círculos concéntricos y varios impactos de bola (agujeros suaves). */
export function texturaDiana(semilla = 5) {
  const rnd = azar(semilla);
  const { canvas, ctx } = lienzo(512, 640);
  ctx.fillStyle = colors.papel;
  ctx.fillRect(0, 0, 512, 640);
  ctx.strokeStyle = colors['tinta-papel'];
  ctx.fillStyle = colors['tinta-papel'];
  const cx = 256;
  const cy = 300;
  for (let r = 40; r <= 220; r += 36) {
    ctx.lineWidth = r === 40 ? 9 : 6;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.arc(cx, cy, 20, 0, Math.PI * 2);
  ctx.fill();
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(cx - 236, cy);
  ctx.lineTo(cx + 236, cy);
  ctx.moveTo(cx, cy - 236);
  ctx.lineTo(cx, cy + 236);
  ctx.stroke();
  // Impactos: más agrupados cerca del centro.
  for (let k = 0; k < 13; k++) {
    const ang = rnd() * Math.PI * 2;
    const d = Math.abs(rnd() + rnd() - 1) * 190;
    ctx.fillStyle = 'rgb(20 24 28 / 0.88)';
    ctx.beginPath();
    ctx.arc(cx + Math.cos(ang) * d, cy + Math.sin(ang) * d, 9, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = colors['tinta-papel'];
  ctx.font = `500 22px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'center';
  ctx.fillText('DIANA · 10 m', 256, 590);
  grano(ctx, 512, 640, 10, rnd);
  return textura(canvas);
}

/**
 * Plano enmarcado: la elevación del compactus (2 700 × 2 720 mm, de MUEBLE) con sus divisiones y cotas en
 * milímetros, sobre papel. Es un plano de verdad de la estantería de la sala, no un dibujo de relleno.
 */
export function texturaPlano(ancho_mm: number, alto_mm: number, titulo: string) {
  const { canvas, ctx } = lienzo(768, 576);
  ctx.fillStyle = colors.papel;
  ctx.fillRect(0, 0, 768, 576);
  const tinta = colors['tinta-papel'];
  ctx.strokeStyle = tinta;
  ctx.fillStyle = tinta;
  // Cajetín.
  ctx.lineWidth = 6;
  ctx.strokeRect(20, 20, 728, 536);
  ctx.strokeRect(20, 486, 728, 70);
  ctx.font = `700 38px ${FONT_FAMILIES.rotulo}`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(titulo.toUpperCase(), 40, 514);
  ctx.font = `500 20px ${FONT_FAMILIES.datos}`;
  ctx.fillText('ESC. 1:20 · MEDIDAS EN mm', 40, 540);
  // Alzado a escala (1:20 → cabe en 520 × 400 px).
  const k = Math.min(520 / ancho_mm, 400 / alto_mm);
  const w = ancho_mm * k;
  const h = alto_mm * k;
  const x0 = (768 - w) / 2;
  const y0 = 50 + (420 - h) / 2;
  ctx.lineWidth = 7;
  ctx.strokeRect(x0, y0, w, h);
  ctx.lineWidth = 4.5;
  // Balda media y zócalo, a su altura real.
  for (const frac of [0.047, 0.529]) {
    ctx.beginPath();
    ctx.moveTo(x0, y0 + h * (1 - frac));
    ctx.lineTo(x0 + w, y0 + h * (1 - frac));
    ctx.stroke();
  }
  // Cotas.
  ctx.lineWidth = 3.4;
  ctx.font = `600 26px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'center';
  const yc = y0 + h + 22;
  ctx.beginPath();
  ctx.moveTo(x0, yc);
  ctx.lineTo(x0 + w, yc);
  for (const x of [x0, x0 + w]) {
    ctx.moveTo(x, y0 + h + 4);
    ctx.lineTo(x, yc + 8);
  }
  ctx.stroke();
  ctx.fillStyle = colors.papel;
  ctx.fillRect(768 / 2 - 52, yc - 12, 104, 24);
  ctx.fillStyle = tinta;
  ctx.fillText(`${ancho_mm.toLocaleString('es-ES')} mm`.replace('.', ' '), 768 / 2, yc);
  ctx.save();
  ctx.translate(x0 - 24, y0 + h / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.beginPath();
  ctx.moveTo(-h / 2, 0);
  ctx.lineTo(h / 2, 0);
  ctx.moveTo(-h / 2, -8);
  ctx.lineTo(-h / 2, 8);
  ctx.moveTo(h / 2, -8);
  ctx.lineTo(h / 2, 8);
  ctx.stroke();
  ctx.fillStyle = colors.papel;
  ctx.fillRect(-52, -12, 104, 24);
  ctx.fillStyle = tinta;
  ctx.fillText(`${alto_mm.toLocaleString('es-ES')} mm`.replace('.', ' '), 0, 0);
  ctx.restore();
  grano(ctx, 768, 576, 9, azar(ancho_mm));
  return textura(canvas);
}

/** Etiqueta de caja o maletín: papel con código y medida en Plex Mono, como las de un almacén ordenado. */
export function texturaEtiqueta(codigo: string, linea2: string, papelHex: string = colors.papel) {
  const { canvas, ctx } = lienzo(512, 256);
  ctx.fillStyle = papelHex;
  ctx.fillRect(0, 0, 512, 256);
  ctx.strokeStyle = colors['tinta-papel'];
  ctx.lineWidth = 5;
  ctx.strokeRect(10, 10, 492, 236);
  ctx.fillStyle = colors['tinta-papel'];
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.font = `700 78px ${FONT_FAMILIES.datos}`;
  ctx.fillText(codigo, 34, 96);
  ctx.font = `500 40px ${FONT_FAMILIES.datos}`;
  ctx.fillText(linea2, 34, 184);
  // Código de barras sencillo, sin significado.
  const rnd = azar(codigo.length * 31 + linea2.length);
  for (let x = 330; x < 484; x += 6) ctx.fillRect(x, 150, 2 + Math.floor(rnd() * 3), 70);
  grano(ctx, 512, 256, 8, rnd);
  return textura(canvas);
}

/** Panel perforado de herramientas (ref-05): chapa oscura con retícula de agujeros. */
export function texturaPerforado() {
  const rnd = azar(71);
  const { canvas, ctx } = lienzo(512, 512);
  ctx.fillStyle = '#44606f';
  ctx.fillRect(0, 0, 512, 512);
  for (let y = 16; y < 512; y += 32) {
    for (let x = 16; x < 512; x += 32) {
      ctx.fillStyle = '#05080a';
      ctx.beginPath();
      ctx.arc(x, y, 5.6, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'rgb(156 195 208 / 0.14)';
      ctx.beginPath();
      ctx.arc(x - 1.2, y - 1.4, 5.8, Math.PI * 0.95, Math.PI * 1.7);
      ctx.fill();
    }
  }
  grano(ctx, 512, 512, 12, rnd);
  return textura(canvas, [3, 2]);
}

/** Tela técnica (chaleco, funda): tejido con trama fina y pequeñas irregularidades; el color lo da el material. */
export function texturaTela(base: string) {
  const rnd = azar(83);
  const { canvas, ctx } = lienzo(256, 256);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, 256, 256);
  for (let y = 0; y < 256; y += 3) {
    ctx.fillStyle = `rgb(0 0 0 / ${0.1 + rnd() * 0.08})`;
    ctx.fillRect(0, y, 256, 1);
  }
  for (let x = 0; x < 256; x += 3) {
    ctx.fillStyle = `rgb(255 255 255 / ${0.03 + rnd() * 0.04})`;
    ctx.fillRect(x, 0, 1, 256);
  }
  grano(ctx, 256, 256, 22, rnd);
  return textura(canvas, [2, 2]);
}

/** Señal de protección ocular obligatoria (ISO 7010 M004): círculo azul con unas gafas, sobre la pared. */
export function texturaSenalOjos() {
  const { canvas, ctx } = lienzo(512, 512);
  ctx.fillStyle = '#e9e6de';
  ctx.fillRect(0, 0, 512, 512);
  ctx.fillStyle = '#1f5fa8';
  ctx.beginPath();
  ctx.arc(256, 256, 220, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#f4f2ec';
  // Montura: dos lentes y puente, con patillas.
  for (const x of [196, 316]) {
    ctx.beginPath();
    ctx.ellipse(x, 256, 62, 44, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1f5fa8';
    ctx.beginPath();
    ctx.ellipse(x, 256, 46, 30, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#f4f2ec';
  }
  ctx.fillRect(244, 246, 24, 14);
  ctx.fillRect(96, 244, 44, 14);
  ctx.fillRect(372, 244, 44, 14);
  grano(ctx, 512, 512, 12, azar(91));
  return textura(canvas);
}

/** Regla vertical de papel con marcas cada 10 mm y cifras cada 100 mm (1 px ≈ 1 mm). Plano de cotas en la propia sala. */
export function texturaRegla(alto_mm: number) {
  const ancho = 96;
  const { canvas, ctx } = lienzo(ancho, alto_mm);
  ctx.fillStyle = colors.papel;
  ctx.fillRect(0, 0, ancho, alto_mm);
  ctx.fillStyle = colors['tinta-papel'];
  ctx.font = `600 22px ${FONT_FAMILIES.datos}`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  for (let mm = 0; mm <= alto_mm; mm += 10) {
    const y = alto_mm - mm;
    const largo = mm % 100 === 0 ? 46 : mm % 50 === 0 ? 32 : 18;
    ctx.fillRect(ancho - largo, y - 1, largo, 2.4);
    if (mm % 100 === 0 && mm > 0 && mm < alto_mm - 20) ctx.fillText(String(mm / 10), 6, y);
  }
  grano(ctx, ancho, alto_mm, 9, azar(alto_mm));
  return textura(canvas);
}

/** Tablero de banco: nogal oscuro con veta marcada y juntas de tablas (se ve el material, no un color liso). */
export function texturaTablero() {
  const rnd = azar(113);
  const { canvas, ctx } = lienzo(1024, 512);
  const tablas = 5;
  for (let t = 0; t < tablas; t++) {
    const y0 = (t * 512) / tablas;
    const tono = 0.82 + rnd() * 0.3;
    ctx.fillStyle = `rgb(${Math.round(98 * tono)} ${Math.round(64 * tono)} ${Math.round(38 * tono)})`;
    ctx.fillRect(0, y0, 1024, 512 / tablas);
    for (let k = 0; k < 46; k++) {
      const y = y0 + rnd() * (512 / tablas);
      ctx.strokeStyle = `rgb(${24 + rnd() * 30} ${14 + rnd() * 18} ${8 + rnd() * 10} / ${0.3 + rnd() * 0.4})`;
      ctx.lineWidth = 0.8 + rnd() * 2.6;
      ctx.beginPath();
      ctx.moveTo(0, y);
      for (let x = 0; x <= 1024; x += 40) ctx.lineTo(x, y + Math.sin(x / (70 + rnd() * 90)) * 4 + (rnd() - 0.5) * 2.4);
      ctx.stroke();
    }
    ctx.fillStyle = 'rgb(8 5 3 / 0.85)';
    ctx.fillRect(0, y0, 1024, 3);
  }
  // Marcas de uso: algún golpe y mancha clara.
  for (let k = 0; k < 24; k++) {
    ctx.fillStyle = `rgb(${140 + rnd() * 50} ${110 + rnd() * 40} ${80 + rnd() * 30} / ${0.07 + rnd() * 0.12})`;
    ctx.beginPath();
    ctx.ellipse(rnd() * 1024, rnd() * 512, 6 + rnd() * 26, 3 + rnd() * 9, rnd() * 3, 0, Math.PI * 2);
    ctx.fill();
  }
  grano(ctx, 1024, 512, 18, rnd);
  return textura(canvas);
}
