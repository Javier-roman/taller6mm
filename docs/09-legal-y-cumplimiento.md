# 09 · Legal y cumplimiento

> Esto no es asesoramiento jurídico. Es el mapa de obligaciones que el producto debe implementar y de lo que hay que validar con un abogado antes de lanzar (sobre todo §5 y §6). Fecha de revisión: 31-10-2026.

## 1. Protección de datos (RGPD + LOPDGDD)
- Base jurídica por finalidad: la cuenta, por contrato; las alertas, por consentimiento; la seguridad, por interés legítimo.
- Información clara (arts. 13 y 14 RGPD) y derechos (acceso, rectificación, supresión, portabilidad) implementados como funciones de la Taquilla.
- Edad mínima para crear cuenta: en España, 14 años para consentir (art. 7 LOPDGDD). Decidir si el servicio exige 18 años por su temática.
- Encargados del tratamiento (Cloudflare, Resend, Sentry, GitHub): contratos de encargo y marcos de transferencias internacionales, a verificar.
- Registro de actividades de tratamiento y análisis de riesgos. Brechas: notificación a la AEPD en 72 h cuando proceda.
- Fuentes tipográficas autoalojadas, para no transferir IPs a terceros sin necesidad.

## 2. Servicios de la sociedad de la información (LSSI-CE)
- Aviso legal con los datos del titular: identidad, NIF y contacto.
- Comunicaciones comerciales identificables: los enlaces de afiliación y los patrocinios van **etiquetados**.
- Cookies: solo técnicas, así que sin banner. Si algún día se añade algo no esencial, consentimiento previo (art. 22.2).

## 3. Reglamento de Servicios Digitales (DSA, Reglamento (UE) 2022/2065)
Como servicio que aloja contenido de usuarios (builds, comentarios, reseñas, fotos):
- Punto de contacto y términos que expliquen cómo se modera.
- **Mecanismo de notificación y acción** (art. 16), accesible desde cualquier contenido.
- **Declaración de motivos** (art. 17) cada vez que se restringe contenido o una cuenta.
- Comunicación a las autoridades de sospechas de delitos graves que amenacen vidas o la seguridad (art. 18).

Las obligaciones adicionales de las "plataformas en línea" tienen exenciones para micro y pequeñas empresas. Aun así, se implementan desde el inicio por diseño: recurso interno, transparencia básica y publicidad identificada.

## 4. Consumo y publicidad
- Comparador honesto: precio, tienda y fecha de comprobación, con el aviso de que el precio final lo fija la tienda.
- **Parámetros de clasificación** visibles (por qué una oferta sale primero) y resultados patrocinados marcados (Directiva Ómnibus).
- Afiliación declarada en una página propia y junto a los enlaces.

## 5. Propiedad intelectual e industrial
- **Marcas**: nombrar marcas y modelos para identificar productos reales es uso referencial, habitual en los comparadores. Límites: no usar logos como si hubiera asociación, no sugerir patrocinio y no reproducir marcajes en los modelos.
- **Diseños**: la reforma del diseño de la UE (Reglamento (UE) 2024/2822, aplicable desde el 1-5-2025) extiende la protección a los productos digitales y añade una excepción de **uso referencial**. Representar productos reales para identificarlos y compararlos encaja en ese espíritu, pero hay que **validarlo con un abogado**.
- **Derechos de autor**: las fotos, renders y modelos 3D ajenos están protegidos, así que no se publican sin permiso (docs/05). Tampoco se copian los textos de las fichas de las tiendas.
- **Minería de textos y datos (TDM)**: la excepción general (Directiva (UE) 2019/790, art. 4, transpuesta en España) cede ante las reservas expresas legibles por máquina: robots.txt, líneas `Content-Signal` y condiciones de uso. Si hay reserva, no se procesa.
- **Derecho sui generis sobre bases de datos** (Directiva 96/9/CE): no se extraen partes sustanciales del catálogo de una tienda. Tomamos hechos puntuales (precio, stock) y enlazamos.
- **Contenido de usuarios**: licencia no exclusiva y gratuita para mostrar sus fotos, builds y reseñas, revocable con la baja salvo en builds derivadas por terceros.
- **Referencias de videojuegos** (`docs/referencias/`): solo inspiración interna; no se reproduce nada.

## 6. Normativa sobre réplicas (contenido informativo)
- En España, las réplicas de airsoft están en la **4.ª categoría** del Reglamento de Armas (Orden INT/2860/2012) y requieren **tarjeta de armas**, que expide el ayuntamiento. El Tribunal Supremo avaló esa inclusión.
- En 2026, el Ministerio del Interior ha sometido a audiencia pública un proyecto de modificación del Reglamento de Armas, ligado a la Directiva (UE) 2021/555. La página `/guias/normativa` debe llevar fecha de revisión, enlaces al BOE y la revisión de alguien experto.
- La web **no vende** réplicas: informa y enlaza a tiendas.
- **Solo airsoft**: quedan fuera las armas de fuego reales, la munición real, las piezas reguladas de armas de fuego y cualquier contenido sobre modificaciones ilegales. Se aplica en las normas de comunidad y en el filtro de ingesta.

## 7. Fiscalidad y forma jurídica
Los ingresos por afiliación o patrocinio suponen actividad económica. Antes de monetizar, valorar el alta como autónomo o como sociedad y sus obligaciones fiscales.

## 8. Documentos a redactar
Las plantillas se preparan en la Fase 9 y las revisa un abogado:
- Aviso legal.
- Política de privacidad y política de cookies.
- Términos de uso.
- Normas de comunidad.
- Política de moderación y recursos (DSA).
- Página `/bot`: qué rastreamos y cómo excluirse.
- Programa de tiendas.
- Declaración de afiliación.
- Normativa de réplicas: informativa y fechada.

## Criterios de aceptación
- [ ] Todos los documentos publicados y enlazados en el pie de página.
- [ ] Flujo DSA implementado y probado.
- [ ] Política de imágenes por fuente aplicada en el código.
- [ ] Revisión de un abogado sobre §5 y §6 antes del lanzamiento público.
