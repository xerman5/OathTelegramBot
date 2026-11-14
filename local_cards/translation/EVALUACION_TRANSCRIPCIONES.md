# Evaluación de las transcripciones de 2Tomatoes

Revisión: **14 de noviembre de 2026**.

## Resultado

**Sí ayudan a desambiguar vocabulario del juego base.** Aportan contexto oral,
reiteran términos ya comprobados en componentes y ofrecen candidatos para algunos
títulos. Su utilidad es menor para grafías exactas, operaciones regladas y texto
de cartas: mezclan reconocimiento automático, explicación coloquial y reglas
anteriores a New Foundations.

Se han leído íntegramente las tres transcripciones únicas. No se ha escuchado
el audio ni revisado fotogramas. Se conservan los cuatro archivos originales sin
corregirlos; [video-evidence.json](video-evidence.json) registra sus hashes,
fragmentos localizables y las decisiones de esta evaluación.

## Inventario y procedencia

| Fuente | Material local | Localización disponible |
| --- | --- | --- |
| ES-VIDEO-1 | Intro y Roles: TXT de Tactiq y SRT de DownSub | [Vídeo enlazado en el TXT](https://www.youtube.com/watch?v=opLXFjIpBHk). Ambos archivos incluyen tiempos. |
| ES-VIDEO-2 | Canciller, Ciudadano e Imperio: TXT | Sin URL ni tiempos; referencias por líneas del archivo original. |
| ES-VIDEO-3 | Palos de Cartas: TXT | [Vídeo localizado](https://www.youtube.com/watch?v=7ti48TdTJ9k). El índice de YouTube identifica el canal 2Tomatoes Games y fecha 16/12/2022; el TXT no incluye tiempos. |

El usuario identifica los tres vídeos como oficiales. Se ha corroborado de forma
independiente la metadata del tercero; no la del primero ni del segundo. El
nombre del canal que reconoce el ASR está deformado y no sirve para atribuirlos.

**Cuatro archivos no equivalen a cuatro fuentes independientes.** Al retirar
cabeceras, numeración y tiempos, las **341 entradas** del SRT y del TXT de
Intro y Roles son literalmente iguales y están en el mismo orden. Son una sola
transcripción en dos formatos; Tactiq y DownSub no aportan confirmaciones
independientes de esos términos.

## Qué refuerza en el glosario

| IDs | Vocabulario | Aportación |
| --- | --- | --- |
| M014 | palo | Aparece explícitamente en la explicación y en el título oficial del vídeo 3. |
| M051 | plan de batalla | Se repite en varios ejemplos; respalda esta propuesta frente a plan de combate. |
| M061 | jugador Imperial | El vídeo 2 utiliza expresamente jugadores imperiales. |
| M007 | edificio | El vídeo 2 lo enumera junto a habitante y reliquia, apoyando su uso como categoría. |
| N049 | Usurpador | Hay apariciones limpias, aunque otros pasajes lo deformen como observador. |
| M002, M003, M019, M056 | consejero, sitio, tropa, gobernar | Corroboran los términos de las fotografías; las paráfrasis no requieren nuevos sinónimos. |
| M017, F011, F012, F038 | Suministro, Actividad, Descanso, actualizar | El vídeo 2 mantiene la terminología de la ayuda de jugador. |
| N022–N027 | Arcano, Bestia, Discordia, Hogar, Nómada, Orden | Coinciden con el tapete. Nómada se reconoce bien al final, aunque la primera enumeración diga nuevo. |
| M062–M066, N006–N009 | Canciller, Ciudadanía, exiliar, Sucesor, Guardián del Juramento y nombres de estandartes y relicario | Amplían el contexto de uso de palabras ya comprobadas. Relicario Imperial sigue siendo la forma del base. |

Se han añadido referencias de transcripción a las entradas pertinentes y se han
reclasificado **cinco** como `2T-transcripcion`: M007, M014, M051, M061 y N049.
Esta categoría distingue evidencia automática de texto impreso legible. No se
ha elevado su certeza a alta por el mero hecho de aparecer en subtítulos.

## Títulos que merece la pena comprobar en pantalla

| ID | Lectura automática | Evaluación |
| --- | --- | --- |
| T153 | código de magos | Candidato **Código de Magos** para Magician's Code. El efecto sobre el Secreto más Oscuro encaja con la carta base; falta comprobar el título exacto y su número. |
| T076 | Heredero largo tiempo perdida | Apoya la familia **Heredero Largo Tiempo Perdido**. La concordancia errónea impide usarla como prueba literal del rótulo. |
| N051 | exploradores | **No corresponde a Outriders**: el efecto descrito de ganar Suministro al atacar encaja con Scouts (`OATH-008`). Outriders (`OATH-104`) ignora calaveras. Mantener su título español pendiente. |

Ubicaciones en el vídeo 3, por líneas originales del TXT: Código de magos,
208–223; Exploradores y su efecto, 295–304; Heredero, 442–463. Las ventanas
concretas y los fragmentos completos figuran en V025–V027 de video-evidence.json.
No se han inventado tiempos para los archivos que carecen de ellos.

La identificación por efecto evita una asociación engañosa: que Scouts y
Outriders admitan traducciones militares parecidas no permite intercambiar sus
IDs. Otros títulos mencionados —como Médico Ambulante o Posada junto al Camino—
sirven como pistas para futuras comprobaciones, aunque esas cartas base no formen
parte de los dos catálogos que estamos traduciendo.

## Errores y usos que no deben importarse literalmente

- **Nombres mal reconocidos**: Oz, Ghost, off y out por Oath; gran centro por
  Gran Cetro; mejoramiento por juramento; Casillero o cáncer en pasajes sobre
  Canciller. Algunos se resuelven por contexto y por los componentes ya leídos.
- **Cambios de término peligrosos**: observador aparece en explicaciones del
  Usurpador; nuevo sustituye a Nómada en una enumeración; pan de batalla aparece
  donde otros ejemplos dicen plan de batalla. No añadir estas formas como
  vocabulario válido del glosario.
- **Paráfrasis**: robar secretos describe coloquialmente el efecto de Juego de
  Manos. No demuestra que `take` deba traducirse como `draw`. Mantener coger,
  robar y ganar con sus funciones diferenciadas.
- **Vocabulario no específico**: juego Legacy habla del género y de continuidad
  entre partidas, no de las cartas de legado nuevas de NF. No acredita una
  traducción oficial para `legacy` como componente.
- **Ambigüedad reglada**: mayoría, lugar, contador, turno y ronda pueden aparecer
  como simplificaciones o lapsus. Mantener el término impreso comprobado y
  contrastar el efecto inglés antes de fijar una equivalencia técnica.

No conviene hacer reemplazos globales sobre los archivos: una misma palabra
errónea puede tener varias lecturas, y una paráfrasis oral no siempre es un error
del reconocimiento automático. Las normalizaciones deben guardar el fragmento
original y la justificación.

## Separar la edición base de NF

Los vídeos explican el base. Por ejemplo, la transcripción describe una oferta
de ciudadanía con una reliquia del Relicario Imperial y reglas antiguas de exilio
mediante pagos. NF modifica esos procedimientos y la negociación. También el
objetivo antiguo de Protección cuenta reliquias y estandartes, mientras el
objetivo de NF cuenta reliquias.

Los nombres españoles pueden reutilizarse; las restricciones, costes y ventanas
se traducen desde el inglés actual de NF. Las transcripciones tampoco resuelven
la traducción de fundamentos, linajes, estados de legados o Challenge, que son
parte de nuestro trabajo nuevo.

## Cambios y siguiente uso

El glosario conserva sus **408 propuestas españolas, estados y notas de usuario**.
Solo se han ampliado procedencias, clasificaciones y notas de investigación.
Código de Magos y la familia del Heredero quedan como candidatos documentados;
Exploradores se descarta como prueba para Outriders. No se han modificado las
cartas, sus traducciones vacías, los PNG ni las transcripciones aportadas.

Para avanzar, estas fuentes permiten dirigir la revisión a los fotogramas donde
se enseñan las cartas, fijar títulos y comprobar encabezados. Para vocabulario
reiterado y ya visible en componentes aportan corroboración útil desde ahora.
