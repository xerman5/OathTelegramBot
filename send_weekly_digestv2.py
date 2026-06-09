"""
send_weekly_digest.py
---------------------
Recopila novedades semanales del universo Leder Games / Buried Giant,
las resume con Gemini y las publica en Telegram.

Ejecutado cada miércoles desde GitHub Actions.
Sin dependencias externas — solo stdlib de Python 3.12.

Variables de entorno (GitHub Secrets):
    TELEGRAM_BOT_TOKEN   — token del bot
    TELEGRAM_CHAT_ID     — ej: "@oathespana"
    TELEGRAM_THREAD_ID   — topic del grupo (ej: 143)
    GEMINI_API_KEY       — Google AI Studio
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

# ── ESTRATEGIA CONTRA BLOQUEOS 403 (GitHub Actions IPs) ────────────────────────
# Opción A: Proxy público gratuito (corsproxy.io). Envuelve la URL original.
# Opción B: Si la Opción A falla en el futuro porque saturan el proxy, cambia esto a False
#           e implementa tu propio Cloudflare Worker (se detalla al final del archivo).
USE_PROXY_OPTION_A = True 

# ── Fuentes ───────────────────────────────────────────────────────────────────

YOUTUBE_CHANNELS = [
    {"name": "Buried Giant Studios", "id": "UC0MIABBBLK0YETRMWEDmWDA"},
    {"name": "Leder Games",          "id": "UCjea2nM_6W-zGOxk22mXkIg"},
    {"name": "Shut Up & Sit Down",   "id": "UCyRhIGDUKdIOw07Pd8pHxCw"},
]

RSS_FEEDS = [
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
    {
        "name":  "Kickstarter — Tabletop Games (nuevos)",
        "url":   "https://www.kicktraq.com/categories/tabletop-games/rss/",
        "emoji": "🚀",
    },
]

# ── Utilidades HTTP ───────────────────────────────────────────────────────────

def http_get(url: str, timeout: int = 15) -> bytes | None:
    """GET simple que aplica Opción A (Proxy) para evadir el bloqueo 403 de Cloudflare."""
    target_url = url
    
    # Aplicar el proxy de la Opción A solo a dominios conflictivos con las IPs de GitHub
    if USE_PROXY_OPTION_A and any(domain in url for domain in ["boardgamegeek.com", "shutupandsitdown.com", "kicktraq.com"]):
        target_url = f"https://corsproxy.io/?{urllib.parse.quote_plus(url)}"
        log.info(f"Enrutando via Proxy (Opción A): {url}")

    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"},
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
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
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
        return True
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
        is_atom = "Atom" in root.tag or root.tag == "{http://www.w3.org/2005/Atom}feed"

        if is_atom:
            entries = root.findall("atom:entry", ns) or root.findall("entry")
            for entry in entries:
                title   = (entry.findtext("atom:title", namespaces=ns) or entry.findtext("title") or "")
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
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel['id']}"
    return fetch_rss_items({
        "name":  f"YouTube — {channel['name']}",
        "url":   url,
        "emoji": "📺",
    })

# ── Resumen con Gemini ────────────────────────────────────────────────────────

# Reordenados priorizando los modelos estables más eficientes y con mayor ventana de contexto real
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

# PROMPT MODIFICADO: Se le prohíbe taxativamente generar código HTML para evitar roturas de tags.
PROMPT_TEMPLATE = """Eres el editor de una newsletter semanal en español para el grupo de Telegram "Oath España", un grupo de aficionados a los juegos de mesa de Leder Games y Buried Giant Studios (Oath, Root, Arcs, Pax Pamir, John Company, Ahoy).

Tu tarea es redactar un resumen semanal bien desarrollado basándote en la lista de contenidos recientes que te paso.

INSTRUCCIONES IMPORTANTES:
- Escribe SIEMPRE en español, con un tono cercano, dinámico y entusiasta.
- El resumen debe tener sustancia y desarrollo (un buen cuerpo de texto explicativo).
- Para cada vídeo o artículo mencionado, describe o conjetura brevemente de qué trata basándote en el título.
- Agrupa obligatoriamente la información por secciones claras usando emojis: 📺 Vídeos, 🎲 Foros y Comunidad, 🚀 Crowdfunding (omite las secciones que no tengan contenidos).
- Usa **negrita** con doble asterisco para los títulos de secciones y nombres propios de juegos de mesa.
- FORMATO DE ENLACES OBLIGATORIO: Enlaza los vídeos y fuentes usando única y exclusivamente el formato Markdown estándar: [Título descriptivo del vídeo o post](URL).
- PROHIBICIÓN ABSOLUTA: NO escribas ninguna etiqueta HTML (como <a>, <b>, <br>). El formateo a HTML seguro lo hará mi sistema interno. Si pones HTML, el sistema fallará.
- No inventes noticias ni campañas que no aparezcan de forma explícita en la lista.
- Termina siempre con la coletilla exacta: "📅 Próximo resumen: miércoles que viene"

