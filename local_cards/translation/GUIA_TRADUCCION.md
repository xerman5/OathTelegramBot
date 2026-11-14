# Guía para fijar la traducción al español

Esta guía desarrolla la parte lingüística del
[estado del proyecto](../../docs/ESTADO_PROYECTO.md). Para formatos, originales
y actualización de los catálogos, consultar [el README local](../README.md).

## Alcance y punto de partida

Se han revisado nombres, textos y etiquetas de las **300 entradas locales**:
240 caras de New Foundations y 60 cartas del Denizen Pack. El inventario cubre
unas 7.500 palabras de reglas, además de títulos y etiquetas.

Hay **408 propuestas**, de las cuales **89 son prioritarias**:

| Grupo | Contenido | Entradas |
| --- | --- | ---: |
| M | Componentes, relaciones y estados | 82 |
| F | Acciones, operaciones y ventanas de reglas | 89 |
| N | Nombres de sistemas, fundamentos y referencias | 81 |
| T | Vocabulario temático y expresiones ambiguas | 156 |

Se prioriza el vocabulario comprobable de **2Tomatoes**, contrastando su función
con el reglamento inglés de NF. Las propuestas nuevas están identificadas como
tales. Ninguna equivalencia cuenta todavía como aprobada por el usuario.

El criterio editorial acordado con el usuario es **conservar la traducción oficial
de 2Tomatoes para los términos habituales**. La revisión humana se concentra en
conceptos nuevos, títulos sin equivalencia comprobada y ambigüedades. No proponer
sinónimos nuevos para vocabulario ya establecido; traducir los efectos conforme
al inglés actual de NF aunque sus reglas hayan cambiado respecto al base.

No se incluyen palabras corrientes sin dificultad específica, como `tree`.
Sí se incluyen palabras sencillas con función reglada, como `hold`, `rule` o
`empty`, y vocabulario especializado como `yew`. Una entrada puede cubrir una
expresión completa o un sentido particular de una palabra.

## Archivos y revisión

- [PROPUESTA_TERMINOS.md](PROPUESTA_TERMINOS.md): criterio, equivalencias centrales,
  comparación de referencias y diferencias de reglas relevantes.
- [glossary.csv](glossary.csv): **archivo editable principal**, separado por punto
  y coma, UTF-8 con BOM. Incluye propuesta, alternativas, fuente, certeza y notas.
- [GLOSARIO.md](GLOSARIO.md): vista de consulta de las 408 propuestas, referencias
  a títulos y símbolos que deben conservarse.
- [PENDIENTES.md](PENDIENTES.md): las 55 decisiones de certeza baja, agrupadas
  para facilitar una primera revisión humana.
- [FUENTES.md](FUENTES.md) y [sources.json](sources.json): procedencia, enlaces,
  versiones y límites de la comprobación.
- [EVALUACION_TRANSCRIPCIONES.md](EVALUACION_TRANSCRIPCIONES.md) y
  [video-evidence.json](video-evidence.json): evaluación de los tres vídeos
  únicos aportados en `assets`, con errores, candidatos y localización de pasajes.
- [terminology-context.json](terminology-context.json): evidencia de las cartas
  donde aparecen los términos y hashes de los catálogos. Sus campos
  `spanish: null` / `status: pending` conservan el punto de partida; el estado
  actual de las propuestas se mantiene exclusivamente en el CSV.

Los Markdown son vistas de esta primera propuesta; no se actualizan por sí
solos al editar el CSV. Al incorporar decisiones, sincronizar las vistas sin
sobrescribir `espanol`, `estado` ni `notas_usuario` del archivo principal.

Filtrar primero `prioridad = alta`; después, `certeza = baja`. `2T-visible`
significa leído en un componente fotografiado, mientras que `adaptacion-2T`
identifica una composición propia con ese vocabulario. `2T-transcripcion` señala
apoyo en subtítulos automáticos que aún no se han contrastado con audio o imagen.
Las demás etiquetas se explican en FUENTES.md. La certeza no sustituye la aprobación.

Para aceptar una entrada, revisar `espanol`, poner `approved` en `estado` y
añadir matices en `notas_usuario`. `proposed` es un borrador; `pending` se reserva
para una decisión que se deje sin propuesta. Conservar IDs y columnas de origen.
También se pueden comunicar decisiones por ID:

