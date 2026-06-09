"""
send_daily_card.py
------------------
Script de un solo disparo: elige la carta del día, la envía a Telegram y termina.
Diseñado para ejecutarse desde GitHub Actions (cron diario).

Uso:
    python send_daily_card.py

Variables de entorno requeridas (GitHub Secrets):
    TELEGRAM_BOT_TOKEN   — token del bot 
    TELEGRAM_CHAT_ID     — canal/grupo destino

Variables opcionales:
    TELEGRAM_THREAD_ID   — ID del topic en grupos con temas (
    CARDS_FILE           — ruta al JSON 
"""

import json
import logging
import os
import random
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

TOKEN      = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")
THREAD_ID  = os.environ.get("TELEGRAM_THREAD_ID", "")   # topic General = 143
CARDS_FILE = Path(os.environ.get("CARDS_FILE", "oath_cards.json"))

# ── Cargar cartas ─────────────────────────────────────────────────────────────

def load_cards(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        cards = json.load(f)
    valid = [c for c in cards if c.get("image") and c.get("name")]
    log.info(f"Cartas cargadas: {len(valid)}")
    return valid


# ── Elegir carta del día ──────────────────────────────────────────────────────

def pick_card(cards: list[dict]) -> dict:
    """
    Elige la carta del día de forma determinista por fecha.
    La misma fecha siempre produce la misma carta.
    """
    today = date.today()
    rng = random.Random(today.toordinal())
    card = rng.choice(cards)
    log.info(f"Carta del día ({today}): {card['id']} — {card['name']}")
    return card


# ── Formateo del mensaje ──────────────────────────────────────────────────────

SYMBOL_MAP = {
    "symbol:favor":       "🪙",
    "symbol:secret":      "📖",
    "symbol:supply":      "📦",
    "symbol:diceb":       "🎲",
    "symbol:dicer":       "🎲",
    "symbol:suit-order":  "⚔️",
    "symbol:suit-arcane": "✨",
    "symbol:suit-beast":  "🐾",
    "symbol:suit-nomad":  "🏕️",
    "symbol:suit-hearth": "🏠",
    "symbol:suit-discord":"💀",
}

def format_caption(card: dict) -> str:
    """Genera el caption HTML para el mensaje de Telegram."""
    name  = card.get("name", "???")
    desc  = card.get("description") or ""
    tags  = card.get("tags") or []
    cid   = card.get("id", "")

    # Sustituir símbolos del juego por emojis
    desc = re.sub(
        r"`(symbol:[^`]+)`",
        lambda m: SYMBOL_MAP.get(m.group(1), f"[{m.group(1)}]"),
        desc,
    )
    # **negrita** → <b>
    desc = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", desc)
    # *cursiva* → <i>
    desc = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", desc)

    lines = [f"🃏 <b>La Carta del Día</b>", ""]
    lines.append(f"<b>{name}</b>  <code>{cid}</code>")
    if tags:
        lines.append(f"<i>{' · '.join(tags)}</i>")
    if desc:
        lines.append("")
        lines.append(desc)

    return "\n".join(lines)


# ── Envío a Telegram (sin dependencias externas, solo stdlib) ─────────────────

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _api_call(token: str, method: str, data: dict, files: dict | None = None) -> dict:
    """
    Llama a la Bot API de Telegram.
    Si se pasa `files`, hace multipart/form-data (para enviar bytes).
    Si no, hace application/x-www-form-urlencoded.
    """
    url = TELEGRAM_API.format(token=token, method=method)

    if files:
        # Multipart manual con stdlib
        boundary = "----TelegramBotBoundary"
        body_parts = []

        for key, value in data.items():
            body_parts.append(
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{value}\r\n"
            )

        for field_name, (filename, content_bytes, content_type) in files.items():
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            )
            body_parts_bytes = b"".join(p.encode() for p in body_parts)
            body_parts_bytes += header.encode() + content_bytes + b"\r\n"
            body_parts_bytes += f"--{boundary}--\r\n".encode()

            req = urllib.request.Request(
                url,
                data=body_parts_bytes,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())

    # Formulario normal
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def download_image(url: str) -> bytes:
    """Descarga una imagen desde una URL y devuelve los bytes."""
    req = urllib.request.Request(url, headers={"User-Agent": "OathBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def send_card(token: str, chat_id: str, card: dict, thread_id: str = "") -> bool:
    """
    Envía la carta como foto a Telegram.
    Estrategia:
      1. Intentar con la URL directa (rápido, funciona para jpeg/png públicos).
      2. Si falla (ej: webp, redirección, CDN hostil), descargar y enviar bytes.
    thread_id: si se especifica, publica en ese topic del grupo.
    Returns True si el envío fue exitoso.
    """
    caption = format_caption(card)
    image_url = card["image"]

    # Parámetros base — añadir thread_id solo si viene informado
    base_params = {
        "chat_id":    chat_id,
        "caption":    caption,
        "parse_mode": "HTML",
    }
    if thread_id:
        base_params["message_thread_id"] = thread_id

    # — Intento 1: URL directa —
    try:
        log.info("Intentando enviar por URL directa...")
        result = _api_call(token, "sendPhoto", {**base_params, "photo": image_url})
        if result.get("ok"):
            log.info("Enviado correctamente por URL.")
            return True
        log.warning(f"URL directa rechazada: {result.get('description')}")
    except Exception as e:
        log.warning(f"Error con URL directa: {e}")

    # — Intento 2: Descargar y subir bytes —
    try:
        log.info("Descargando imagen para subir como fichero...")
        image_bytes = download_image(image_url)
        filename    = image_url.split("/")[-1]
        content_type = "image/webp" if filename.endswith(".webp") else "image/jpeg"

        result = _api_call(
            token,
            "sendPhoto",
            base_params,
            files={"photo": (filename, image_bytes, content_type)},
        )
        if result.get("ok"):
            log.info("Enviado correctamente como fichero.")
            return True
        log.error(f"Fallo subiendo fichero: {result.get('description')}")
    except Exception as e:
        log.error(f"Error subiendo fichero: {e}")

    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Validar config
    if not TOKEN:
        log.error("Falta TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    if not CHAT_ID:
        log.error("Falta TELEGRAM_CHAT_ID")
        sys.exit(1)
    if not CARDS_FILE.exists():
        log.error(f"No se encuentra el fichero de cartas: {CARDS_FILE}")
        sys.exit(1)

    cards = load_cards(CARDS_FILE)
    card  = pick_card(cards)
    ok    = send_card(TOKEN, CHAT_ID, card, THREAD_ID)

    if not ok:
        log.error("No se pudo enviar la carta.")
        sys.exit(1)

    # Devolver el ID de la carta para que el workflow lo use en el commit
    print(card["id"])


if __name__ == "__main__":
    main()
