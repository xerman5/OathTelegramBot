# Repository Guidelines

## Scope & Orientation

Read [README.md](README.md) and [the project state](docs/ESTADO_PROYECTO.md) first. Three flows generate the public catalog, post daily cards, and publish weekly news. Local NF/Denizen images and terminology are prepared; Spanish card translations, fan layouts, and local-image delivery remain pending. Runtime still uses English and remote images.

## Project Structure

- `generate_cards.py`, `tests/`: catalog export and offline `unittest` coverage.
- `send_daily_card.py`: daily delivery; `send_weekly_digestv3.py`: active digest. Other digest versions are historical.
- `oath_cards.json`: runtime base + Denizen catalog; `history.json`: workflow-managed delivery history.
- `local_cards/`: NF + Denizen originals, translation placeholders, guides, and dated audits; excludes base.
- `local_cards/translation/glossary.csv`: canonical terminology decisions. Markdown views require synchronization; context JSON is historical evidence.
- `assets/`: original automatic transcripts; preserve them and record interpretations separately.
- `.github/workflows/`: authoritative runtime schedules and entry points.

## Build, Test & Development

Use Python 3.12 and the standard library; no installation or build is required.

- `python3 -m unittest discover -s tests -v`: offline generator tests.
- `python3 -m py_compile *.py`: syntax check.
- `python3 -m json.tool oath_cards.json > /dev/null`: JSON validation; repeat for history and local catalogs.
- `python3 generate_cards.py --dry-run`: network validation without writing.

The daily and active weekly scripts send real Telegram messages. They have no dry-run mode. Tests must never publish. Use `tests/test_*.py`, mock network/date dependencies, and cover meaningful behavior; no coverage threshold is configured.

## Coding & Data Conventions

Use four spaces, `snake_case`, `UPPER_SNAKE_CASE` constants, existing type hints, Spanish comments, and two-space JSON indentation. No formatter is configured. Keep daily stdout limited to its selected ID.

Preserve official IDs, `legacy_id`, history, original text, symbol tokens, and PNG originals. Keep all images local; public Git must not track originals, references, or derivatives. Never overwrite local catalogs with generator output: it drops translation fields. Preserve `translations` by ID/product/locale. Use established 2Tomatoes vocabulary and current English NF rules; ASR cannot certify exact titles. Approval of terminology policy does not approve every draft.

## Commits, Pull Requests & Configuration

Use short descriptive commit subjects; no prefix convention is enforced. PRs explain behavior, validation, and related issues; include sample output for formatting changes. Leave automated card-history commits to Actions. Check tracking status before assuming local assets exist in a clone.

Use environment variables or Actions secrets for Telegram credentials and `GEMINI_API_KEY`; never log credentials. Optional settings include `TELEGRAM_THREAD_ID` and daily `CARDS_FILE`. `.env` files are not loaded automatically.
