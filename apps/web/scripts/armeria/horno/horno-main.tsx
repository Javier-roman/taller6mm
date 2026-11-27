// Entrada del horno: monta la sala 3D en la página que abren los scripts de horneado. Fuera de la web.
import '@taller6mm/ui/estilos/fuentes.css';
import { createRoot } from 'react-dom/client';
import Horno from '../../../src/components/armeria/horno/Horno.tsx';

const raiz = document.getElementById('raiz');
if (!raiz) throw new Error('Falta #raiz');
createRoot(raiz).render(<Horno />);
