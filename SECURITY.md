# Política de seguridad de Taller6mm

Gracias por ayudar a que Taller6mm sea seguro. Este documento explica cómo avisarnos de una vulnerabilidad y qué puedes esperar de nosotros. También está en `/.well-known/security.txt` (RFC 9116).

## Cómo avisar
Usa los **avisos privados de seguridad de GitHub**: [Report a vulnerability](https://github.com/Javier-roman/taller6mm/security/advisories/new). El aviso solo lo ve el equipo del proyecto y no hace falta exponer ningún email.

No abras un issue público ni publiques el fallo hasta que esté corregido.

Incluye, si puedes:
- qué componente afecta (web, worker `jobs`, rastreador, pipeline de assets, CI) y la URL o el archivo;
- los pasos para reproducirlo y el impacto que ves;
- si has accedido a datos de otras personas (no deberías: ver «Reglas»).

Idiomas: español o inglés.

## Qué puedes esperar
| Paso | Plazo objetivo |
|---|---|
| Acuse de recibo | 3 días laborables |
| Primera valoración (severidad y si lo reproducimos) | 10 días laborables |
| Corrección de un fallo crítico o alto | 30 días |
| Publicación coordinada del aviso | Cuando esté corregido, con tu crédito si lo quieres |

Es un proyecto personal sin programa de recompensas: no hay pagos por los avisos.

## Alcance
**Dentro**:
- el código de este repositorio;
- los despliegues de Taller6mm en Cloudflare (web, previews y worker `jobs`);
- la configuración del CI y la cadena de suministro (dependencias, acciones y scripts).

**Fuera**:
- las tiendas y marcas enlazadas desde la web;
- denegaciones de servicio y pruebas de carga;
- ingeniería social y ataques físicos;
- informes automáticos sin una prueba de impacto (por ejemplo, cabeceras «que faltan» sin un ataque concreto).

## Reglas (puerto seguro)
Si actúas de buena fe y dentro de estas reglas, no emprenderemos acciones contra ti:
- usa solo cuentas propias o de prueba y no accedas, modifiques ni borres datos de otras personas;
- para en cuanto demuestres el fallo y no lo explotes más de lo necesario;
- no degrades el servicio (nada de pruebas de volumen ni de fuerza bruta);
- danos un plazo razonable antes de hacerlo público.

## Versiones soportadas
Solo la rama `main` y lo desplegado desde ella. Las ramas `spike/*` son prototipos desechables y nunca se despliegan en producción.
