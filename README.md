# Energy Tender Monitor

Energy Tender Monitor is a small Python project for collecting tender notices,
matching them against configurable keywords and companies, storing the results,
and optionally sending pending notifications to a webhook.

## Features

- YAML-driven keyword, company, and runtime configuration
- Lightweight scraper abstraction with a demo source
- Keyword and company matching
- SQLite persistence
- Optional webhook notifications
- CLI commands for one-off runs and inspection
- Focused unit tests for parsing, matching, and storage

## Project layout

```text
.
|-- config/
|   |-- companies.yaml
|   |-- keywords.yaml
|   `-- settings.yaml
|-- data/
|-- logs/
|-- src/
|   |-- config_loader.py
|   |-- models.py
|   |-- notifier.py
|   |-- parser.py
|   |-- pipeline.py
|   |-- scheduler.py
|   |-- storage.py
|   `-- scraper.py
|-- tests/
|-- main.py
`-- requirements.txt
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` if you want to customize runtime values.

## CLI

```powershell
python main.py run-once
python main.py crawl-only
python main.py push-pending
python main.py list-latest --limit 10
python main.py schedule --interval-minutes 30
```

## Notes

The default scraper is intentionally conservative and ships with demo tender
items so the project can run immediately. Replace `DemoTenderScraper` with real
site-specific implementations when you are ready to connect production sources.

