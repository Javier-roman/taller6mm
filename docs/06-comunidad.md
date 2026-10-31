# 06 · Comunidad (la Vitrina)

## 1. Builds públicas
- Se publican desde el Banco con:
  - título y descripción;
  - etiquetas de uso: CQB, bosque, milsim, francotirador, speedsoft o colección;
  - presupuesto y nivel (novato o avanzado).
- Visibilidad: privada, por enlace o pública.
- **Foto real** opcional: fotos de la build montada de verdad, con insignia "Foto real", crédito y licencia según los términos.
- La página de una build incluye:
  - render y modo foto;
  - lista de piezas con sus ofertas;
  - compatibilidad y coste total;
  - autor y versiones;
  - "Duplicar y modificar" (fork con atribución);
  - comentarios;
  - compartir (Open Graph generado y código `T6M-…`).

## 2. Interacciones
Me gusta · favoritos (colecciones con nombre, públicas o privadas) · comentarios (un nivel de respuesta, con menciones) · seguir a usuarios · denunciar.

## 3. Rankings (secciones de la Vitrina)
| Ranking | Fórmula |
|---|---|
| Tendencia | `(likes + 1,5·favs + 2·comentarios + 0,05·vistas_únicas) / (horas + 2)^1,5` |
| Top semana / mes / siempre | Suma ponderada de interacciones dentro de la ventana |
| Más vistos | Vistas únicas (deduplicadas cada 24 h) por ventana |
| Más populares | likes + favs |
| Mejor valorados | Media bayesiana `(C·m + Σ notas) / (C + n)`, con m = media global y C = 10 |
| Build del mes | Selección del equipo + votación de la comunidad |

- Filtros por plataforma, presupuesto y estilo.
- Recalculados por cron en tablas materializadas: tendencia cada 15 min y el resto a diario.

### Antimanipulación
- Un voto por cuenta y sin autovotos.
- Las cuentas con menos de 24 h o sin email verificado no cuentan para los rankings.
- Límites de ritmo.
- Detección de anillos de votos: mismos hashes de IP o dispositivo y patrones temporales.
- Vistas deduplicadas con un hash diario rotatorio de IP + navegador, sin guardar IPs.

## 4. Reseñas y opiniones
- **De productos**: nota de 1 a 5, pros, contras, texto, tiempo de uso y "Lo tengo" (con foto opcional, que da insignia). Se ordenan por utilidad (límite inferior de Wilson de los votos útiles).
- **De tiendas**: envío, atención, embalaje y precio. La tienda puede responder en público (programa de tiendas).
- **Informes de compatibilidad**: "Lo he montado: encaja / con adaptador / con modificación / no encaja", con nota y foto. Alimentan el motor (docs/03, regla 6) ponderados por reputación.

## 5. Perfiles y reputación
- **Perfil**: apodo, avatar, bio, provincia (opcional), equipo o club (opcional), builds, colecciones, reseñas e insignias.
- **Reputación** por aportaciones útiles: builds con me gusta, reseñas útiles, informes de compatibilidad confirmados, escaneos aprobados y datos de catálogo aceptados.
- **Rangos**: Recluta → Tirador → Armero → Maestro armero → Leyenda del taller.
- **Insignias**: primera build, fotógrafo (escaneo aprobado), verificador (10 informes confirmados), etc.
- La reputación desbloquea permisos: proponer correcciones de catálogo y moderación comunitaria ligera.

## 6. Notificaciones
En la Taquilla, y también por email o push según preferencias:
- respuestas;
- me gusta (agrupados);
- nuevos seguidores;
- alertas de mercado;
- cambios en builds favoritas (una pieza agotada o más barata).

## 7. Moderación (y DSA, ver docs/09)
### Normas de comunidad
- Respeto: nada de odio, acoso ni doxxing.
- **Solo airsoft**: nada de armas de fuego reales ni de modificaciones ilegales.
- Imágenes propias.
- Sin compraventa entre particulares, por ahora.
- Sin spam ni enlaces de afiliación de usuarios.

### Herramientas
- Botón de denunciar con motivos y cola de moderación en la Trastienda.
- Automoderación de texto e imágenes con un clasificador barato y revisión humana.
- Turnstile en altas y en publicaciones de cuentas nuevas.
- Límites de ritmo y restricciones progresivas.

### Garantías
Cada decisión genera una **declaración de motivos** para el afectado, que puede recurrirla. Todas las acciones quedan registradas.

## 8. Privacidad en la comunidad
- Perfiles públicos con datos mínimos; la ubicación es opcional y solo a nivel de provincia.
- Se eliminan los metadatos EXIF y GPS de toda foto.
- Exportar y borrar la cuenta desde la Taquilla.

## Criterios de aceptación (Fase 5)
- [ ] Publicar, ver, dar me gusta, guardar en colección, comentar y duplicar una build.
- [ ] Rankings calculados por cron, con tests de las fórmulas y de la antimanipulación.
- [ ] Reseñas de producto y de tienda, e informes de compatibilidad conectados al motor.
- [ ] Flujo completo de denuncia → decisión → declaración de motivos → recurso.
- [ ] Contadores sin escribir una fila por visita (Durable Objects con volcado periódico).
