"""
send_weekly_digestv2.py (Versión 3 - Antispam & Estructura Forzada)
------------------------------------------------------------------
Recopila novedades semanales del universo Leder Games / Buried Giant,
las resume con Gemini mediante una plantilla estricta y publica en Telegram.
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

# Tu URL de Cloudflare Worker
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
    
    if "shutupandsitdown.com" in url:
        target_url = f"{CLOUDFLARE_WORKER_URL}/?url={urllib.parse.quote_plus(url)}"
        log.info(f"Enrutando via Cloudflare Worker: {url}")
        
    elif "boardgamegeek.com" in url or "kicktraq.com" in url:
        # Cambiado a CodeTabs Proxy para evitar el bloqueo que sufrió AllOrigins
        target_url = f"https://api.codetabs.com/v1/proxy/?quest={urllib.parse.quote_plus(url)}"
        log.info(f"Enrutando via CodeTabs Proxy: {url}")

    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"},
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
    formats = ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f%z"]
    for fmt in formats:
        try: return datetime.strptime(date_str.strip(), fmt)
        except ValueError: continue
    return None

def is_recent(date_str: str, days: int = DAYS_BACK) -> bool:
    dt = parse_date(date_str)
    if dt is None: return True
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)

# ── Recolección de fuentes ────────────────────────────────────────────────────
def fetch_rss_items(feed: dict) -> list[dict]:
    raw = http_get(feed["url"])
    if not raw: return []
    items = []
    try:
        root = ET.fromstring(raw)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        
        if "Atom" in root.tag or root.tag == "{http://www.w3.org/2005/Atom}feed":
            entries = root.findall("atom:entry", ns)
            if not entries:
                entries = root.findall("entry")
            for entry in entries:
                title = (entry.findtext("atom:title", namespaces=ns) or entry.findtext("title") or "").strip()
                link_el = entry.find("atom:link", ns)
                if link_el is None:
                    link_el = entry.find("link")
                link = link_el.get("href", "") if link_el is not None else ""
                date = (entry.findtext("atom:updated", namespaces=ns) or entry.findtext("atom:published", namespaces=ns) or entry.findtext("updated") or "")
                if is_recent(date): items.append({"source": feed["name"], "title": title, "link": link})
        else:
            for item in root.iter("item"):
                title = (item.findtext("title") or "").strip()
                link = item.findtext("link") or ""
                date = item.findtext("pubDate") or ""
                if is_recent(date): items.append({"source": feed["name"], "title": title, "link": link})
    except ET.ParseError as e:
        log.warning(f"XML parse error for {feed['name']}: {e}")
    
    log.info(f"  {feed['name']}: {len(items)} items recientes")
    return items

def fetch_youtube_items(channel: dict) -> list[dict]:
    return fetch_rss_items({"name": f"YouTube — {channel['name']}", "url": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel['id']}"})

# ── Resumen con Gemini ────────────────────────────────────────────────────────
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# PROMPT REDISEÑADO CON ESTRUCTURA MILITAR EXPLICITA
PROMPT_TEMPLATE = """Eres el redactor oficial de la newsletter semanal en español para el canal de Telegram "Oath España". Tu comunidad está compuesta por fans apasionados de los juegos de mesa de **Leder Games** y **Buried Giant Studios** (Oath, Root, Arcs, Pax Pamir, etc.).

Tu objetivo es leer la lista de contenidos recientes provista al final y redactar un boletín informativo EXTENSO, con cuerpo, estructurado y muy entusiasta. No resumas todo en un párrafo genérico.

DEBES SEGUIR ESTA ESTRUCTURA OBLIGATORIA PASO A PASO:

1. **Introducción**: Un saludo cercano y emocionante adaptado a la comunidad de estrategas de Oath España.
2. **📺 SECCIÓN VÍDEOS Y DIARIOS DE DISEÑO**: Analiza los vídeos de YouTube provistos. Habla extensamente sobre el final de la campaña de Kickstarter de **Arcs: Beyond the Reach**, los diarios de diseño de **Buried Giant**, las charlas de estudio de **Leder Games** y el contenido reciente de **Shut Up & Sit Down** (menciona especialmente su reseña de 'Dirt & Dust'). Agrupa los vídeos por temáticas comunes y redacta párrafos descriptivos para cada una.
3. **🎲 SECCIÓN COMUNIDAD Y FOROS**: Si en la lista ves hilos de BoardGameGeek (BGG), coméntalos. Si no aparecen hilos esta semana, haz una sección breve animando a los miembros del grupo a pasarse por los foros de BGG a generar debate sobre las expansiones de **Root** o las crónicas de **Oath**.
4. **Cierre**: Termina OBLIGATORIAMENTE con la frase exacta: "📅 Próximo resumen: miércoles que viene"

