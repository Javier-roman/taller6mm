---
paths:
  - "apps/pipeline/**"
  - "assets-src/**"
---

# Reglas de assets
Lee `docs/05-assets-y-fidelidad.md`.

- Puerta de licencias: nada se publica sin un `license_status` publicable y su procedencia registrada.
- Las fotos de terceros son solo referencia interna: nunca se publican ni se proyectan en texturas. Las imágenes de fuentes con opt-out de TDM o de IA ni siquiera se procesan.
- Las texturas salen solo de la biblioteca de materiales PBR propia. Sin logos ni marcajes sin permiso de la marca.
- Las piezas estándar (raíles, roscas, tubos) se generan de forma paramétrica, con medidas exactas.
- Convenciones: mm en los datos, metros en la escena, ejes canónicos, sockets `socket.<ranura>`, LODs y presupuestos de peso.
- Modelos de IA solo con licencia comercial compatible con la UE (ver `apps/pipeline/MODELOS.md`).
- Cada asset pasa la validación automática (cotas + silueta) y el subagente `revisor-fidelidad` antes de publicarse.
