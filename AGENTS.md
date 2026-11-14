# Repository Guidelines

## Project Structure & Module Organization

This Spanish-language Oath Telegram bot runs through GitHub Actions using Python's standard library.

- `send_daily_card.py`: deterministic daily selection, captions, and Telegram photo delivery.
- `generate_cards.py`: downloads and decodes the public catalog; `tests/` contains its offline `unittest` tests.
- `send_weekly_digestv3.py`: active news digest using Gemini and Telegram. `send_weekly_digest.py` and `send_weekly_digestv2.py` are earlier implementations.
- `oath_cards.json`: base game and Denizen Pack cards, including source metadata and historical `legacy_id` references. Images remain external.
- `history.json`: automated delivery history.
- `.github/workflows/`: schedules, Python setup, and secrets. Workflows are authoritative when README instructions differ.

## Build, Test, and Development Commands

Use Python 3.12 from the repository root. No build or installation is required.

- `python3 -m py_compile *.py`: check syntax without sending messages.
- `python3 generate_cards.py --dry-run`: validate the current public catalog; omit `--dry-run` to update JSON.
- `python3 -m json.tool oath_cards.json > /dev/null`: validate catalog JSON; repeat for `history.json`.
- `python3 send_daily_card.py`: send today's card to the configured Telegram destination.
- `python3 send_weekly_digestv3.py`: collect news, call Gemini, and send the weekly digest.

The last two commands publish messages; use a dedicated test chat.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions and variables, and `UPPER_SNAKE_CASE` constants. Follow existing type hints, Spanish comments, and user-facing wording. Prefer standard-library dependencies. No formatter or linter is configured. Use official card IDs, preserve historical `legacy_id` references, and retain two-space JSON indentation. Keep daily-script stdout limited to the selected card ID because Actions captures it; use logging for diagnostics.

## Testing Guidelines

Run `python3 -m unittest discover -s tests -v` plus syntax and JSON checks. No coverage threshold is configured. Place tests in `tests/test_*.py`; mock HTTP and dates. Cover decoding, product/locale filters, ID migrations, and failed writes. Never publish messages from automated tests.

## Commit & Pull Request Guidelines

History uses short subjects such as `Update send_weekly_digestv3.py`, with no enforced prefix convention. Use concise, descriptive subjects. Leave automated `🃏 Carta del día: ...` history commits to the workflow. PRs should explain behavior changes, affected scripts or schedules, validation performed, and related issues. Include sample Telegram output when formatting changes.

## Security & Configuration

Supply `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` through environment variables or GitHub Actions secrets; weekly digests also require `GEMINI_API_KEY`. Optional settings include `TELEGRAM_THREAD_ID` and daily-script `CARDS_FILE`. Never commit credentials or include credential-bearing request URLs in logs. Local `.env` files are ignored but are not loaded automatically.
