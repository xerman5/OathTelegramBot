# Oath — La Carta del Día 🃏

Bot de Telegram para una comunidad española de [Oath](https://ledergames.com/products/oath),
ejecutado con Python 3.12 y GitHub Actions, sin servidor propio.

El proyecto tiene tres partes:

1. **Generar el catálogo** desde la biblioteca pública de Buried Giant Studios.
2. **Publicar una carta diaria** con imagen, texto y símbolos convertidos a emojis.
   La selección es determinista según la fecha; el historial registra los envíos,
   pero no evita repeticiones entre días distintos.
3. **Publicar un resumen semanal** de novedades de Leder Games y Buried Giant:
   YouTube, blogs, Reddit, BoardGameGeek, Kickstarter y Backerkit. Gemini prepara
   el resumen en español; algunas fuentes se consultan mediante un proxy de
   Cloudflare cuyo código no está incluido en este repositorio.

La evolución en curso es conservar las cartas en local, traducirlas al español
y producir versiones tradumaquetadas de fans. Los originales locales y el
glosario ya están preparados; la traducción, maquetación y conexión con Telegram
siguen pendientes.

**El repositorio es público: no se versiona ninguna imagen.** Originales,
referencias y reescalados se conservan solo en local y están excluidos por
`.gitignore`. Los catálogos, rutas, URLs y auditorías de texto sí se versionan;
una copia recién clonada no incluye los PNG.

## Por dónde empezar

- [Estado del proyecto](docs/ESTADO_PROYECTO.md): alcance, decisiones acordadas,
  limitaciones, trabajo pendiente y situación de los archivos locales.
- [AGENTS.md](AGENTS.md): pautas para agentes y colaboradores.
- [Catálogos locales](local_cards/README.md): datos, originales PNG y esquema español.
- [Guía de traducción](local_cards/translation/GUIA_TRADUCCION.md): glosario editable,
  criterio de 2Tomatoes y uso de las fuentes.
- [Transcripciones aportadas](assets/README.md): inventario y límites del material de apoyo.

## Estructura del repo

```
send_daily_card.py          ← script principal (stdlib puro, sin pip)
generate_cards.py           ← reconstruye y actualiza el catálogo público
send_weekly_digestv3.py     ← versión activa del resumen semanal
send_weekly_digest.py       ← implementación anterior
send_weekly_digestv2.py     ← implementación anterior
oath_cards.json             ← 330 cartas: juego base + Denizen Pack
history.json                ← historial de cartas enviadas (se autogenera)
tests/                     ← pruebas del generador sin acceso a red
.github/
  workflows/
    daily_card.yml          ← cron de GitHub Actions
    weekly_digest.yml       ← resumen semanal con send_weekly_digestv3.py
docs/ESTADO_PROYECTO.md     ← estado y continuidad del trabajo
local_cards/               ← catálogos NF + Denizen y guías; las imágenes son solo locales
assets/                    ← transcripciones automáticas de vídeos de 2Tomatoes
```

---

## Estado actual — 14/11/2026

| Área | Estado comprobado en esta copia local |
| --- | --- |
| Generador | Reconstruido; 14 pruebas offline. Catálogo del bot: 330 registros, 108 con `legacy_id`. |
| Bot diario y resumen semanal | Implementados y configurados en Actions; no se ha auditado su ejecución remota en esta revisión. |
| Copias locales | 240 caras de NF + 60 cartas del Denizen Pack, con 300 PNG originales contrastados con GitHub. |
| Preparación del español | Esquema en los JSON y 408 propuestas terminológicas; las 300 traducciones siguen vacías. |
| Tradumaquetación y envío local | Pendientes; el bot continúa usando texto inglés e imágenes remotas. |

Los dos catálogos tienen funciones distintas: `oath_cards.json` contiene
**base + Denizen Pack** para el bot; `local_cards/` contiene **NF + Denizen Pack**
para preparar la traducción, excluyendo el base por decisión del usuario.
No se sustituyen entre sí. La procedencia y situación en Git están detalladas
en [ESTADO_PROYECTO.md](docs/ESTADO_PROYECTO.md).

---

## Generar y actualizar el catálogo

Desde la raíz del repositorio, con Python 3.12 y sin dependencias externas:

```bash
python3 generate_cards.py --dry-run  # consultar y validar sin escribir
python3 generate_cards.py            # actualizar oath_cards.json
python3 -m unittest discover -s tests -v
```

La [biblioteca pública](https://cards.buriedgiant.com/search?q=game:oath%20product:%22denizen-deck%22)
es una aplicación JavaScript. El generador utiliza los mismos datos: consulta
[`version.json`](https://cardcdn.buriedgiant.com/version.json), descarga
[`cards.min.json`](https://cardcdn.buriedgiant.com/cards.min.json) con esa versión
y decodifica su formato `compress-json` (tabla de valores con referencias en base 62).
No necesita navegador, scraping de HTML ni claves de API.

Por defecto selecciona solo `game=oath`, `locale=en-US` y los productos
`oathbasegame` y `denizen-deck`: actualmente **270 + 60 cartas**. Descarta el idioma
de prueba `te-ST`. New Foundations y Clockwork se pueden exportar por separado:

```bash
python3 generate_cards.py --products denizen-deck --output denizen_cards.json
python3 generate_cards.py --products oath-newfoundations --output foundations_cards.json
python3 generate_cards.py --products oath-clockwork --output clockwork_cards.json
python3 generate_cards.py --input /ruta/cards.min.json --output catalogo_local.json
```

El campo público `text` se guarda como `description`, conservando Markdown y
símbolos del juego. Se mantienen `image`, `name`, `id` y `tags`, y se añaden
`game`, `product` y `locale` para identificar el origen de cada carta. Las imágenes
siguen siendo las URLs originales, normalmente WebP. Este generador no descarga
PNG, añade traducciones ni conserva campos arbitrarios de un archivo anterior.
**No usar su salida para sobrescribir los JSON de `local_cards/`**: perderían
metadatos locales y el campo `translations`. Las copias PNG existentes se
obtuvieron aparte; su actualización completa aún no tiene un comando reproducible
incorporado al repositorio.

### Identificadores e historial

El catálogo utiliza los **IDs oficiales actuales**. Buried Giant ha reasignado
algunos: por ejemplo, `OATH-199` era *Sprawling Rampart* en nuestro JSON antiguo y
ahora corresponde a *Golem Legions*. *Sprawling Rampart* pasa a `OATH-E01-OG` y
conserva `"legacy_id": "OATH-199"`. La migración compara nombre, producto e idioma,
no IDs reutilizados, y mantiene esa referencia en actualizaciones posteriores.

`history.json` se conserva intacto: sus entradas anteriores a esta migración
utilizan los IDs antiguos. Para interpretarlas, consulta `legacy_id` y el catálogo
anterior en Git; un mismo ID puede significar cartas distintas antes y después.

El generador valida los productos solicitados, los campos obligatorios y la
unicidad de IDs antes de sustituir el archivo de forma atómica. Si una actualización
eliminaría cartas existentes, se detiene: revisa la fuente y los filtros o usa
`--allow-removals` si la eliminación es intencionada. La actualización se ejecuta
manualmente y no envía nada a Telegram; los siguientes envíos diarios utilizan el
JSON actualizado.

---

## Puesta en marcha

### 1. Crear el bot en Telegram

1. Abre [@BotFather](https://t.me/BotFather) → `/newbot`
2. Sigue los pasos y copia el **token** (`123456789:ABC-DEF...`)

### 2. Obtener el Chat ID del canal/grupo

- **Canal público**: usa `@nombre_del_canal` directamente.
- **Canal privado o grupo**: añade el bot como admin, envía un mensaje y visita:
  ```
  https://api.telegram.org/bot<TOKEN>/getUpdates
  ```
  Busca `"chat": {"id": -1001234567890 ...}` en la respuesta.

> En canales, el bot debe ser **administrador** con permiso para publicar mensajes.

### 3. Preparar el repositorio en GitHub

Usa este repositorio o un fork y habilita Actions. Los archivos de trabajo local
pueden no estar versionados: comprueba `git status --short` antes de preparar
un cambio. El inventario distingue originales de copias reescaladas auxiliares.

### 4. Añadir los Secrets en GitHub

En tu repo: **Settings → Secrets and variables → Actions → New repository secret**

| Nombre                | Valor                          |
|-----------------------|--------------------------------|
| `TELEGRAM_BOT_TOKEN`  | `123456789:ABC-DEF...`         |
| `TELEGRAM_CHAT_ID`    | `@tu_canal` o `-1001234567890` |
| `TELEGRAM_THREAD_ID`  | ID del tema del grupo, opcional |
| `GEMINI_API_KEY`      | Clave de Gemini, necesaria para el resumen semanal |

No imprimas credenciales ni URLs que las contengan en los logs.

### 5. Ejecutar una publicación manual

En tu repo: **Actions → Carta del Día → Run workflow**

Esto envía un mensaje real. Para verificar cambios sin publicar, usa las
[comprobaciones locales](#comprobaciones-locales). El script diario no dispone
de modo `--dry-run`; esa opción corresponde al generador.

---

## Horario

El workflow diario está configurado a las **7:00 UTC**:

- Invierno (CET = UTC+1): **8:00** en España peninsular.
- Verano (CEST = UTC+2): **9:00** en España peninsular.

Para ajustarlo edita `.github/workflows/daily_card.yml`:

```yaml
- cron: "0 7 * * *"
```

El resumen semanal se ejecuta los **miércoles a las 17:00 UTC**: 18:00 en invierno
y 19:00 en verano. Ambos workflows admiten ejecución manual desde Actions.
Los horarios programados no garantizan que la publicación sea inmediata.

---

## Historial automático

Después de un envío correcto, el workflow añade la fecha UTC y el ID a
`history.json` y hace commit si hay cambios:

```json
[
  {"date": "2026-06-08", "card_id": "OATH-042"},
  {"date": "2026-06-09", "card_id": "OATH-117"}
]
```

El historial lo escribe el workflow, no el script diario por sí solo. Si ya
existe una última entrada con la fecha de hoy, no añade otra; eso **no impide
reenviar** una carta al ejecutar de nuevo el script o el workflow. Tampoco evita
que una carta vuelva a salir otro día. La selección depende de la fecha del
entorno y de la lista y orden actuales del catálogo.

## Comprobaciones locales

Estos comandos no envían mensajes ni necesitan claves:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile *.py
python3 -m json.tool oath_cards.json > /dev/null
python3 -m json.tool history.json > /dev/null
python3 -m json.tool local_cards/new-foundations/cards.json > /dev/null
python3 -m json.tool local_cards/denizen-pack/cards.json > /dev/null
```

Las pruebas cubren el generador. Las auditorías de cartas y traducción documentan
otras comprobaciones realizadas; no constituyen una suite automática completa
para traducción, imágenes o Telegram.

---

## Dependencias

Los scripts usan solo la biblioteca estándar de Python 3.12. No hay
`requirements.txt` ni es necesario ejecutar `pip install`. El catálogo, las imágenes,
las fuentes del resumen, el proxy, Gemini y Telegram son servicios externos.

---

## Próximo trabajo

1. Revisar las decisiones terminológicas nuevas y los títulos todavía dudosos,
   conservando la traducción oficial de 2Tomatoes para conceptos habituales.
2. Incorporar una actualización reproducible de las copias locales que conserve
   traducciones y relacione los PNG por ID oficial y producto.
3. Traducir y revisar las cartas; después, crear versiones tradumaquetadas de fans.
4. Adaptar el bot para cargar traducciones e imágenes locales. Cambiar solo
   `CARDS_FILE` no implementa esa integración: hoy espera una URL en `image`.

El objetivo es evitar depender del CDN para las imágenes durante la publicación.
La actualización del catálogo, Telegram y el resumen semanal siguen necesitando
servicios externos. Los criterios y tareas están desarrollados en
[ESTADO_PROYECTO.md](docs/ESTADO_PROYECTO.md).
