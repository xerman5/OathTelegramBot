"""
send_weekly_digest.py
---------------------
Recopila novedades semanales del universo Leder Games / Buried Giant,
las resume con Gemini Flash y las publica en Telegram.

Ejecutado cada miércoles desde GitHub Actions.
Sin dependencias externas — solo stdlib de Python 3.12.

Variables de entorno (GitHub Secrets):
    TELEGRAM_BOT_TOKEN   — token del bot
    TELEGRAM_CHAT_ID     — ej: "@oathespana"
    TELEGRAM_THREAD_ID   — topic del grupo (ej: 143)
    GEMINI_API_KEY       — Google AI Studio (gratuito)
"""

import json
import logging
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID", "")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")

# Ventana de tiempo: últimos N días
# Cámbialo a 7 para producción, 30 para pruebas con más contenido
DAYS_BACK = 30

# ── Fuentes ───────────────────────────────────────────────────────────────────
# Fácil de modificar: añade o quita entradas de estas listas

YOUTUBE_CHANNELS = [
    # Para añadir un canal: {"name": "Nombre", "id": "UCxxxxxxxxxxxxxxxxxxxxxxx"}
    # El ID se obtiene entrando al canal en YouTube y mirando la URL o el código fuente
    {"name": "Buried Giant Studios", "id": "UC0MIABBBLK0YETRMWEDmWDA"},
    {"name": "Leder Games",          "id": "UCjea2nM_6W-zGOxk22mXkIg"},
    {"name": "Shut Up & Sit Down",   "id": "UCyRhIGDUKdIOw07Pd8pHxCw"},
]

RSS_FEEDS = [
    # ── Blogs y webs oficiales ──────────────────────────────────────────────
    # Para añadir un feed: {"name": "Nombre", "url": "https://...", "emoji": "🔤"}
    {
        "name":  "Leder Games — Blog",
        "url":   "https://feeds.feedburner.com/LederGames",
        "emoji": "🌿",
    },
    {
        "name":  "Buried Giant Studios — Blog",
        "url":   "https://buriedgiant.com/rss.xml",
        "emoji": "⚔️",
    },

    # ── Shut Up & Sit Down ──────────────────────────────────────────────────
    {
        "name":  "Shut Up & Sit Down — Artículos",
        "url":   "https://www.shutupandsitdown.com/feed/",
        "emoji": "🎙️",
    },
    {
        "name":  "Shut Up & Sit Down — Vídeos",
        "url":   "https://www.shutupandsitdown.com/feed/?post_type=videos",
        "emoji": "🎙️",
    },
    {
        "name":  "Shut Up & Sit Down — Reseñas de juegos",
        "url":   "https://www.shutupandsitdown.com/feed/?post_type=games",
        "emoji": "🎙️",
    },

    # ── BGG — foros por juego ───────────────────────────────────────────────
    # ID numérico de cada juego en BGG (en la URL de la página del juego)
    {
        "name":  "BGG — Oath",
        "url":   "https://boardgamegeek.com/rss/boardgame/291572/forums",
        "emoji": "🎲",
    },
    {
        "name":  "BGG — Root",
        "url":   "https://boardgamegeek.com/rss/boardgame/237182/forums",
        "emoji": "🎲",
    },
    {
        "name":  "BGG — Arcs",
        "url":   "https://boardgamegeek.com/rss/boardgame/341254/forums",
        "emoji": "🎲",
    },
    {
        "name":  "BGG — Pax Pamir",
        "url":   "https://boardgamegeek.com/rss/boardgame/256960/forums",
        "emoji": "🎲",
    },
    {
        "name":  "BGG — John Company",
        "url":   "https://boardgamegeek.com/rss/boardgame/332686/forums",
        "emoji": "🎲",
    },
    {
        "name":  "BGG — Ahoy",
        "url":   "https://boardgamegeek.com/rss/boardgame/338628/forums",
        "emoji": "🎲",
    },
    {
        "name":  "BGG — Infamous Traffic",
        "url":   "https://boardgamegeek.com/rss/boardgame/394240/forums",
        "emoji": "🎲",
    },

    # ── Kickstarter via Kicktraq ────────────────────────────────────────────────
    # Kicktraq genera RSS de Kickstarter por categoría (tabletop games)
    {
        "name":  "Kickstarter — Tabletop Games (nuevos)",
        "url":   "https://www.kicktraq.com/categories/tabletop-games/rss/",
        "emoji": "🚀",
    },
]

