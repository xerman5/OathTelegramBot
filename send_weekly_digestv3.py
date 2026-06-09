"""
send_weekly_digestv2.py (Versión 9 - Expansión de Fuentes & Worker Ciego)
-------------------------------------------------------------------------
El Cloudflare Worker actúa únicamente como túnel de red (dumb proxy) 
para evadir bloqueos 403/400. Toda la lógica de extracción, scrapeo 
y parseo de BGG, Reddit, Kickstarter y Backerkit reside en Python.
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

# Ajustado a 7 días: Con las nuevas fuentes, habrá suficiente volumen semanal
DAYS_BACK = 7  
CLOUDFLARE_WORKER_URL = "https://square-term-7f74.xermanpl.workers.dev"

# ── Catálogo de Fuentes ───────────────────────────────────────────────────────
YOUTUBE_CHANNELS = [
    {"name": "Buried Giant Studios", "id": "UC0MIABBBLK0YETRMWEDmWDA"},
    {"name": "Leder Games",          "id": "UCjea2nM_6W-zGOxk22mXkIg"},
    {"name": "Shut Up & Sit Down",   "id": "UCyRhIGDUKdIOw07Pd8pHxCw"},
]

# Webs estándar que soportan bien el RSS puro
RSS_STANDARD = [
    {"name": "Leder Games Blog", "url": "https://feeds.feedburner.com/LederGames", "proxy": False},
    {"name": "Buried Giant Blog", "url": "https://buriedgiant.com/rss.xml", "proxy": False},
    {"name": "SUSD - Artículos", "url": "https://www.shutupandsitdown.com/feed/", "proxy": True},
    {"name": "SUSD - Vídeos", "url": "https://www.shutupandsitdown.com/feed/?post_type=videos", "proxy": True},
    {"name": "SUSD - Reseñas", "url": "https://www.shutupandsitdown.com/feed/?post_type=games", "proxy": True},
]

# Comunidades de Reddit (vía RSS)
REDDIT_FEEDS = [
    {"name": "Reddit r/Arcs", "url": "https://www.reddit.com/r/Arcs/new/.rss"},
    {"name": "Reddit r/rootgame", "url": "https://www.reddit.com/r/rootgame/new/.rss"},
    {"name": "Reddit r/oathgame", "url": "https://www.reddit.com/r/oathgame/new/.rss"},
    # Búsqueda global en r/boardgames restringida a palabras clave exactas
    {"name": "Reddit r/boardgames", "url": 'https://www.reddit.com/r/boardgames/search.rss?q=title:(oath+OR+ahoy+OR+leder+OR+"buried+giant"+OR+root+OR+arcs+OR+"john+company"+OR+"cole+wehrle"+OR+"patrick+leder"+OR+"kyle+ferrin")&sort=new&restrict_sr=on'}
]

# BoardGameGeek (IDs de Juegos)
BGG_FEEDS = [
    {"name": "BGG Oath: NF", "url": "https://boardgamegeek.com/rss/boardgame/420719/forums"},
    {"name": "BGG Oath", "url": "https://boardgamegeek.com/rss/boardgame/291572/forums"},
    {"name": "BGG Arcs: Blighted", "url": "https://boardgamegeek.com/rss/boardgame/363757/forums"},
    {"name": "BGG Arcs: Beyond", "url": "https://boardgamegeek.com/rss/boardgame/468035/forums"},
    {"name": "BGG Ahoy", "url": "https://boardgamegeek.com/rss/boardgame/359402/forums"},
]

# Crowdfunding (Canales ocultos Atom)
KICKSTARTER_FEEDS = [
    {"name": "KS Cole Wehrle (Actividad)", "url": "https://www.kickstarter.com/profile/colewehrle/activity.atom"},
    {"name": "KS Patrick Leder (Actividad)", "url": "https://www.kickstarter.com/profile/ledergames/activity.atom"},
    {"name": "KS Arcs Beyond (Updates)", "url": "https://www.kickstarter.com/projects/colewehrle/arcs-beyond-the-reach/posts.atom"},
    {"name": "KS Oath NF (Updates)", "url": "https://www.kickstarter.com/projects/ledergames/oath-new-foundations/posts.atom"},
]

# Webs HTML (Requieren Regex, no RSS)
BACKERKIT_PAGES = [
    {"name": "Backerkit Ahoy", "url": "https://www.backerkit.com/c/projects/leder-games/ahoy-its-a-whale-of-an-expansion/updates"}
]

# ── Utilidades HTTP ───────────────────────────────────────────────────────────
def http_get(url: str, use_proxy: bool = True, timeout: int = 15) -> bytes | None:
    """Envía la petición a través del Worker pasivo si use_proxy es True."""
    target_url = f"{CLOUDFLARE_WORKER_URL}/?url={urllib.parse.quote_plus(url)}" if use_proxy else url
    
    try:
        req = urllib.request.Request(
            target_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        log.warning(f"Error fetching {url} (Proxy: {use_proxy}): {e}")
        return None

def http_post_json(url: str, payload: dict, timeout: int = 30) -> dict | None:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        log.warning(f"Error posting to Gemini: {e}")
        return None

# ── Parseo de Fechas y Nodos ──────────────────────────────────────────────────
def parse_date(date_str: str) -> datetime | None:
    if not date_str: return None
    formats = ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%SZ"]
    for fmt in formats:
        try: return datetime.strptime(date_str.strip(), fmt)
        except ValueError: continue
    return None

def is_recent(date_str: str, days: int = DAYS_BACK) -> bool:
    dt = parse_date(date_str)
    if dt is None: return True
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)

def get_node_text(element, tags, ns=None) -> str:
    for tag in tags:
        el = element.find(tag, ns) if ns and ":" in tag else element.find(tag)
        if el is not None and el.text: return el.text.strip()
    return ""

def get_node_link(element, tags, ns=None) -> str:
    for tag in tags:
        els = element.findall(tag, ns) if ns and ":" in tag else element.findall(tag)
        for el in els:
            href = el.get("href")
            if href: return href
            if el.text and "http" in el.text: return el.text.strip()
    return ""

# ── Extractores de Datos (Lógica en Python) ───────────────────────────────────
def fetch_rss_items(feed: dict, use_proxy: bool = True) -> list[dict]:
    raw = http_get(feed["url"], use_proxy=use_proxy)
    if not raw: return []
    items = []
    try:
        xml_str = raw.decode("utf-8", errors="ignore")
        xml_str = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#[0-9]+;)", "&amp;", xml_str)
        xml_str = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", xml_str)
        
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
        log.warning(f"XML parse error for {feed['name']}")
    
    log.info(f"  {feed['name']}: {len(items)} items recientes")
    return items

def fetch_youtube_items(channel: dict) -> list[dict]:
    return fetch_rss_items({"name": f"YouTube — {channel['name']}", "url": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel['id']}"}, use_proxy=False)

def fetch_backerkit_items(page: dict) -> list[dict]:
    """Scrapea HTML puro de Backerkit mediante Expresiones Regulares en Python"""
    raw = http_get(page["url"], use_proxy=True)
    if not raw: return []
    items = []
    
    html_str = raw.decode("utf-8", errors="ignore")
    # Busca enlaces que lleven a la carpeta de updates
    pattern = r'href="(/c/projects/[^"]+/updates/\d+)".*?>(.*?)</a>'
    matches = re.findall(pattern, html_str, re.IGNORECASE | re.DOTALL)
    
    # Extraer los 2 más recientes (para no saturar si no hay fechas precisas)
    for match in matches[:2]:
        link_path, title_raw = match
        # Limpiar HTML dentro del título si lo hay
        clean_title = re.sub(r'<[^>]+>', '', title_raw).strip()
        if clean_title:
            full_link = f"https://www.backerkit.com{link_path}"
            items.append({"source": page["name"], "title": f"Update: {clean_title}", "link": full_link})
            
    log.info(f"  {page['name']}: {len(items)} items extraídos (HTML Parser)")
    return items

# ── Resumen con Gemini ────────────────────────────────────────────────────────
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT_TEMPLATE = """Eres el redactor del resumen semanal de novedades del ecosistema de Leder Games (Oath, Arcs, Root, Ahoy...) para el canal de Telegram "Oath España".