```text
M012 = cimiento
M069 = latente
F006 = Disputar
T026 = Velada de Hilado
```

Indicar género, plural, conjugación o mayúsculas cuando afecten al uso. Una
equivalencia no autoriza la sustitución automática de todas sus coincidencias:
los recuentos son léxicos, no un análisis del sentido de cada aparición.

## Distinciones que hay que conservar

| Términos | Distinción |
| --- | --- |
| `discard` / `bury` / `return to the box` | Descartar, enterrar y devolver a la caja tienen destinos distintos. |
| `burn` / `spend` / `pay` / `return` | Quemar, gastar, pagar y devolver no son operaciones intercambiables. |
| `rule` / `hold` | Gobernar y tener expresan relaciones distintas. |
| `draw` / `take` / `peek` / `reveal` / `play` | Conservar origen, visibilidad y activación de efectos. |
| `place` / `move` / `Travel` | Poner un peón no implica realizar Viajar. |
| `raid` / `conquest` / `Campaign` / `Challenge` | Incursión, conquista, Campaña y Disputar tienen reglas propias. |
| `legacy` / `lineage` | Legado y linaje pertenecen a sistemas distintos. |
| `active` / `dormant` / `faceup` / `facedown` | Separar estado del legado y orientación de la carta. |
| `Act` / `Action` | Actividad es la fase; Acción es el encabezado de un poder. |
| `most` / `more than` / `fewest` / `fewer than` | Mantener extremos relativos, comparaciones estrictas y reglas de empate. |
| `Oath` / `Vow` / `Pledge` | Juramento, voto y promesa conservan familias distintas. |

## Nombres y estilo

Fijar palos, regiones, estandartes, fundamentos y tareas de Crónica antes de
traducir sus referencias. Los títulos reutilizados conservan la equivalencia
elegida, incluidos los de cartas base citadas: `Marriage` (`OATH-148`) y
`Outriders` (`OATH-104`). Sus nombres españoles propuestos aún no se han
comprobado en 2Tomatoes.

Usar minúsculas para sustantivos comunes en el cuerpo y conservar nombres de
palos, regiones, fases y rótulos como términos identificables. Las mayúsculas del
inventario distinguen rótulos, no obligan a capitalizar cada palabra de un título
maquetado. Mantener el tratamiento de tú de la edición española, con la
conjugación que exija cada frase.

Las marcas `(NF)`, `(Back)` y prefijos como `Setup -` son metadatos del catálogo:
comprobar en el PNG qué debe aparecer en el título maquetado. En títulos ambiguos,
consultar la ilustración y registrar el criterio, sin deducir reglas de ella.

## Traducción posterior de las cartas

1. Conservar literalmente los **24 tokens de símbolos**, incluidos los acentos
   graves. No fusionar `favor` con `favorb`, `secret` con `secretb` ni `sword` con
   `swordh`.
2. Mantener Markdown, cifras, variables, signos como `±`, numeración de fundamentos
   y relaciones entre anversos y reversos.
3. Verificar quién decide, consentimiento, origen y destino, información oculta,
   momentos de resolución, cantidades, excepciones y empates. Los paréntesis
   pueden contener reglas esenciales.
4. No recortar reglas para ajustar la maquetación. Revisar primero la traducción;
   resolver el espacio después.
5. Guardar el resultado en `translations.es-ES.name` y `.text`, conservando inglés
   e IDs. Aprobar términos no convierte automáticamente una carta en `reviewed`.

**Los dos JSON de cartas conservan sus traducciones vacías y no se han modificado.**

## Mantener esta documentación

Tras incorporar decisiones, sincronizar el glosario de consulta, las alternativas
pendientes y los recuentos de la propuesta, esta guía y el estado del proyecto.
El criterio general de 2Tomatoes ya está acordado; los estados individuales del
CSV indican qué decisiones concretas se han registrado, no si ese criterio sigue
abierto. No hacer reemplazos globales sobre los textos de cartas a partir del CSV.

Las auditorías son instantáneas fechadas. Si cambian sus archivos, revisar las
comprobaciones pertinentes y después actualizar sus hashes y alcance, distinguiendo
lo revalidado de resultados históricos. No hay un comando incorporado que regenere
automáticamente todas las guías, contextos y auditorías sin intervención.
