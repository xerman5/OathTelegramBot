"""Reconstruye el catálogo de Oath desde los datos públicos de Buried Giant.

Solo usa la biblioteca estándar. No descarga imágenes ni publica en Telegram.
La web obtiene version.json y después cards.min.json, comprimido mediante
compress-json (tabla de valores y referencias en base 62).
"""

import argparse
import json
import logging
import os
import string
import tempfile
import time
import urllib.parse
import urllib.request
from collections import Counter
from functools import lru_cache
from pathlib import Path


CDN_URL = "https://cardcdn.buriedgiant.com"
DEFAULT_PRODUCTS = ("oathbasegame", "denizen-deck")
BASE62 = string.digits + string.ascii_uppercase + string.ascii_lowercase
log = logging.getLogger(__name__)


def decode_integer(value: str) -> int:
    """Lee un entero con el alfabeto base 62 de compress-json."""
    if not value:
        raise ValueError("Referencia base 62 vacía")
    result = 0
    for character in value:
        result = result * 62 + BASE62.index(character)
    return result


def decode_number(value: str) -> int | float:
    """Decodifica números; las fracciones y los exponentes están invertidos."""
    if value.startswith("-"):
        return -decode_number(value[1:])
    parts = value.split(".")
    if len(parts) == 1:
        return decode_integer(value)
    if len(parts) not in (2, 3) or not all(parts):
        raise ValueError(f"Número comprimido inválido: {value}")

    def decimal(part: str) -> str:
        return str(decode_integer(part.removeprefix(":")))

    number = decimal(parts[0]) + "." + decimal(parts[1])[::-1]
    if len(parts) == 3:
        exponent = parts[2]
        sign = "-" if exponent.startswith("-") else ""
        number += "e" + sign + decimal(exponent.removeprefix("-"))[::-1]
    return float(number)


def decode_catalog(payload: list) -> list[dict]:
    """Acepta el JSON comprimido de la web o una lista de cartas sin comprimir."""
    if not isinstance(payload, list):
        raise ValueError("El catálogo debe ser una lista JSON")
    if all(isinstance(card, dict) for card in payload):
        return payload
    if len(payload) != 2 or not isinstance(payload[0], list):
        raise ValueError("Formato de catálogo desconocido")
    values, root = payload
    active = set()

    @lru_cache(maxsize=None)
    def decode(reference: str):
        if reference in ("", "_"):
            return None
        if not isinstance(reference, str):
            raise ValueError("Referencia comprimida inválida")
        index = decode_integer(reference)
        if index >= len(values):
            raise ValueError(f"Referencia fuera de rango: {reference}")
        if index in active:
            raise ValueError("Referencia circular en el catálogo")
        value = values[index]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if not isinstance(value, str):
            raise ValueError("Valor comprimido inválido")
        active.add(index)
        try:
            prefix, body = value[:2], value[2:]
            if prefix == "a|":
                return [decode(item) for item in body.split("|")] if body else []
            if prefix == "o|":
                if not body:
                    return {}
                schema, *references = body.split("|")
                keys = decode(schema)
                if not isinstance(keys, list):
                    keys = [keys]
                if len(keys) != len(references) or not all(isinstance(k, str) for k in keys):
                    raise ValueError("Esquema de objeto comprimido inválido")
                return dict(zip(keys, (decode(item) for item in references)))
            if prefix == "n|":
                return decode_number(body)
            if prefix == "b|":
                if body not in ("T", "F"):
                    raise ValueError("Booleano comprimido inválido")
                return body == "T"
            return body if prefix == "s|" else value
        finally:
            active.remove(index)

    cards = decode(root)
    if not isinstance(cards, list) or not all(isinstance(card, dict) for card in cards):
        raise ValueError("El catálogo decodificado no contiene una lista de cartas")
    return cards