REGLAS DE FORMATO ESTRICTAS:
1. Omite cualquier introducción. Ve directamente a las novedades.
2. La primera línea debe ser exactamente: "Resumen de la semana de **Oath**, **Arcs**, **Root** y compañía:"
3. Organiza los contenidos usando subtítulos limpios (ej: ### BGG y Reddit, ### Crowdfunding, ### Novedades Oficiales).
4. Cada viñeta debe usar obligatoriamente un guion simple (`-`) y este formato estricto:
   - [Título descriptivo](URL): Breve comentario sobre lo que trata.
5. REGLA DEL EMOJI: Si la fuente original del elemento empieza por "YouTube — ", pon el emoji 🎦 justo antes del enlace. Ejemplo:
   - 🎦 [Vídeo Gameplay](URL): Breve descripción.
   (No uses el emoji para Reddit, BGG o Kickstarter).
6. Consolida temas repetidos (ej. si hay 5 hilos de BGG sobre dudas de Arcs, resúmelos en 1 o 2 viñetas clave).
7. NUNCA utilices etiquetas HTML. Usa Markdown estándar.
8. Termina con: "📅 Próximo resumen: miércoles que viene"

LISTA DE ENLACES DE ESTA SEMANA (USA LAS URLs PROVISTAS):
{items}
"""

def summarize_with_gemini(items: list[dict]) -> str | None:
    if not items: return None
    
    items_text = "\n".join([f"[{i['source']}] {i['title']} — {i['link']}" for i in items])
    
    payload = {
        "contents": [{"parts": [{"text": PROMPT_TEMPLATE.format(items=items_text)}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192}
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
                log.info(f"Gemini respondió con éxito ({len(text)} caracteres)")
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
    log.info(f"Enviando mensaje a Telegram...")
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
    for feed in YOUTUBE_CHANNELS: all_items.extend(fetch_youtube_items(feed))
    
    log.info("Recopilando RSS Estándar...")
    for feed in RSS_STANDARD: all_items.extend(fetch_rss_items(feed, use_proxy=feed.get("proxy", True)))
    
    log.info("Recopilando Subreddits...")
    for feed in REDDIT_FEEDS: all_items.extend(fetch_rss_items(feed, use_proxy=True))
    
    log.info("Recopilando BGG...")
    for feed in BGG_FEEDS: all_items.extend(fetch_rss_items(feed, use_proxy=True))
        
    log.info("Recopilando Kickstarter...")
    for feed in KICKSTARTER_FEEDS: all_items.extend(fetch_rss_items(feed, use_proxy=True))
        
    log.info("Recopilando Backerkit (HTML)...")
    for page in BACKERKIT_PAGES: all_items.extend(fetch_backerkit_items(page))

    log.info(f"Total items recopilados (Últimos 7 días): {len(all_items)}")
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
