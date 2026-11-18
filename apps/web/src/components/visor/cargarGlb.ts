// Carga de un GLB del visor (GLTFLoader + decodificador Meshopt de three). Se importa con `import()` desde
// el visor para que three entre en su propio trozo y la ficha se pinte antes. El decodificador Meshopt es
// WebAssembly: por eso /visor-prueba (y solo esa ruta) añade `'wasm-unsafe-eval'` a su CSP.
import { Box3, type Mesh, type Object3D, Vector3 } from 'three';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export interface ModeloCargado {
  objeto: Object3D;
  /** Caja de la geometría en mm (X largo, Y alto, Z ancho; docs/05 §4). Es la de la malla T0, no una cota de SKU. */
  caja: { largo: number; alto: number; ancho: number };
  /** Piezas con malla (los marcadores sin modelo llevan la malla del marcador). */
  mallas: number;
}

export async function cargarGlb(url: string): Promise<ModeloCargado> {
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const gltf = await loader.loadAsync(url);
  const objeto = gltf.scene;
  const t = new Box3().setFromObject(objeto).getSize(new Vector3());
  let mallas = 0;
  objeto.traverse((o) => {
    if ((o as Mesh).isMesh) mallas += 1;
  });
  return { objeto, caja: { largo: t.x * 1000, alto: t.y * 1000, ancho: t.z * 1000 }, mallas };
}

/** Libera la memoria de GPU de un modelo que ya no se muestra. */
export function liberarModelo(objeto: Object3D): void {
  objeto.traverse((o) => {
    const m = o as Mesh;
    if (!m.isMesh) return;
    m.geometry.dispose();
    for (const mat of Array.isArray(m.material) ? m.material : [m.material]) mat.dispose();
  });
}
