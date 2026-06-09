"""
send_weekly_digestv2.py (Versión 7 - Token Limit & BGG Proxy Fix)
------------------------------------------------------------------
Soluciona el truncado liberando el límite máximo de tokens de salida.
Devuelve BGG a CodeTabs con saneamiento de strings y compacta el prompt.
"""

import json
import logging
import os
import re
import sys
import time
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

DAYS_BACK = 30  # Ventana de tiempo en días
CLOUDFLARE_WORKER_URL = "https://square-term-7f74.xermanpl.workers.dev"

# ── Fuentes ───────────────────────────────────────────────────────────────────
YOUTUBE_CHANNELS = [
    {"name": "Buried Giant Studios", "id": "UC0MIABBBLK0YETRMWEDmWDA"},
    {"name": "Leder Games",          "id": "UCjea2nM_6W-zGOxk22mXkIg"},
    {"name": "Shut Up & Sit Down",   "id": "UCyRhIGDUKdIOw07Pd8pHxCw"},
]

RSS_FEEDS = [
    {"name": "Leder Games — Blog", "url": "https://feeds.feedburner.com/LederGames"},
    {"name": "Buried Giant Studios — Blog", "url": "https://buriedgiant.com/rss.xml"},
    {"name": "Shut Up & Sit Down — Artículos", "url": "https://www.shutupandsitdown.com/feed/"},
    {"name": "Shut Up & Sit Down — Vídeos", "url": "https://www.shutupandsitdown.com/feed/?post_type=videos"},
    {"name": "Shut Up & Sit Down — Reseñas", "url": "https://www.shutupandsitdown.com/feed/?post_type=games"},
    {"name": "BGG — Oath", "url": "https://boardgamegeek.com/rss/boardgame/291572/forums"},
    {"name": "BGG — Root", "url": "https://boardgamegeek.com/rss/boardgame/237182/forums"},
    {"name": "BGG — Arcs", "url": "https://boardgamegeek.com/rss/boardgame/341254/forums"},
    {"name": "BGG — Pax Pamir", "url": "https://boardgamegeek.com/rss/boardgame/256960/forums"},
    {"name": "BGG — John Company", "url": "https://boardgamegeek.com/rss/boardgame/332686/forums"},
    {"name": "BGG — Ahoy", "url": "https://boardgamegeek.com/rss/boardgame/338628/forums"},
    {"name": "BGG — Infamous Traffic", "url": "https://boardgamegeek.com/rss/boardgame/394240/forums"},
    {"name": "Kickstarter — Tabletop Games", "url": "https://www.kicktraq.com/categories/tabletop-games/rss/"},
]

# ── Utilidades HTTP ───────────────────────────────────────────────────────────
def http_get(url: str, timeout: int = 15) -> bytes | None:
    target_url = url
    
    # Enrutar SUSD al Cloudflare Worker privado
    if "shutupandsitdown.com" in url:
        target_url = f"{CLOUDFLARE_WORKER_URL}/?url={urllib.parse.quote_plus(url)}"
        log.info(f"Enrutando via Cloudflare Worker: {url}")
    # Enrutar BGG y Kickstarter a CodeTabs (Cloudflare da 403 en BGG)
    elif "boardgamegeek.com" in url or "kicktraq.com" in url:
        target_url = f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote_plus(url)}"
        log.info(f"Enrutando via CodeTabs Proxy: {url}")

    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        log.warning(f"Error fetching {url}: {e}")
        return None

def http_post_json(url: str, payload: dict, timeout: int = 30) -> dict | None:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log.warning(f"Error posting to {url}: {e}")
        return None

# ── Parseo de fechas RSS/Atom ─────────────────────────────────────────────────
def parse_date(date_str: str) -> datetime | None:
    if not date_str: return None
    formats = ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]
    for fmt in formats:
        try: return datetime.strptime(date_str.strip(), fmt)
        except ValueError: continue
    return None

def is_recent(date_str: str, days: int = DAYS_BACK) -> bool:
    dt = parse_date(date_str)
    if dt is None: return True
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)

# ── Extracción XML Segura ─────────────────────────────────────────────────────
def get_node_text(element, tags, ns=None) -> str:
    for tag in tags:
        el = element.find(tag, ns) if ns and ":" in tag else element.find(tag)
        if el is not None and el.text:
            return el.text.strip()
    return ""

def get_node_link(element, tags, ns=None) -> str:
    for tag in tags:
        els = element.findall(tag, ns) if ns and ":" in tag else element.findall(tag)
        for el in els:
            href = el.get("href")
            if href: return href
            if el.text and "http" in el.text: return el.text.strip()
    return ""

