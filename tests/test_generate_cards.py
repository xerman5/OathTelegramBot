"""Pruebas del catálogo sin acceso a la red ni publicaciones en Telegram."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from generate_cards import (
    check_removals,
    decode_catalog,
    decode_integer,
    decode_number,
    download_catalog,
    preserve_legacy_ids,
    select_cards,
    write_catalog,
)


def source_card(card_id="OATH-199", name="Golem Legions", product="denizen-deck", **extra):
    return {
        "id": card_id,
        "name": name,
        "image": "https://cardcdn.buriedgiant.com/cards/oath/en-US/Golem%20Legions.webp",
        "text": "**Action**: Gain `symbol:favor`.",
        "tags": ["Arcane"],
        "game": "oath",
        "product": product,
        "locale": "en-US",
        **extra,
    }


class DecodeCatalogTests(unittest.TestCase):
    def test_decodes_shared_schemas_nulls_and_escaped_strings(self):
        # Una tabla realista del formato compress-json, incluidas referencias
        # compartidas, cadenas que parecen valores codificados y metadatos.
        packed = [[
            "id", "text", "tags", "meta", "a|0|1|2|3",  # 0..4
            "OATH-199", "s|a|literal", "Arcane", "a|7",  # 5..8
            "defense", "a|9", "n|3", "o|A|B",  # 9..12
            "o|4|5|6|8|C", "a|D|D|_",  # 13..14
        ], "E"]
        expected = {
            "id": "OATH-199", "text": "a|literal",
            "tags": ["Arcane"], "meta": {"defense": 3},
        }
        # La raíz de producción es una lista de objetos, sin valores nulos.
        packed[0][14] = "a|D|D"
        self.assertEqual(decode_catalog(packed), [expected, expected])
        self.assertEqual(decode_catalog([["name", "o|0|_", "a|1"], "2"]), [{"name": None}])

    def test_decodes_empty_containers_booleans_and_literal_prefixes(self):
        packed = [[
            "empty", "tags", "enabled", "text", "a|0|1|2|3",
            "o|", "a|", "b|F", "s|b|T", "o|4|5|6|7|8", "a|9",
        ], "A"]
        self.assertEqual(decode_catalog(packed), [{
            "empty": {}, "tags": [], "enabled": False, "text": "b|T",
        }])

    def test_decodes_base62_numbers_and_decimal_exponents(self):
        self.assertEqual(decode_integer("z"), 61)
        self.assertEqual(decode_integer("10"), 62)
        self.assertEqual(decode_number("-10"), -62)
        self.assertEqual(decode_number("1.q"), 1.25)
        self.assertEqual(decode_number("1.q.-2"), 0.0125)
        values = [None] * 62 + ["a|"]
        self.assertEqual(decode_catalog([values, "10"]), [])

    def test_rejects_invalid_and_circular_references(self):
        for payload in ({}, [["a|1"], "0"], [["a|0"], "0"], [["n|3"], "0"]):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                decode_catalog(payload)

    def test_accepts_uncompressed_cards(self):
        cards = [source_card()]
        self.assertEqual(decode_catalog(cards), cards)

    @patch("generate_cards.fetch_json")
    def test_download_uses_the_published_version(self, fetch):
        fetch.side_effect = [{"cards": "version with spaces"}, [source_card()]]
        self.assertEqual(download_catalog(), [source_card()])
        self.assertIn("/version.json?t=", fetch.call_args_list[0].args[0])
        self.assertTrue(fetch.call_args_list[1].args[0].endswith("cards.min.json?v=version+with+spaces"))

    @patch("generate_cards.fetch_json", return_value={})
    def test_download_rejects_missing_version(self, fetch):
        with self.assertRaises(ValueError):
            download_catalog()
        fetch.assert_called_once()


class SelectCardsTests(unittest.TestCase):
    def test_filters_game_product_and_locale_and_maps_text(self):
        source = source_card()
        others = [
            source_card(game="arcs"),
            source_card(locale="te-ST"),
            source_card(product="oath-clockwork"),
        ]
        result = select_cards([source, *others], ["denizen-deck"], "en-US")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], source["text"])
        self.assertEqual(result[0]["image"], source["image"])
        self.assertEqual(result[0]["product"], "denizen-deck")
        self.assertNotIn("text", result[0])

    def test_missing_text_is_an_empty_description(self):
        card = source_card()
        del card["text"]
        self.assertEqual(select_cards([card], ["denizen-deck"], "en-US")[0]["description"], "")

    def test_rejects_missing_products_duplicate_ids_and_bad_fields(self):
        cases = [
            ([source_card()], ["oathbasegame", "denizen-deck"]),
            ([source_card(), source_card()], ["denizen-deck"]),
            ([source_card(image="relative.webp")], ["denizen-deck"]),
            ([source_card(tags="Arcane")], ["denizen-deck"]),
            ([source_card(text=None)], ["denizen-deck"]),
            ([source_card(name="")], ["denizen-deck"]),
        ]
        for cards, products in cases:
            with self.subTest(cards=cards, products=products), self.assertRaises(ValueError):
                select_cards(cards, products, "en-US")


class MigrationAndWriteTests(unittest.TestCase):
    def setUp(self):
        self.previous = [{"id": "OATH-199", "name": "Sprawling Rampart"}]
        self.cards = select_cards([
            source_card("OATH-E01-OG", "Sprawling Rampart", "oathbasegame"),
            source_card(),
        ], ["oathbasegame", "denizen-deck"], "en-US")

    def test_reused_ids_do_not_confuse_old_and_new_cards(self):
        check_removals(self.cards, self.previous)
        preserve_legacy_ids(self.cards, self.previous)
        self.assertEqual(self.cards[0]["id"], "OATH-E01-OG")
        self.assertEqual(self.cards[0]["legacy_id"], "OATH-199")
        self.assertEqual(self.cards[1]["id"], "OATH-199")
        self.assertNotIn("legacy_id", self.cards[1])

    def test_migration_is_repeatable(self):
        preserve_legacy_ids(self.cards, self.previous)
        expected = copy.deepcopy(self.cards)
        refreshed = copy.deepcopy(self.cards)
        for card in refreshed:
            card.pop("legacy_id", None)
        preserve_legacy_ids(refreshed, expected)
        self.assertEqual(refreshed, expected)

    def test_partial_source_cannot_remove_existing_cards(self):
        with self.assertRaisesRegex(ValueError, "eliminaría 1 cartas"):
            check_removals(self.cards[1:], self.previous)

    def test_write_preserves_unicode_and_existing_file_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cards.json"
            cards = [{"name": "Consejo arcano — edición española"}]
            write_catalog(path, cards)
            original = path.read_bytes()
            self.assertEqual(json.loads(original), cards)
            self.assertIn("española", original.decode("utf-8"))
            with patch("generate_cards.json.dump", side_effect=OSError("disco lleno")):
                with self.assertRaises(OSError):
                    write_catalog(path, [])
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(directory).iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
