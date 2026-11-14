# Verificación de integridad — 14/11/2026

Informe sobre las versiones consultadas, no una comprobación permanente de la
biblioteca. El [estado del proyecto](../docs/ESTADO_PROYECTO.md) explica cómo se
relaciona esta descarga con el bot y qué queda por automatizar.

## Resultado

Las descargas están completas respecto al contenido publicado en inglés en la
biblioteca oficial para `denizen-deck` y `oath-newfoundations`: **300 registros y
300 imágenes**, sin cartas ausentes, IDs duplicados ni diferencias en los campos
de origen. El juego base y Clockwork quedan fuera de esta comprobación.

| Producto | Registros oficiales | Registros locales | Imágenes locales |
| --- | ---: | ---: | ---: |
| Denizen Pack | 60 | 60 | 60 |
| New Foundations | 240 | 240 | 240 |

## Fuentes contrastadas

- [Catálogo oficial sin comprimir](https://cardcdn.buriedgiant.com/cards.json):
  comprobación independiente del decodificador de `cards.min.json`.
- [Inventario oficial del Denizen Pack](https://github.com/buriedgiantstudios/cards/blob/c9ef9b6f75c4979fad00da31622519556d444ae8/content/card-data/oath/en-US/denizen-deck.yml)
  e [inventario de New Foundations](https://github.com/buriedgiantstudios/cards/blob/c9ef9b6f75c4979fad00da31622519556d444ae8/content/card-data/oath/en-US/oath-newfoundations.yml):
  los conjuntos de IDs coinciden exactamente con ambos JSON locales.
- [Ficha comercial oficial del Denizen Deck](https://buriedgiant.shop/products/oath-denizen-deck):
  anuncia 60 denizens, coherentes con las diez cartas de cada uno de los seis
  palos presentes en la descarga.
- [Repositorio oficial de imágenes](https://github.com/buriedgiantstudios/cards/tree/c9ef9b6f75c4979fad00da31622519556d444ae8/content/card-images/oath/en-US):
  existen archivos PNG originales para las 300 imágenes seleccionadas.

Versión pública del catálogo: `d53a26b7562f40726e916f074ac31675`, coincidente con
el MD5 del archivo `cards.json` descargado. Revisión del repositorio oficial:
`c9ef9b6f75c4979fad00da31622519556d444ae8`.

## Qué representan los 240 registros de New Foundations

Los registros cuentan **caras publicadas**, no necesariamente cartas físicas:

| Contenido | Caras |
| --- | ---: |
| Reliquias, incluido el Gran Cetro | 48 |
| Denizens revisados | 33 |
| Visiones y Conspiración | 5 |
| Legados | 36 |
| Preparación | 19 |
| Sitios | 24 |
| Edificios: 30 intactos y sus 30 ruinas | 60 |
| Crónica | 7 |
| Estandartes | 4 |
| Objetivos del Guardián del Juramento | 4 |
| **Total** | **240** |

El campo `flipSide` identifica 42 parejas de caras: 30 edificios, ocho cartas de
preparación, dos de crónica y dos estandartes. Todas las referencias tienen su
contraparte y son recíprocas. No faltan reversos específicos enlazados por la fuente.

## Comprobaciones realizadas

- El resultado de descomprimir el catálogo coincide con el JSON oficial sin comprimir.
- Los campos originales, incluidos `text`, etiquetas, `meta` y `flipSide`, coinciden
  en las 300 cartas. `description` reproduce el texto original. No hay textos vacíos.
- En la primera auditoría, las 300 conversiones PNG locales se podían abrir y
  coincidían con las dimensiones y los píxeles decodificados de sus WebP en el CDN.
  No había imágenes idénticas asignadas a diferentes IDs dentro de estos productos.
- Las rutas locales existen y cada imagen puede relacionarse con su PNG original
  en el inventario de GitHub. Las traducciones pendientes no se han modificado.

El detalle de esa primera auditoría, anterior a la sustitución de imágenes, está
en [`completeness-audit.json`](completeness-audit.json). Los hashes de los originales
PNG actuales y sus URLs están en [`original-png-audit.json`](original-png-audit.json).

## Calidad de imagen y alcance

Las primeras copias PNG se crearon a partir de los WebP públicos. El
[proceso oficial de conversión](https://github.com/buriedgiantstudios/cards/blob/c9ef9b6f75c4979fad00da31622519556d444ae8/scripts/compress-card-images.ts)
usa WebP con calidad 90; convertir esos WebP a PNG no recupera la información perdida.

Se compararon los PNG originales de *Golem Legions* y *Sticky Fire (NF)*:
tienen la misma resolución que las conversiones (381 × 596 y 381 × 381), pero
diferentes píxeles.

Después de la auditoría, y por solicitud del usuario, **se sustituyeron las 300
conversiones por los PNG originales oficiales**, conservando los nombres locales.
Cada archivo se contrastó con el tamaño y el hash de objeto Git publicados para
esa revisión: los archivos locales son idénticos byte a byte a los originales.
No se convirtieron, recomprimieron ni ampliaron. Ambos `cards.json`, incluidos los
campos de traducción española, se conservaron intactos.

Esta verificación acredita la copia íntegra del catálogo público consultado.
El [contraste posterior con los manuales oficiales](CONTRASTE_CAJA.md) confirma
los recuentos de las categorías de cartas y explica los 33 denizens revisados.
La biblioteca no representa todo el contenido físico: quedan fuera tableros,
título del Guardián, ayudas y otros elementos, incluidos reversos no publicados.
No se ha comparado palabra por palabra el texto de cada carta con una copia
física ni incorporado las cartas base compatibles con New Foundations que se
excluyeron expresamente. Las carpetas de reescalado y referencias auxiliares
no forman parte del conjunto de PNG originales verificado aquí.
