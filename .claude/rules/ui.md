---
paths:
  - "apps/web/src/**"
  - "packages/ui/**"
---

# Reglas de interfaz
Lee `docs/02-experiencia-y-diseno.md` antes de diseñar.

- Solo tokens de `packages/ui` para color, tipografía, espaciado, radios, sombras, duraciones y curvas. Ningún valor suelto.
- Componentes accesibles: HTML semántico, foco visible, objetivos de 44 px o más, `aria-*` correcto y contraste AA.
- Todo movimiento respeta `prefers-reduced-motion`. Todo el 3D tiene una alternativa ligera y una navegación HTML equivalente.
- Islas React solo donde haya interactividad. Prioriza `client:visible` o `client:idle` sobre `client:load`. El 3D va con `client:only="react"` y carga diferida.
- Textos de interfaz en español de España, con tono experto y cercano y vocabulario de airsoft correcto (glosario en `docs/00-INDICE.md`).
- Precios siempre con su fecha de comprobación, stock con su estado y assets con su nivel de fidelidad.
- Verifica el resultado en el navegador (Playwright) antes de darlo por terminado.
