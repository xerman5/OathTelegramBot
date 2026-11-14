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
```

---

## Estado de la reconstrucción — 14/11/2026

La primera etapa está completada: se ha reconstruido el generador perdido,
actualizado el catálogo a **330 cartas** y conservado **108 identificadores
antiguos** en `legacy_id`. Los archivos del bot diario, del resumen semanal y el
historial de envíos no se han modificado. `AGENTS.md` recoge las pautas de contribución.

Se verificaron la descarga real del catálogo, la conservación de las 270 cartas
anteriores por nombre, los datos contra la fuente oficial, la regeneración idéntica
con la misma fuente, las exportaciones por producto y el formato del bot diario.
Las 14 pruebas automatizadas pasan, además de las comprobaciones de sintaxis y JSON.
Estas verificaciones no publican mensajes en Telegram.

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
siguen siendo las URLs originales, normalmente WebP. Este paso no las descarga,
traduce ni modifica; esas mejoras corresponden a la segunda etapa.

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

### 3. Subir el código a GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/oath-carta-del-dia.git
git push -u origin main
```

### 4. Añadir los Secrets en GitHub

En tu repo: **Settings → Secrets and variables → Actions → New repository secret**

| Nombre                | Valor                          |
|-----------------------|--------------------------------|
| `TELEGRAM_BOT_TOKEN`  | `123456789:ABC-DEF...`         |
| `TELEGRAM_CHAT_ID`    | `@tu_canal` o `-1001234567890` |
| `TELEGRAM_THREAD_ID`  | ID del tema del grupo, opcional |
| `GEMINI_API_KEY`      | Clave de Gemini, necesaria para el resumen semanal |

No imprimas credenciales ni URLs que las contengan en los logs.

### 5. Probar manualmente

En tu repo: **Actions → Carta del Día → Run workflow**

Si todo va bien, verás la carta en tu canal y un nuevo commit en `history.json`.

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

## Historial automático (anti-desactivación)

Cada vez que se ejecuta, el workflow hace un commit en `history.json`:

```json
[
  {"date": "2026-06-08", "card_id": "OATH-042"},
  {"date": "2026-06-09", "card_id": "OATH-117"}
]
```

Esto mantiene el repo activo y evita que GitHub desactive el cron por inactividad a los 60 días.

---

## Dependencias

Los scripts usan solo la biblioteca estándar de Python 3.12. No hay
`requirements.txt` ni es necesario ejecutar `pip install`. El catálogo, las imágenes,
las fuentes del resumen, el proxy, Gemini y Telegram son servicios externos.

---

## Segunda etapa pendiente: cartas en español e imágenes locales

El siguiente objetivo es servir las cartas sin depender del CDN durante la
publicación y acercarlas a los fans en español:

1. **Descargar las imágenes en local como PNG.** La fuente actual suele ser WebP;
   habrá que descargar y convertir la imagen, no solo cambiar su extensión.
2. **Traducir el texto de cada carta al español**, conservando el original y
   manteniendo una terminología coherente para reglas y símbolos.
3. **Crear una versión tradumaquetada de fans** con el texto español sobre la
   carta e identificarla como traducción no oficial.
4. **Adaptar el envío diario** para publicar el archivo local de esa versión.

Esta etapa todavía no está implementada. El catálogo conserva el texto original,
las URLs de imagen y los campos `id`, `game`, `product` y `locale` que permitirán
relacionar originales, traducciones e imágenes generadas. Quedan por concretar
el almacenamiento de imágenes, la herramienta de traducción y el proceso de
maquetación y revisión.