def fetch_rss_items(feed: dict) -> list[dict]:
    raw = http_get(feed["url"])
    if not raw: return []
    items = []
    try:
        # Sanear caracteres '&' sueltos que rompen BGG en proxies públicos
        xml_str = raw.decode("utf-8", errors="ignore")
        xml_str = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#[0-9]+;)", "&amp;", xml_str)
        
        root = ET.fromstring(xml_str)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        if "Atom" in root.tag or root.tag == "{http://www.w3.org/2005/Atom}feed":
            entries = root.findall("atom:entry", ns) or root.findall("entry")
            for entry in entries:
                title = get_node_text(entry, ["atom:title", "{http://www.w3.org/2005/Atom}title", "title"], ns)
                link = get_node_link(entry, ["atom:link", "{http://www.w3.org/2005/Atom}link", "link"], ns)
                date = get_node_text(entry, ["atom:updated", "atom:published", "updated"], ns)
                if title and link and is_recent(date):
                    items.append({"source": feed["name"], "title": title, "link": link})
        else:
            for item in root.iter("item"):
                title = get_node_text(item, ["title"])
                link = get_node_link(item, ["link"])
                date = get_node_text(item, ["pubDate", "date"])
                if title and link and is_recent(date):
                    items.append({"source": feed["name"], "title": title, "link": link})
                    
    except ET.ParseError as e:
        log.warning(f"XML parse error for {feed['name']}: {e}")
    
    log.info(f"  {feed['name']}: {len(items)} items recientes")
    return items

def fetch_youtube_items(channel: dict) -> list[dict]:
    return fetch_rss_items({"name": f"YouTube — {channel['name']}", "url": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel['id']}"})

# ── Resumen con Gemini ────────────────────────────────────────────────────────
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT_TEMPLATE = """Eres un asistente encargado de resumir las novedades semanales del ecosistema de Leder Games (Oath, Arcs, Root, Vast, Ahoy...) para el canal de Telegram "Oath España".

REGLAS DE FORMATO ESTRICTAS:
1. No incluyas saludos, introducciones ni textos aclaratorios. Empieza directamente con el contenido.
2. La primera línea debe ser exactamente: "Resumen de la semana de **Oath**, **Arcs**, **Root** y compañía:"
3. Organiza los contenidos en una lista limpia agrupada por juegos o temáticas (ej: **Arcs**, **Root**, **Otros juegos** o **Shut Up & Sit Down**). Usa subtítulos simples si lo consideras necesario.
4. Cada viñeta debe usar obligatoriamente un guion simple (`-`) y este formato:
   - [Título adaptado o claro](URL): Breve descripción de una línea sobre lo que trata.
5. Agrupa o consolida elementos si detectas múltiples vídeos de diarios de desarrollo o hilos redundantes del mismo tema, de forma que el boletín sea conciso pero incluya la información esencial.
6. NUNCA utilices etiquetas HTML como <a> o <b>. Usa únicamente Markdown estándar.
7. Termina el boletín con la línea exacta: "📅 Próximo resumen: miércoles que viene"

LISTA DE ENLACES DISPONIBLES (USA LAS URLs PROVISTAS AL FINAL DE CADA LÍNEA):
{items}
"""

def summarize_with_gemini(items: list[dict]) -> str | None:
    if not items: return None
    
    items_text = "\n".join([f"[{i['source']}] {i['title']} — {i['link']}" for i in items])
    
    payload = {
        "contents": [{"parts": [{"text": PROMPT_TEMPLATE.format(items=items_text)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192  # CRÍTICO: Soluciona el error MAX_TOKENS aumentando el límite al máximo
        }
    }

    for model in GEMINI_MODELS:
        url = GEMINI_URL.format(model=model, key=GEMINI_API_KEY)
        log.info(f"Probando Gemini modelo: {model}...")
        for attempt in range(2):
            result = http_post_json(url, payload)
            if not result:
                time.sleep(3)
                continue
            try:
                candidate = result["candidates"][0]
                parts = candidate.get("content", {}).get("parts", [])
                text = "".join([p.get("text", "") for p in parts])
                reason = candidate.get("finishReason", "UNKNOWN")
                
                log.info(f"Gemini respondió con éxito ({len(text)} caracteres). FinReason: {reason}")
                return text
            except (KeyError, IndexError) as e:
                log.error(f"Error parseando respuesta de Gemini: {e}")
                time.sleep(3)
                continue
    return None

# ── Formateo Blindado para Telegram ───────────────────────────────────────────
def markdown_to_html(text: str) -> str:
    if not text: return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text

def build_message(summary: str, item_count: int) -> str:
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    header = f"📰 <b>Resumen Semanal — Universo Leder Games</b>\n{today}\n\n"
    footer = f"\n\n<i>Fuentes consultadas esta semana: {item_count} titulares</i>"
    body   = markdown_to_html(summary)
    return header + body + footer

def send_message(token: str, chat_id: str, text: str, thread_id: str = "") -> bool:
    log.info(f"Enviando mensaje final a Telegram...")
    params = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}
    if thread_id: params["message_thread_id"] = thread_id
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=urllib.parse.urlencode(params).encode(), method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read())
            return res.get("ok", False)
    except Exception as e:
        log.error(f"Error enviando a Telegram: {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY]):
        log.error("Faltan variables de entorno esenciales.")
        sys.exit(1)

    all_items = []
    log.info("Recopilando YouTube...")
    for channel in YOUTUBE_CHANNELS: all_items.extend(fetch_youtube_items(channel))
    log.info("Recopilando RSS feeds...")
    for feed in RSS_FEEDS: all_items.extend(fetch_rss_items(feed))

    log.info(f"Total items recopilados: {len(all_items)}")
    if not all_items: return

    summary = summarize_with_gemini(all_items)
    if not summary: return

    ok = send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, build_message(summary, len(all_items)), TELEGRAM_THREAD_ID)
    if not ok:
        log.error("Fallo definitivo al enviar a Telegram")
        sys.exit(1)
    log.info("✅ Digest semanal enviado correctamente")

if __name__ == "__main__":
    main()