CONTENIDOS DE ESTA SEMANA:
{items}
"""


def summarize_with_gemini(items: list[dict]) -> str | None:
    if not items:
        return None

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
            "temperature": 0.4,
            "maxOutputTokens": 2048,
        },
    }

    for model in GEMINI_MODELS:
        url = GEMINI_URL.format(model=model, key=GEMINI_API_KEY)
        log.info(f"Probando Gemini modelo: {model}...")

        for attempt in range(2):
            result = http_post_json(url, payload)

            if result is None:
                if attempt == 0:
                    log.warning(f"  Fallo en {model}, reintentando en 5s...")
                    time.sleep(5)
                else:
                    log.warning(f"  {model} no disponible, saltando al siguiente modelo...")
                continue

            try:
                candidate = result["candidates"][0]
                finish = candidate.get("finishReason", "UNKNOWN")
                log.info(f"finishReason de Gemini: {finish}")
                
                text = candidate["content"]["parts"][0]["text"]
                log.info(f"Gemini respondió con éxito usando {model} ({len(text)} caracteres)")
                return text
            except (KeyError, IndexError) as e:
                log.error(f"Error parseando respuesta de {model}: {e}")
                continue

    log.error("Todos los modelos de Gemini fallaron.")
    return None

# ── Formateo Blindado para Telegram (Sanitización) ───────────────────────────

def markdown_to_html(text: str) -> str:
    """
    Convierte el Markdown limpio generado por la IA en HTML válido para Telegram.
    Garantiza que no existan caracteres sueltos que rompan la API de Telegram (Error 400).
    """
    if not text:
        return ""
    
    # 1. Escapar de forma estricta los caracteres especiales planos antes de inyectar HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 2. Convertir negritas (**texto** -> <b>texto</b>)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b></b>", text)
    
    # 3. Convertir enlaces Markdown ([texto](url) -> <a href="url">texto</a>)
    # Como ya escapamos los < >, las etiquetas <a> inyectadas aquí serán perfectamente válidas.
    text = re.sub(r"\[(.+?)\]\((https?://.+?)\)", r'<a href=""></a>', text)
    
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
                    return False
        except Exception as e:
            log.error(f"Error enviando chunk {i+1}: {e}")
            return False

    log.info("Mensaje enviado a Telegram correctamente")
    return True

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    missing = [k for k, v in {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID":   TELEGRAM_CHAT_ID,
        "GEMINI_API_KEY":     GEMINI_API_KEY,
    }.items() if not v]

    if missing:
        log.error(f"Faltan variables de entorno: {', '.join(missing)}")
        sys.exit(1)

    all_items: list[dict] = []

    log.info("Recopilando YouTube...")
    for channel in YOUTUBE_CHANNELS:
        all_items.extend(fetch_youtube_items(channel))

    log.info("Recopilando RSS feeds...")
    for feed in RSS_FEEDS:
        all_items.extend(fetch_rss_items(feed))

    log.info(f"Total items recopilados: {len(all_items)}")

    if not all_items:
        log.info("Sin items esta semana — no se envía nada.")
        return

    summary = summarize_with_gemini(all_items)

    if not summary:
        log.info("Gemini no devolvió resumen — no se envía nada.")
        return

    if "no hay novedades" in summary.lower() or "no se han encontrado" in summary.lower():
        log.info("Gemini indica que no hay novedades relevantes.")
        return

    message = build_message(summary, len(all_items))
    ok = send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message, TELEGRAM_THREAD_ID)

    if not ok:
        log.error("Fallo definitivo al enviar el mensaje")
        sys.exit(1)

    log.info("✅ Digest semanal enviado correctamente")


if __name__ == "__main__":
    main()


# ── APÉNDICE: DOCUMENTACIÓN PARA IMPLEMENTAR LA OPCIÓN B (CLOUDFLARE WORKER) ──
"""
Si en el futuro la Opción A (corsproxy.io) deja de funcionar o devuelve errores de cuota, 
la solución definitiva es desplegar un Cloudflare Worker gratuito. 
Actuará como tu propio proxy privado indetectable.

Pasos para configurarlo:
1. Regístrate gratis en Cloudflare.
2. Ve a 'Workers & Pages' -> 'Create application' -> 'Create Worker'.
3. Nómbralo (ej: 'mi-rss-proxy') y pega el siguiente código JavaScript en el editor:

================================================================================
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const targetUrl = url.searchParams.get('url')

  if (!targetUrl) {
    return new Response('Falta el parámetro ?url=', { status: 400 })
  }

  const modifiedRequest = new Request(targetUrl, {
    method: request.method,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
      'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
  })

  try {
    const response = await fetch(modifiedRequest)
    const responseHeaders = new Headers(response.headers)
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders
    })
  } catch (err) {
    return new Response('Error en el proxy: ' + err.stack, { status: 500 })
  }
}
================================================================================

4. Publica el Worker ('Deploy'). Te dará una URL (ej: https://mi-rss-proxy.tu-usuario.workers.dev/).
5. En este archivo de Python, cambia:
   - USE_PROXY_OPTION_A = False
   - Modifica la línea dentro de `http_get`:
     target_url = f"https://mi-rss-proxy.tu-usuario.workers.dev/?url={urllib.parse.quote_plus(url)}"
"""