# ── Utilidades HTTP ───────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 15) -> bytes | None:
    """GET simple, devuelve bytes o None si falla."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:151.0) Gecko/20100101 Firefox/151.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        log.warning(f"Error fetching {url}: {e}")
        return None


def http_post_json(url: str, payload: dict, timeout: int = 30) -> dict | None:
    """POST JSON, devuelve dict o None si falla."""
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log.warning(f"Error posting to {url}: {e}")
        return None

# ── Parseo de fechas RSS/Atom ─────────────────────────────────────────────────

def parse_date(date_str: str) -> datetime | None:
    """Intenta parsear los formatos de fecha más comunes en feeds."""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",   # RFC 2822 (RSS)
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",         # ISO 8601 (Atom)
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def is_recent(date_str: str, days: int = DAYS_BACK) -> bool:
    """Comprueba si una fecha está dentro de la ventana de tiempo."""
    dt = parse_date(date_str)
    if dt is None:
        return True  # si no podemos parsear la fecha, incluimos el item
    # Normalizar a UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff

# ── Recolección de fuentes ────────────────────────────────────────────────────

def fetch_rss_items(feed: dict) -> list[dict]:
    """Descarga y parsea un feed RSS/Atom, devuelve items recientes."""
    raw = http_get(feed["url"])
    if not raw:
        return []

    items = []
    try:
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # Detectar formato: Atom o RSS
        is_atom = "Atom" in root.tag or root.tag == "{http://www.w3.org/2005/Atom}feed"

        if is_atom:
            entries = root.findall("atom:entry", ns) or root.findall("entry")
            for entry in entries:
                title   = (entry.findtext("atom:title", namespaces=ns)
                           or entry.findtext("title") or "")
                link_el = entry.find("atom:link", ns)
                if link_el is None:
                    link_el = entry.find("link")
                link    = link_el.get("href", "") if link_el is not None else ""
                date    = (entry.findtext("atom:updated", namespaces=ns)
                           or entry.findtext("atom:published", namespaces=ns)
                           or entry.findtext("updated")
                           or entry.findtext("published") or "")
                if is_recent(date):
                    items.append({
                        "source": feed["name"],
                        "emoji":  feed.get("emoji", "📰"),
                        "title":  title.strip(),
                        "link":   link,
                        "date":   date,
                    })
        else:
            # RSS 2.0
            for item in root.iter("item"):
                title = item.findtext("title") or ""
                link  = item.findtext("link")  or ""
                date  = item.findtext("pubDate") or ""
                if is_recent(date):
                    items.append({
                        "source": feed["name"],
                        "emoji":  feed.get("emoji", "📰"),
                        "title":  title.strip(),
                        "link":   link,
                        "date":   date,
                    })
    except ET.ParseError as e:
        log.warning(f"XML parse error for {feed['name']}: {e}")

    log.info(f"  {feed['name']}: {len(items)} items recientes")
    return items


def fetch_youtube_items(channel: dict) -> list[dict]:
    """Descarga el feed RSS nativo de YouTube para un canal."""
    url = (f"https://www.youtube.com/feeds/videos.xml"
           f"?channel_id={channel['id']}")
    return fetch_rss_items({
        "name":  f"YouTube — {channel['name']}",
        "url":   url,
        "emoji": "📺",
    })


def fetch_gamefound_items() -> list[dict]:
    """Gamefound no tiene API pública estable — función desactivada por ahora."""
    log.info("  Gamefound: desactivado (API sin documentación pública)")
    return []

# ── Resumen con Gemini ────────────────────────────────────────────────────────

# Modelos a probar en orden — si uno da 429 se prueba el siguiente
GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

PROMPT_TEMPLATE = """Eres el editor de una newsletter semanal en español para el grupo de Telegram "Oath España", un grupo de aficionados a los juegos de mesa de Leder Games y Buried Giant Studios (Oath, Root, Arcs, Pax Pamir, John Company, Ahoy).

Tu tarea es redactar un resumen semanal bien desarrollado basándote en la lista de contenidos recientes que te paso.

INSTRUCCIONES IMPORTANTES:
- Escribe SIEMPRE en español, tono cercano y entusiasta
- El resumen debe tener al menos 300 palabras aunque solo haya vídeos de YouTube
- Para cada vídeo de YouTube mencionado, describe brevemente de qué podría tratar basándote en el título
- Agrupa por secciones: 📺 Vídeos, 🎲 Foros y comunidad, 🚀 Crowdfunding (omite secciones vacías)
- Usa **negrita** con doble asterisco para títulos de secciones y nombres de juegos
- Enlaza los vídeos con formato HTML: <a href="URL">Título</a>
- NO inventes noticias ni campañas que no estén en la lista
- Termina siempre con: "📅 Próximo resumen: miércoles que viene"

