# Fuentes de la propuesta terminológica

Consulta y revisión: **14 de noviembre de 2026**. Los identificadores de esta
tabla se usan en `glossary.csv`. [sources.json](sources.json) conserva URLs,
huellas de los documentos consultados y recuentos de la revisión.

## Criterio de prioridad

Para el **nombre español**, primero se usa el texto legible de componentes de
2Tomatoes. Para el **significado y funcionamiento actuales**, manda el inglés de
New Foundations. Una palabra publicada en la caja base no demuestra que sus
reglas antiguas sigan vigentes ni que un título nuevo esté traducido oficialmente.

El usuario confirma el 14 de noviembre de 2026 que NF aún no ha salido en español
y fija como criterio conservar la traducción oficial de 2Tomatoes para los
términos habituales. Los conceptos nuevos se proponen desde el inglés de NF.

No se ha conseguido consultar un PDF completo del reglamento de 2Tomatoes:
su ficha española devuelve HTTP 403. Para comprobar su vocabulario se utilizan
las fotografías de componentes identificadas a continuación. La ausencia de una
edición española de NF no es una carencia de la búsqueda: su inglés es la
referencia de reglas de esta traducción fan.

## Referencias españolas prioritarias

Las fotos siguientes están publicadas en una [reseña de la edición española de
2Tomatoes](https://misutmeeple.com/2022/12/resena-oath-cronicas-del-imperio-y-del-exilio/).
El autor identifica expresamente que utilizó una copia de esa edición facilitada
por la editorial. Se ha leído el texto impreso de las imágenes, evitando adoptar
automáticamente las paráfrasis de la explicación del reseñador.

| ID | Fuente | Comprobación |
| --- | --- | --- |
| ES-AYUDA | [Tablero y ayuda del Canciller](https://misutmeeple.com/wp-content/uploads/2022/12/oath_detalle_canciller.jpg) | Fases, acciones, sitio, consejeros, tropas, Suministro, reservas, gobernar, bocarriba/bocabajo y verbos operativos. |
| ES-MAPA | [Tapete](https://misutmeeple.com/wp-content/uploads/2022/12/oath_tapete.jpg) | Las tres regiones, los seis palos, mazo del mundo, mazo de reliquias y pilas de descarte. |
| ES-HABITANTES | [Cartas de habitantes](https://misutmeeple.com/wp-content/uploads/2022/12/oath_cartas.jpg) | Voto, Acción, negociar, fuerza de ataque y título Redactora de Documentos. |
| ES-RELIQUIAS | [Cartas de reliquias](https://misutmeeple.com/wp-content/uploads/2022/12/oath_reliquias.jpg) | Gran Cetro, Varillas de Radiestesia, Harpa de la Verdad, Piel de Dragón, revelar, mirar en secreto y exiliar. |
| ES-ESTANDARTES | [Estandartes](https://misutmeeple.com/wp-content/uploads/2022/12/oath_favores_estandartes.jpg) | Favor del Pueblo, Secreto más Oscuro, habitante y reserva común. |
| ES-JURAMENTOS | [Objetivos y título](https://misutmeeple.com/wp-content/uploads/2022/12/oath_juramentos.jpg) | Guardián del Juramento, Sucesor del Canciller y nombres de los cuatro objetivos. |
| ES-VISIONES | [Visiones y Conspiración](https://misutmeeple.com/wp-content/uploads/2022/12/oath_visiones.jpg) | Nombres de Visiones, Cuando es Jugada, quemar, devolver a la caja y Despertar. |
| ES-RESENA | [Texto de la reseña](https://misutmeeple.com/2022/12/resena-oath-cronicas-del-imperio-y-del-exilio/) | Identificación de la edición; apoyo secundario para edificio y palo. |
| ES-EDITORIAL | [Ficha de 2Tomatoes](https://2tomatoesgames.com/es/oath-cronica-del-imperio-y-el-exilio-8437022321301.html) | Localizada, pero acceso directo 403; no se usa como prueba de haber leído el reglamento. |

## Transcripciones de vídeos de 2Tomatoes

El usuario ha aportado cuatro archivos en `assets`, correspondientes a tres
vídeos del base. Se han evaluado íntegramente en
[EVALUACION_TRANSCRIPCIONES.md](EVALUACION_TRANSCRIPCIONES.md); los pasajes,
líneas, tiempos disponibles y hashes se conservan en
[video-evidence.json](video-evidence.json). El SRT y el TXT del primer vídeo son
duplicados exactos del mismo texto y se cuentan como una sola fuente.

| ID | Vídeo | Procedencia y límite |
| --- | --- | --- |
| ES-VIDEO-1 | [Intro y Roles](https://www.youtube.com/watch?v=opLXFjIpBHk) | URL del TXT; atribución oficial aportada por el usuario. Texto automático con tiempos, sin verificación de audio o fotogramas. |
| ES-VIDEO-2 | Canciller, Ciudadano e Imperio | Archivo aportado sin URL ni tiempos; atribución oficial del usuario. Localización por líneas. |
| ES-VIDEO-3 | [Palos de Cartas](https://www.youtube.com/watch?v=7ti48TdTJ9k) | Canal 2Tomatoes Games y fecha 16/12/2022 corroborados en el índice de YouTube. TXT sin tiempos; sin verificación de audio o fotogramas. |

El vocabulario reiterado en transcripciones puede apoyar una elección, pero no
prevalece sobre un componente legible ni convierte una explicación del base en
regla de NF. Los títulos dudosos se contrastan por efecto e ID antes de adoptarlos.

## Fuentes inglesas y corpus

| ID | Fuente | Alcance |
| --- | --- | --- |
| NF | [New Foundations Rulebook](https://buriedgiant.com/oath/New_Foundations_Rulebook.pdf) | 48 páginas. Especialmente pp. 9–10: direcciones y Explorar; 17–29: fases, acciones y poderes; 31: sitios; 33–36: legados, Imperio y empates; 36–40: Crónica; 44–45: glosario. |
| NF-WELCOME | [Welcome to New Foundations](https://buriedgiant.com/oath/Welcome_to_New_Foundations_Booklet.pdf) | 16 páginas. Transición desde el juego base, componentes sustituidos y preparación. |
| CORPUS | [Catálogo oficial](https://cards.buriedgiant.com/) y [repositorio público](https://github.com/buriedgiantstudios/cards/tree/c9ef9b6f75c4979fad00da31622519556d444ae8/content/card-images/oath/en-US) | Los 300 registros locales y sus PNG originales. Contextos por ID en terminology-context.json; hashes del catálogo y de las imágenes en las auditorías locales. |

Las páginas de NF son las numeradas en el PDF, que coinciden con la posición de
sus páginas. Los archivos consultados muestran fechas de edición de junio de
2026. Se registran sus SHA-256 para distinguirlos de futuras sustituciones bajo
la misma URL. Las ilustraciones sirven para resolver sentidos de títulos, no
para añadir restricciones a los poderes.

## Manual español revisado y descartado como norma actual

**ES-SUFFO**: [traducción de Manuel Suffo publicada en Mesa de Guerra](https://mesadeguerra.com/download/oath-manual-esp/),
22 páginas, página de descarga creada en diciembre de 2020 y actualizada en
febrero de 2021. Aunque la ficha diga «traducción final», su contenido refleja
reglas anteriores a la edición comercial y usa Concentración, Interior,
Asesores y Aventura, entre otros términos. No está identificado como reglamento
de 2Tomatoes. Se ha comparado y **no se usa para fijar la terminología de NF**.

## Apoyo léxico

**LEX-BEE**: [Scripps National Spelling Bee: origen del término bee](https://spellingbee.com/node/85).
La institución explica el sentido de reunión comunitaria para una actividad y
cita expresamente spinning bee. Apoya la interpretación de T026 junto con la
ilustración de `OATH-232`; Velada de Hilado sigue siendo una propuesta propia.

## Etiquetas de procedencia

- `2T-visible`: término o forma flexionada leído en un componente fotografiado.
  No certifica la redacción completa de una carta nueva.
- `adaptacion-2T`: composición o ampliación propia de términos comprobados;
  por ejemplo, Relicario a partir de Relicario Imperial.
- `referencia-secundaria`: apoyo en la explicación del reseñador, sin foto que
  confirme la etiqueta completa.
- `2T-transcripcion`: apoyo en una transcripción automática aportada de un vídeo
  atribuido a 2Tomatoes; no equivale a haber verificado audio ni texto impreso.
- `propuesta-NF`: traducción propuesta de una regla, sistema o expresión del
  corpus, contrastada cuando procede con el reglamento inglés.
- `propuesta-tematica`: propuesta léxica o de título a partir del texto y,
  en los casos anotados, de la ilustración. No se presenta como nombre publicado.

`certeza = alta` indica respaldo claro del término o una distinción reglada bien
definida; `media`, una equivalencia razonable sin confirmación editorial;
`baja`, una decisión con alternativas relevantes. Todas siguen en `proposed`.

La [auditoría de la revisión](revision-audit.json) registra los recuentos,
comprobaciones y hashes de los archivos finales de traducción.