NORMAS DE FORMATO ESTRICTAS:
- Escribe completamente en español.
- Usa **negrita** con doble asterisco para resaltar los nombres de juegos y canales de contenido.
- Para todos los enlaces que uses, emplea estrictamente el formato Markdown: [Título del Vídeo/Artículo](URL). No dejes URLs sueltas.
- PROHIBICIÓN ABSOLUTA: No generes ninguna etiqueta HTML (como <a>, <b>, <br>).
- Sé generoso en la extensión de los párrafos explicativos. No te dejes contenidos importantes fuera.

LISTA DE CONTENIDOS DISPONIBLES ESTA SEMANA:
{items}
"""

def summarize_with_gemini(items: list[dict]) -> str | None:
    if not items: return None
    
    items_text = "\n".join([f"[{i['source']}] {i['title']} — {i['link']}" for i in items])
    log.info(f"Items enviados a Gemini:\n{items_text}")
    
    payload = {
        "contents": [{"parts": [{"text": PROMPT_TEMPLATE.format(items=items_text)}]}],
        # Temperatura bajada a 0.2 para evitar que la IA divague o recorte el texto a su antojo
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}
    }

    for model in GEMINI_MODELS:
        url = GEMINI_URL.format(model=model, key=GEMINI_API_KEY)
        log.info(f"Probando Gemini modelo: {model}...")
        for attempt in range(2):
            result = http_post_json(url, payload)
            if not result:
                time.sleep(5)
                continue
            try:
                candidate = result["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]
                log.info(f"Gemini respondió con éxito usando {model} ({len(text)} caracteres)")
                return text
            except (KeyError, IndexError) as e:
                log.error(f"Error parseando respuesta de {model}: {e}")
                continue
    return None

# ── Formateo Blindado para Telegram ───────────────────────────────────────────
def markdown_to_html(text: str) -> str:
    if not text: return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\[(.+?)\]\((https?://.+?)\)", r'<a href="\2">\1</a>', text)
    return text

def build_message(summary: str, item_count: int) -> str:
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    header = f"📰 <b>Resumen Semanal — Universo Leder Games</b>\n{today}\n\n"
    footer = f"\n\n<i>Fuentes consultadas esta semana: {item_count} titulares</i>"
    body   = markdown_to_html(summary)
    return header + body + footer

def split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit: return [text]
    chunks, current = [], ""
    for paragraph in text.split("\n"):
        line = paragraph + "\n"
        if len(current) + len(line) > limit:
            if current: chunks.append(current.rstrip())
            current = line
        else:
            current += line
    if current.strip(): chunks.append(current.rstrip())
    return chunks

def send_message(token: str, chat_id: str, text: str, thread_id: str = "") -> bool:
    chunks = split_message(text)
    log.info(f"Enviando mensaje en {len(chunks)} parte/s...")
    for i, chunk in enumerate(chunks):
        params = {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML", "disable_web_page_preview": "true"}
        if thread_id: params["message_thread_id"] = thread_id
        try:
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=urllib.parse.urlencode(params).encode(), method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read())
                if not res.get("ok"): return False
        except Exception as e:
            log.error(f"Error enviando chunk {i+1}: {e}")
            return False
    return True

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY]):
        log.error("Faltan variables de entorno")
        sys.exit(1)

    all_items = []
    log.info("Recopilando YouTube...")
    for channel in YOUTUBE_CHANNELS: all_items.extend(fetch_youtube_items(channel))
    log.info("Recopilando RSS feeds...")
    for feed in RSS_FEEDS: all_items.extend(fetch_rss_items(feed))

    log.info(f"Total items recopilados: {len(all_items)}")
    if not all_items: return

    summary = summarize_with_gemini(all_items)
    if not summary or "no hay novedades" in summary.lower(): return

    ok = send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, build_message(summary, len(all_items)), TELEGRAM_THREAD_ID)
    if not ok:
        log.error("Fallo definitivo al enviar el mensaje")
        sys.exit(1)
    log.info("✅ Digest semanal enviado correctamente")

if __name__ == "__main__":
    main()
