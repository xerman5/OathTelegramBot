# Estado y continuidad del proyecto

Última revisión: **14 de noviembre de 2026**. Este documento resume el estado
observado en la copia de trabajo; no certifica la ejecución remota de Actions.
Actualizarlo cuando cambien el alcance, los datos o las decisiones del usuario.

## Propósito y alcance

El proyecto mantiene tres funciones: reconstruir el catálogo público de Oath,
publicar una carta diaria en Telegram y publicar un resumen semanal de novedades.
La evolución acordada es conservar imágenes en local, traducir cartas al español
y crear versiones tradumaquetadas de fans para publicarlas sin depender del CDN
de imágenes. Telegram y los servicios del resumen semanal siguen siendo externos.

El trabajo de traducción abarca **New Foundations y Denizen Pack**. El usuario
excluyó descargar el juego base en estas carpetas; esto no elimina el base del
catálogo que usa el bot. Clockwork y la reproducción de todos los componentes
físicos de la caja quedan fuera del alcance actual.

## Estado por área

| Área | Hecho | Pendiente o límite |
| --- | --- | --- |
| Catálogo del bot | Generador reconstruido; 330 registros: 270 base + 60 Denizen. | Actualizaciones manuales; no hay sincronización programada. |
| Identificadores | IDs oficiales actuales; 108 referencias antiguas en `legacy_id`. | No reinterpretar IDs históricos sin considerar la migración. |
| Publicación diaria | Script y workflow existentes; imágenes remotas y texto original. | No lee las traducciones ni archivos de imagen locales. |
| Resumen semanal | `send_weekly_digestv3.py` es la versión invocada por Actions. | Depende de fuentes, Gemini y un proxy cuyo código no está aquí. |
| Descarga local | 240 caras de NF + 60 cartas del Denizen Pack y 300 PNG originales. | La descarga y preparación local no tienen todavía un programa reproducible incorporado al repo. |
| Integridad | IDs, campos, caras enlazadas y PNG contrastados con fuentes oficiales. | Es una instantánea de la versión consultada; no acredita futuras actualizaciones. |
| Español | Esquema `translations.es-ES`; glosario de 408 propuestas. | Las 300 traducciones tienen `name/text = null`, `status = pending`. |
| Terminología | 89 entradas prioritarias y 55 de certeza baja; fuentes documentadas. | El CSV tiene 408 estados `proposed`; no hay aprobaciones individuales registradas. |
| Tradumaquetación | Objetivo definido como versión fan no oficial. | Sin herramienta, plantilla, revisión visual ni cartas españolas generadas. |
| Reescalado | Hay 300 copias auxiliares en carpetas `upscayl_*`. | No son nuevos originales oficiales ni tienen validación de legibilidad o integración. |

## Documentos y archivos de referencia

| Necesidad | Referencia principal |
| --- | --- |
| Ejecutar o mantener el bot | [README](../README.md), [código diario](../send_daily_card.py) y [workflows](../.github/workflows/) |
| Contribuir o trabajar como agente | [AGENTS.md](../AGENTS.md) |
| Entender los datos locales | [local_cards/README.md](../local_cards/README.md) |
| Consultar cartas originales y traducciones futuras | `local_cards/{new-foundations,denizen-pack}/cards.json` |
| Editar decisiones de terminología | [glossary.csv](../local_cards/translation/glossary.csv) |
| Entender cómo traducir | [GUIA_TRADUCCION.md](../local_cards/translation/GUIA_TRADUCCION.md) |
| Revisar alternativas y su justificación | [PENDIENTES.md](../local_cards/translation/PENDIENTES.md) y [PROPUESTA_TERMINOS.md](../local_cards/translation/PROPUESTA_TERMINOS.md) |
| Comprobar procedencia | [FUENTES.md](../local_cards/translation/FUENTES.md), `sources.json` y `video-evidence.json` |
| Contrastar descarga y recuentos | [VERIFICACION.md](../local_cards/VERIFICACION.md) y [CONTRASTE_CAJA.md](../local_cards/CONTRASTE_CAJA.md) |
| Conocer las transcripciones aportadas | [assets/README.md](../assets/README.md) y [su evaluación](../local_cards/translation/EVALUACION_TRANSCRIPCIONES.md) |

El CSV es editable y canónico para las decisiones, no `GLOSARIO.md` ni
`terminology-context.json`. Los Markdown son vistas que hay que sincronizar;
el JSON de contextos conserva una instantánea inicial con traducciones vacías.
Los manifiestos de auditoría describen comprobaciones fechadas: no son programas
que regeneren o validen automáticamente todos los archivos.

## Decisiones acordadas que deben mantenerse

1. **Terminología habitual de 2Tomatoes.** El usuario ha fijado este criterio;
   no reabrirlo ni inventar sinónimos para términos ya comprobados. La revisión
   humana se concentra en novedades, ambigüedades y títulos no verificados.
2. **Reglas actuales desde el inglés.** El usuario confirma que NF aún no salió
   en español. Conservar nombres conocidos no significa copiar efectos del base.
3. **Originales y traducción separados.** Mantener texto inglés, metadatos,
   `locale: en-US`, IDs, símbolos y relaciones entre caras. El español se guarda
   solo en `translations.es-ES.name/text` con su propio estado de revisión.