CONTENIDOS DE ESTA SEMANA:
{items}
"""


def summarize_with_gemini(items: list[dict]) -> str | None:
    """Envía los titulares a Gemini y devuelve el resumen en texto.
    Prueba varios modelos en orden; reintenta una vez si hay 429."""
    if not items:
        return None

    # Formatear items para el prompt
    items_text = ""
    for item in items:
        items_text += f"[{item['source']}] {item['title']}"
        if item.get("link"):
            items_text += f" — {item['link']}"
        items_text += "\n"

    log.info(f"Items enviados a Gemini:\n{items_text}")
    prompt = PROMPT_TEMPLATE.format(items=items_text)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":    0.5,
            "maxOutputTokens": 4096,
        },
    }

    import time

    for model in GEMINI_MODELS:
        url = GEMINI_URL.format(model=model, key=GEMINI_API_KEY)
        log.info(f"Probando Gemini modelo: {model}...")

        for attempt in range(2):  # máx 2 intentos por modelo
            result = http_post_json(url, payload)

            if result is None:
                # http_post_json devuelve None en errores HTTP (incluido 429)
                if attempt == 0:
                    log.warning(f"  Fallo en {model}, reintentando en 10s...")
                    time.sleep(10)
                else:
                    log.warning(f"  {model} no disponible, probando siguiente modelo...")
                continue

            # Respuesta recibida — intentar parsear
            try:
                log.info(f"Respuesta cruda de Gemini: {json.dumps(result)[:500]}")
                candidate = result["candidates"][0]
                # Comprobar finish_reason
                finish = candidate.get("finishReason", "UNKNOWN")
                log.info(f"finishReason: {finish}")
                text = candidate["content"]["parts"][0]["text"]
                log.info(f"Gemini respondió con {model} ({len(text)} caracteres)")
                return text
            except (KeyError, IndexError) as e:
                log.error(f"Error parseando respuesta de {model}: {e}")
                log.error(f"Respuesta completa: {json.dumps(result)[:800]}")
            break

    log.error("Todos los modelos de Gemini fallaron.")
    return None

# ── Formateo para Telegram ────────────────────────────────────────────────────

def markdown_to_html(text: str) -> str:
    """Convierte **negrita** a HTML de Telegram."""
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def build_message(summary: str, item_count: int) -> str:
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    header = f"📰 <b>Resumen Semanal — Universo Leder Games</b>\n{today}\n\n"
    footer = f"\n\n<i>Fuentes consultadas esta semana: {item_count} titulares</i>"
    body   = markdown_to_html(summary)
    return header + body + footer

# ── Envío a Telegram ──────────────────────────────────────────────────────────

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def split_message(text: str, limit: int = 4000) -> list[str]:
    """Divide el texto en chunks respetando párrafos para no romper HTML."""
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""

    for paragraph in text.split("\n"):
        line = paragraph + "\n"
        if len(current) + len(line) > limit:
            if current:
                chunks.append(current.rstrip())
            current = line
        else:
            current += line

    if current.strip():
        chunks.append(current.rstrip())

    return chunks


def send_message(token: str, chat_id: str, text: str, thread_id: str = "") -> bool:
    """Envía un mensaje de texto HTML a Telegram, dividiendo por párrafos si es largo."""
    chunks = split_message(text)
    log.info(f"Enviando mensaje en {len(chunks)} parte/s...")

    for i, chunk in enumerate(chunks):
        params: dict = {
            "chat_id":    chat_id,
            "text":       chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
        if thread_id:
            params["message_thread_id"] = thread_id

        url = TELEGRAM_API.format(token=token, method="sendMessage")
        data = urllib.parse.urlencode(params).encode()
        req  = urllib.request.Request(url, data=data, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                if not result.get("ok"):
                    log.error(f"Telegram error (chunk {i+1}): {result.get('description')}")
                    log.error(f"Chunk problemático: {chunk[:200]}")
                    return False
        except Exception as e:
            log.error(f"Error enviando chunk {i+1}: {e}")
            return False

    log.info(f"Mensaje enviado correctamente ({len(chunks)} parte/s)")
    return True

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Validar config
    missing = [k for k, v in {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID":   TELEGRAM_CHAT_ID,
        "GEMINI_API_KEY":     GEMINI_API_KEY,
    }.items() if not v]

    if missing:
        log.error(f"Faltan variables de entorno: {', '.join(missing)}")
        sys.exit(1)

    all_items: list[dict] = []

    # 1. YouTube
    log.info("Recopilando YouTube...")
    for channel in YOUTUBE_CHANNELS:
        all_items.extend(fetch_youtube_items(channel))

    # 2. RSS / Atom feeds
    log.info("Recopilando RSS feeds...")
    for feed in RSS_FEEDS:
        all_items.extend(fetch_rss_items(feed))

    # 3. Gamefound
    log.info("Recopilando Gamefound...")
    all_items.extend(fetch_gamefound_items())

    log.info(f"Total items recopilados: {len(all_items)}")

    # 4. Si no hay ningún item, no hay nada que resumir ni enviar
    if not all_items:
        log.info("Sin items esta semana — no se envía nada.")
        return

    # 5. Resumen con Gemini
    summary = summarize_with_gemini(all_items)

    # Si Gemini no devuelve nada o indica que no hay novedades, no enviamos
    if not summary:
        log.info("Gemini no devolvió resumen — no se envía nada.")
        return

    if "no hay novedades" in summary.lower() or "no se han encontrado" in summary.lower():
        log.info("Gemini indica que no hay novedades relevantes — no se envía nada.")
        return

    # 6. Enviar a Telegram
    message = build_message(summary, len(all_items))
    ok = send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message, TELEGRAM_THREAD_ID)

    if not ok:
        log.error("Fallo al enviar el mensaje")
        sys.exit(1)

    log.info("✅ Digest semanal enviado correctamente")


if __name__ == "__main__":
    main()
