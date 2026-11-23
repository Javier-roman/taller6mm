// Materiales de la sala. Los colores de marca (papel, kraft, latón, verde ranger…) salen de los tokens de
// @taller6mm/ui; los de materiales físicos (ladrillo, hormigón, plásticos, tela) son de la escena, no de interfaz.
// Los emisivos llevan nombre `emisivo:<grupo>`: Blender los separa por grupo de luz al hornear.
import { colors } from '@taller6mm/ui/tokens';
import { Color, DoubleSide, MeshPhysicalMaterial, MeshStandardMaterial } from 'three';
import {
  texturaContrachapado,
  texturaCorcho,
  texturaHormigon,
  texturaLadrillo,
  texturaPantalla,
  texturaPerforado,
  texturaTablero,
  texturaTapete,
  texturaTela,
} from './texturas.ts';

export const CALIDO = new Color('#ffb46a');

export function crearMateriales() {
  const m = (p: ConstructorParameters<typeof MeshStandardMaterial>[0]) => new MeshStandardMaterial(p);
  // Chapa de compactus: verde oliva tan oscuro que casi es negro (ref-08).
  const verde = new Color(colors['verde-ranger']).multiplyScalar(0.42);
  const ladrillo = texturaLadrillo([7, 3]);
  const hormigon = texturaHormigon([8, 6]);
  const pantalla = texturaPantalla();
  return {
    ladrillo: m({ map: ladrillo.mapa, normalMap: ladrillo.normal, roughness: 0.92 }),
    hormigon: m({ map: hormigon.mapa, normalMap: hormigon.normal, roughness: 0.42, metalness: 0.08 }),
    chapa: m({ color: verde, roughness: 0.32, metalness: 0.55 }),
    // Fondo de los huecos: más oscuro que el atrezo para que este se separe de él (critico-diseno: valores).
    chapaOscura: m({ color: verde.clone().multiplyScalar(0.28), roughness: 0.7, metalness: 0.3 }),
    techo: m({ color: '#121315', roughness: 1 }),
    acero: m({ color: '#2b2f34', roughness: 0.2, metalness: 0.9 }),
    aceroClaro: m({ color: '#9aa3ab', roughness: 0.28, metalness: 0.95 }),
    rail: m({ color: '#8a9097', roughness: 0.14, metalness: 0.95 }),
    polimeroNegro: m({ color: '#17191c', roughness: 0.46 }),
    polimeroFde: m({ color: colors.fde, roughness: 0.7 }),
    polimeroOd: m({ color: colors['verde-ranger'], roughness: 0.7 }),
    maletin: m({ color: '#1b1d20', roughness: 0.28, metalness: 0.15 }),
    // Cartón corrugado y kraft (portaetiquetas de precio, ADR-0010).
    kraft: m({ color: colors.kraft, roughness: 0.92 }),
    cinta: m({ color: '#d8c8a2', roughness: 0.5 }),
    // Contrachapado de abedul claro con un barniz muy suave: baldas, mostrador y tablero del banco.
    contrachapado: new MeshPhysicalMaterial({
      map: texturaContrachapado(),
      roughness: 0.55,
      clearcoat: 0.25,
      clearcoatRoughness: 0.35,
    }),
    // Nogal oscuro con veta para el tablero del banco (el protagonista de la sala).
    tablero: new MeshPhysicalMaterial({
      map: texturaTablero(),
      roughness: 0.5,
      clearcoat: 0.4,
      clearcoatRoughness: 0.3,
    }),
    tapete: m({ map: texturaTapete(), roughness: 0.88 }),
    corcho: m({ map: texturaCorcho(), roughness: 0.95 }),
    papel: m({ color: colors.papel, roughness: 0.85 }),
    tintaPapel: m({ color: colors['tinta-papel'], roughness: 0.8 }),
    laton: m({ color: colors.laton, roughness: 0.2, metalness: 0.95 }),
    vidrio: m({
      color: '#d8e4ea',
      roughness: 0.08,
      metalness: 0,
      transparent: true,
      opacity: 0.05,
      depthWrite: false,
    }),
    // Taquilla en verde ranger gastado (no azul: choca con el oliva de la estantería).
    taquilla: m({ color: '#4a5848', roughness: 0.42, metalness: 0.55 }),
    pantalla: m({
      name: 'emisivo:base',
      map: pantalla,
      emissiveMap: pantalla,
      emissive: '#ffffff',
      emissiveIntensity: 0.9,
    }),
    led: m({ name: 'emisivo:calidas', color: '#fff3e2', emissive: CALIDO, emissiveIntensity: 3, roughness: 0.3 }),
    bombilla: m({
      name: 'emisivo:calidas',
      color: '#fff3e2',
      emissive: CALIDO,
      emissiveIntensity: 8,
      roughness: 0.3,
    }),
    // Tiras LED frías bajo las cabeceras: cada una sigue a los tubos de su estantería (grupo de luz).
    ledIzquierda: m({ name: 'emisivo:tubo-izquierda', color: '#e9eef7', emissive: '#dfe9ff', emissiveIntensity: 1.2 }),
    ledDerecha: m({ name: 'emisivo:tubo-derecha', color: '#e9eef7', emissive: '#dfe9ff', emissiveIntensity: 1.2 }),
    // Atrezo de airsoft (sin réplicas ni armas).
    plasticoBlanco: m({ color: '#d9d6cc', roughness: 0.45 }),
    tapaNaranja: m({ color: '#c4562f', roughness: 0.5 }),
    caucho: m({ color: '#0f1113', roughness: 0.85 }),
    lente: new MeshPhysicalMaterial({
      color: '#243847',
      roughness: 0.06,
      transparent: true,
      opacity: 0.55,
      side: DoubleSide,
    }),
    tela: m({ map: texturaTela('#4a5240'), color: '#ffffff', roughness: 0.95 }),
    telaFde: m({ map: texturaTela('#8d7b5a'), color: '#ffffff', roughness: 0.95 }),
    telaNegra: m({ map: texturaTela('#24282b'), color: '#ffffff', roughness: 0.95 }),
    perforado: m({ map: texturaPerforado(), roughness: 0.55, metalness: 0.5 }),
    marco: m({ color: '#0e1214', roughness: 0.4, metalness: 0.6 }),
    bateria: m({ color: '#2a4a6b', roughness: 0.55 }),
    bombona: m({ color: '#3f6b46', roughness: 0.4, metalness: 0.4 }),
    destornilladorNaranja: m({ color: '#b8582f', roughness: 0.55 }),
    destornilladorOlivo: m({ color: colors['verde-ranger'], roughness: 0.55 }),
  };
}

export type Materiales = ReturnType<typeof crearMateriales>;