def fetch_json(url: str):
    """Obtiene JSON público con un tiempo de espera limitado."""
    request = urllib.request.Request(url, headers={"User-Agent": "OathBot-Catalog/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download_catalog() -> list[dict]:
    """Usa la versión publicada para evitar una copia antigua en la caché CDN."""
    version = fetch_json(f"{CDN_URL}/version.json?t={time.time_ns()}")
    if not isinstance(version, dict) or not isinstance(version.get("cards"), str) or not version["cards"]:
        raise ValueError("La fuente no publica una versión del catálogo")
    query = urllib.parse.urlencode({"v": version["cards"]})
    log.info("Versión de origen: %s", version["cards"])
    return decode_catalog(fetch_json(f"{CDN_URL}/cards.min.json?{query}"))


def select_cards(cards: list[dict], products: list[str], locale: str) -> list[dict]:
    """Filtra por juego, producto e idioma y adapta text a description."""
    selected = []
    seen = set()
    counts = Counter()
    for source in cards:
        if source.get("game") != "oath" or source.get("locale") != locale:
            continue
        product = source.get("product")
        if product not in products:
            continue
        for field in ("id", "name", "image"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"Carta sin {field} válido: {source.get('id', '?')}")
        card_id = source["id"]
        if card_id in seen:
            raise ValueError(f"ID duplicado en origen: {card_id}")
        image = urllib.parse.urlsplit(source["image"])
        if image.scheme not in ("http", "https") or not image.netloc:
            raise ValueError(f"Imagen sin URL absoluta: {card_id}")
        description = source.get("text", "")
        tags = source.get("tags", [])
        if not isinstance(description, str):
            raise ValueError(f"Texto inválido: {card_id}")
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError(f"Etiquetas inválidas: {card_id}")
        selected.append({
            "image": source["image"],
            "name": source["name"],
            "id": card_id,
            "description": description,
            "tags": tags,
            "game": "oath",
            "product": product,
            "locale": locale,
        })
        seen.add(card_id)
        counts[product] += 1
    missing = set(products) - counts.keys()
    if missing:
        raise ValueError(f"Productos sin cartas para {locale}: {', '.join(sorted(missing))}")
    return selected


def preserve_legacy_ids(cards: list[dict], previous: list[dict]) -> None:
    """Relaciona por nombre, producto e idioma, nunca por los IDs reutilizados.

    El archivo antiguo carecía de producto e idioma; sus cartas eran todas
    del juego base en inglés. legacy_id conserva el significado de history.json.
    """
    old_by_identity = {}
    for old in previous:
        identity = (
            old["name"],
            old.get("product", "oathbasegame"),
            old.get("locale", "en-US"),
        )
        if identity in old_by_identity:
            raise ValueError(f"Identidad duplicada en el catálogo anterior: {identity}")
        old_by_identity[identity] = old
    for card in cards:
        old = old_by_identity.get((card["name"], card["product"], card["locale"]))
        if old is None:
            continue
        legacy_id = old.get("legacy_id", old["id"])
        if legacy_id != card["id"]:
            card["legacy_id"] = legacy_id


def check_removals(cards: list[dict], previous: list[dict]) -> None:
    """Evita reemplazar silenciosamente el catálogo con una respuesta parcial."""
    identities = {(card["name"], card["product"], card["locale"]) for card in cards}
    current_ids = {(card["id"], card["product"], card["locale"]) for card in cards}
    missing = []
    for old in previous:
        product = old.get("product", "oathbasegame")
        locale = old.get("locale", "en-US")
        if (old["name"], product, locale) in identities:
            continue
        if "product" in old and (old["id"], product, locale) in current_ids:
            continue
        missing.append(old["name"])
    if missing:
        raise ValueError(
            f"La actualización eliminaría {len(missing)} cartas (ej.: {missing[0]}). "
            "Revisa el origen o usa --allow-removals si es intencionado."
        )


def write_catalog(path: Path, cards: list[dict]) -> None:
    """Sustituye el catálogo solo cuando el archivo completo está escrito."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as output:
            temporary = Path(output.name)
            json.dump(cards, output, indent=2, ensure_ascii=False)
            output.write("\n")
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("oath_cards.json"), help="JSON de destino")
    parser.add_argument("--input", type=Path, help="Catálogo de origen local; evita las peticiones HTTP")
    parser.add_argument("--products", nargs="+", default=list(DEFAULT_PRODUCTS), help="IDs de producto")
    parser.add_argument("--locale", default="en-US", help="Idioma de origen (en-US por defecto)")
    parser.add_argument("--dry-run", action="store_true", help="Valida y muestra recuentos sin escribir")
    parser.add_argument("--allow-removals", action="store_true", help="Permite eliminar cartas del catálogo anterior")
    args = parser.parse_args()
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    try:
        source = decode_catalog(json.loads(args.input.read_text(encoding="utf-8"))) if args.input else download_catalog()
        cards = select_cards(source, args.products, args.locale)
        if args.output.exists():
            previous = json.loads(args.output.read_text(encoding="utf-8"))
            if not args.allow_removals:
                check_removals(cards, previous)
            preserve_legacy_ids(cards, previous)
        for product, count in sorted(Counter(card["product"] for card in cards).items()):
            log.info("%s: %s cartas", product, count)
        log.info("Total: %s; referencias antiguas: %s", len(cards), sum("legacy_id" in card for card in cards))
        if not args.dry_run:
            write_catalog(args.output, cards)
            log.info("Catálogo guardado en %s", args.output)
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
