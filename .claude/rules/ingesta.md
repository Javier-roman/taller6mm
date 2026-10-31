---
paths:
  - "apps/crawler/**"
  - "apps/jobs/src/ingest/**"
  - "packages/market/**"
---

# Reglas de ingesta (obligatorias)
Lee `docs/04-mercado-e-ingesta.md` antes de cambiar nada aquí.

- Todo acceso a una tienda pasa por el cliente HTTP común, que respeta robots.txt y `Content-Signal`, el ritmo, el User-Agent, la caché condicional, el backoff y el circuito. Prohibido hacer `fetch` directo a una tienda.
- Desarrollo y tests solo contra fixtures. Cualquier ejecución `--live` necesita permiso de Javi.
- Solo se guardan hechos: precio en céntimos, moneda, disponibilidad (enum común), URL, identificadores y título normalizado.
- De las imágenes ajenas solo se guarda la URL como metadato, salvo que la `image_policy` de la fuente registre un permiso.
- El clasificador de exclusión está siempre activo: armas de fuego reales, munición, piezas reguladas y cuchillería.
- En D1 solo se escriben cambios (eventos de precio y stock), en lotes.
- Una tienda `opted_out` no se vuelve a tocar, y sus datos se borran según la política.
