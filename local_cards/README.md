# Catálogos locales y traducciones

Esta carpeta prepara la traducción y tradumaquetación de fans de **NF y Denizen
Pack**. El [estado general](../docs/ESTADO_PROYECTO.md) distingue este trabajo de
las publicaciones actuales del bot. El catálogo de producción es
`../oath_cards.json` y contiene base + Denizen; no utiliza estos JSON locales.

**Las imágenes no se suben al repositorio público.** Los originales, reescalados
y referencias se conservan únicamente en local, excluidos por `.gitignore`.
El inventario siguiente describe la copia de trabajo completa: al clonar solo
se reciben JSON, documentación y auditorías de texto, no los PNG. Una ruta `image`
sin archivo en un clon nuevo no demuestra una descarga incompleta del original.

## Organización y alcance

- `new-foundations/cards.json`: 240 caras de cartas y sus imágenes PNG.
- `denizen-pack/cards.json`: 60 cartas y sus imágenes PNG.
- `translation/`: decisiones terminológicas, fuentes, contextos y auditoría de revisión.
- `*/upscayl_png_high-fidelity-4x_4x/`: copias reescaladas auxiliares, separadas de los originales.
- `reference for upscaling with more resolution/`: imágenes auxiliares de referencia.

Los productos públicos son `oath-newfoundations` y `denizen-deck`, ambos en
`en-US`. El base y Clockwork quedan fuera de esta descarga. Los recuentos proceden
de los dos JSON y sus imágenes referenciadas: no contar PNG recursivamente,
porque se duplicarían los originales con sus derivados.

## Originales, derivados y verificación

Cada `image` es una ruta relativa a la carpeta de su JSON. `source_image`
conserva la URL del catálogo público. Los archivos PNG actuales están en inglés y
son los originales del repositorio oficial, descargados sin convertir ni recomprimir.
Sus URLs y hashes figuran en [`original-png-audit.json`](original-png-audit.json).
`source_image` puede seguir apuntando al WebP del CDN; la URL exacta del PNG de
origen está en esa auditoría. Los nombres locales combinan ID y nombre, por
ejemplo `denizen-pack/OATH-199-golem-legions.png`.

Los archivos de las carpetas `upscayl_*` no son originales de mayor resolución
publicados por la editorial. No se ha evaluado su legibilidad ni se ha elegido
usarlos para maquetar. No están cubiertos por la auditoría de los 300 originales.
Conservarlos aparte y no redirigirles `image` por defecto.

La [verificación de integridad](VERIFICACION.md) contrasta los 300 registros y sus
imágenes con las fuentes oficiales y detalla su alcance y calidad de imagen.
El [contraste con los manuales de la caja](CONTRASTE_CAJA.md) explica cómo se
corresponden las 240 caras de NF con sus componentes físicos y qué queda fuera.
`completeness-audit.json` documenta la primera fase, cuando había conversiones
desde WebP: sus hashes de imagen son históricos. No usarlos para comprobar los
PNG originales que sustituyeron después esas conversiones.

## Estructura de la traducción española

La [guía de traducción](translation/GUIA_TRADUCCION.md) prepara 408 decisiones de
vocabulario y expresiones, con 89 prioritarias. La
[primera propuesta](translation/PROPUESTA_TERMINOS.md) contrasta el inglés de NF
con componentes españoles de 2Tomatoes y distingue los términos comprobados de
las propuestas propias. Sus [fuentes](translation/FUENTES.md) quedan documentadas;
las [55 decisiones de certeza baja](translation/PENDIENTES.md) tienen alternativas
para revisión. El [glosario editable](translation/glossary.csv) permite fijar las equivalencias antes
de traducir; el [glosario de consulta](translation/GLOSARIO.md) reúne las propuestas
por ID. Todas están en `proposed`, pendientes de aprobación.

La [evaluación de las transcripciones](translation/EVALUACION_TRANSCRIPCIONES.md)
incorpora los vídeos del base aportados en `assets` como apoyo léxico, separando
duplicados, errores automáticos y candidatos que requieren comprobación visual.

Las 300 cartas reservan una traducción en `translations.es-ES`:

```json
{
  "translations": {
    "es-ES": {
      "name": null,
      "text": null,
      "status": "pending"
    }
  }
}
```

- `name`: título traducido. `null` significa que todavía no está disponible.
- `text`: texto traducido de las reglas. `null` significa pendiente; `""` se
  reserva para una carta que no lleva texto. Conservar Markdown y los tokens
  de símbolos, como `` `symbol:favor` ``.
- `status`: `pending` mientras falte la traducción, `draft` para un borrador
  y `reviewed` cuando se haya revisado y esté listo para utilizarse.

El nombre y los textos originales siguen en `name`, `text` y `description`.
`locale: "en-US"` identifica ese contenido original y no se cambia al añadir
una traducción. El texto español solo se guarda en `translations.es-ES.text`,
sin duplicarlo en otro `description` traducido.

Los estados de datos y los de terminología son distintos:

| Archivo | Campo | Estados |
| --- | --- | --- |
| `cards.json` | `translations.es-ES.status` | `pending`, `draft`, `reviewed` |
| `translation/glossary.csv` | `estado` | `pending`, `proposed`, `approved` |

La certeza de una equivalencia mide evidencia, no aprobación. Mantener el
criterio ya acordado de 2Tomatoes para vocabulario habitual; resolver por separado
las novedades y títulos dudosos. Ninguna carta recibe `reviewed` solo por tener
términos aprobados.

Esta estructura prepara los datos; todavía no se ha traducido ni maquetado
ninguna carta. El bot actual sigue leyendo los campos originales. Un futuro
consumidor podrá utilizar la traducción revisada y recurrir al original mientras
esté pendiente. Al volver a exportar estos catálogos, conservar `translations`
por ID oficial y producto; no sobrescribirlo con datos descargados de la fuente.

## Actualización y mantenimiento

`generate_cards.py` exporta el formato del bot, con `description` e imágenes
remotas. **No conserva `translations` ni todos estos metadatos**: no dirigir su
`--output` a los JSON de esta carpeta. Falta incorporar un importador local
reproducible que conserve el trabajo humano por ID oficial, producto e idioma.

Para un cambio de datos, comparar primero una exportación temporal, preservar
originales y traducciones, revisar ambas caras de cada pareja y actualizar las
auditorías tras verificar sus declaraciones. Los hashes identifican una versión
concreta: no actualizarlos simplemente para ocultar una diferencia sin explicar.

Para cambios terminológicos, editar el CSV y sincronizar sus vistas Markdown.
`terminology-context.json` conserva el estado inicial; `revision-audit.json`
registra comprobaciones fechadas y hashes, no ejecuta la revisión. Las
transcripciones originales están en [assets](../assets/README.md); las notas y
correcciones se mantienen separadas.