4. **Identificadores oficiales.** Conservar `legacy_id` como referencia antigua
   y no reescribir el historial. Algunos IDs fueron reutilizados para otras cartas.
5. **Imágenes solo locales.** El repositorio es público y el usuario prohíbe subir
   imágenes: originales, referencias y derivados quedan fuera de Git mediante
   `.gitignore`. Los `image` de los JSON locales apuntan a los originales de cada
   carpeta; una ampliación o una versión española debe ir separada. No sustituir
   originales ni cambiar su procedencia.
6. **Fuentes diferenciadas.** Componentes legibles de 2Tomatoes para nombres;
   reglamento inglés de NF para reglas; ASR como apoyo con errores. El criterio
   editorial aprobado no convierte automáticamente las propuestas o cartas en
   `approved` / `reviewed`.

## Limitaciones que afectan al siguiente trabajo

### Dos formatos de catálogo

El bot consume `oath_cards.json`: `description` contiene el texto y `image` una
URL. Los JSON locales conservan además `text`, metadatos originales,
`source_image`, rutas PNG relativas y el espacio de traducción.

`generate_cards.py` produce el primer formato y solo conserva referencias
históricas conocidas. **No usarlo para sobrescribir los JSON locales**: no
preserva `translations` ni otros campos locales. Para una actualización, exportar
a una ruta temporal, comparar y desarrollar una unión por ID oficial, producto
e idioma que conserve el trabajo humano. Aún falta incorporar ese proceso al repo.

Cambiar `CARDS_FILE` por sí solo tampoco activa imágenes locales: el envío actual
espera URLs y no consulta `translations`. La elección diaria depende de la fecha
del entorno y de la lista y orden del catálogo. El historial no evita repeticiones
ni hace idempotente una nueva ejecución del envío.

### Integridad y calidad

NF tiene 240 **caras publicadas**, no 240 cartas físicas. Las 42 parejas enlazadas
están completas. El catálogo no incluye todos los tableros, ayudas ni reversos
genéricos; la comparación con la caja no equivale a transcribir todo su material.

Los PNG actuales se contrastaron byte a byte con el repositorio oficial en la
revisión `c9ef9b6f75c4979fad00da31622519556d444ae8`. La primera auditoría de
conversiones WebP es histórica; para los PNG actuales consultar
`original-png-audit.json`. El formato PNG no implica más resolución: las copias
oficiales tienen la resolución publicada, y las versiones `upscayl_*` son derivados.

### Fuentes españolas

No se consiguió el PDF completo de 2Tomatoes. La traducción antigua de Manuel
Suffo se revisó y descartó como norma actual porque describe reglas anteriores.
Los vídeos aportados ayudan con vocabulario, pero no se han cotejado audio ni
fotogramas. Cuatro archivos corresponden a tres vídeos: las dos transcripciones
del primero son idénticas. Los candidatos de títulos siguen distinguidos de
equivalencias comprobadas; Exploradores corresponde en el ejemplo a Scouts,
no a Outriders.

## Orden recomendado para continuar

1. Leer esta página, la guía y las decisiones pendientes; conservar las decisiones
   existentes. Cerrar términos nuevos y comprobar títulos con sus IDs y efectos.
2. Incorporar un proceso reproducible de actualización local antes de renovar
   los catálogos, preservando traducciones e imágenes originales.
3. Traducir por lotes y revisar reglas, referencias y los 24 tokens de símbolos.
   No hay un traductor automático de cartas implementado ni una herramienta elegida.
4. Diseñar la maquetación, mantener derivados separados y revisar cada imagen.
5. Integrar selección de traducción e imagen local en el bot y probar el envío
   en un destino de pruebas cuando forme parte de la tarea autorizada.

## Versionado y comprobaciones

La reconstrucción del generador y el catálogo actualizado se incorporaron en
`99a2457`. Esta entrega incorpora los JSON locales, glosario, transcripciones,
documentación y auditorías de texto. **Ninguna imagen debe incorporarse al
repositorio público**, ni siquiera las referencias o los derivados. Comprobar
el contenido preparado con `git diff --cached --name-only` antes de comitear;
no forzar la inclusión de archivos ignorados.

Un clon nuevo no trae los PNG aunque los JSON conserven sus rutas. Los informes
acreditan la descarga local revisada y registran fuentes y hashes; no afirman que
los binarios estén versionados. Falta incorporar el proceso reproducible para
recuperarlos en otra copia local.

Las 300 imágenes originales ocupan unos 107 MiB; las 300 copias reescaladas,
aproximadamente 2 GiB. Se conservan en local: su almacenamiento privado o respaldo
no está automatizado. Las carpetas de referencias y reescalado son material
auxiliar y no son entradas automáticas del bot o del catálogo.

Ejecutar las [comprobaciones locales del README](../README.md#comprobaciones-locales).
Las 14 pruebas cubren el generador; no hay suite completa de traducción,
maquetación o Telegram. Los scripts temporales usados para descargar y preparar
auditorías no están incorporados al repo: no depender de archivos de `/tmp`.
Al cambiar datos o documentación de traducción, sincronizar vistas y recuentos,
comprobar enlaces y actualizar los hashes de `translation/revision-audit.json`
solo después de verificar lo que se declara.
