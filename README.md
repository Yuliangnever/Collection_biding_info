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

## How to Run in VS Code

These commands are entered in the VS Code terminal, not in the Python editor.

1. Open VS Code.
2. Open this project folder:

   ```text
   D:\Python Code\Tender Information
   ```

3. Open the terminal in VS Code:

   ```text
   Terminal -> New Terminal
   ```

   In Chinese VS Code, it is usually:

   ```text
   终端 -> 新建终端
   ```

4. Confirm that the terminal prompt looks like this:

   ```powershell
   PS D:\Python Code\Tender Information>
   ```

5. Run commands in that terminal.

This project currently uses the Python installed with Spyder:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" crawl-only
```

If your terminal recognizes `python`, you can also use the shorter examples
below. If not, use the full Spyder Python command shown above.

## Configuration

Create a local `.env` file for real private settings such as the enterprise
WeCom webhook. Do not put real webhook keys in `.env.example` before pushing to
GitHub.

Example `.env`:

```text
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key
DATABASE_PATH=data/tenders.sqlite3
REQUEST_TIMEOUT=20
```

## CLI

The following commands tell `main.py` what action to perform.

### Run Once

Crawl tender data, save it to the local database, and send pending
notifications when allowed by configuration.

```powershell
python main.py run-once
```

With the Spyder Python path:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" run-once
```

### Crawl Only

Crawl tender data and save it to the local database, but do not send tender
notifications. This is the safest command for first testing.

```powershell
python main.py crawl-only
```

With the Spyder Python path:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" crawl-only
```

### Push Pending

Send notifications for tender records that are already stored in the database
and have not been marked as notified.

```powershell
python main.py push-pending
```

With the Spyder Python path:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" push-pending
```

### List Latest

Print the latest records saved in the local SQLite database.

```powershell
python main.py list-latest --limit 10
```

With the Spyder Python path:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" list-latest --limit 10
```

### Test WeCom

Send a test message to the enterprise WeCom webhook. This does not represent a
real tender notice.

```powershell
python main.py test-wecom
```

With the Spyder Python path:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" test-wecom
```

### Schedule

Keep the program running and execute the pipeline repeatedly. The example below
runs it every 30 minutes. You can stop it with `Ctrl+C` in the terminal.

```powershell
python main.py schedule --interval-minutes 30
```

With the Spyder Python path:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" schedule --interval-minutes 30
```

## Testing

Run unit tests from the VS Code terminal:

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe -m pytest -q
```

Expected result:

```text
3 passed
```

## Notes

The default scraper is intentionally conservative and ships with demo tender
items so the project can run immediately. Replace `DemoTenderScraper` with real
site-specific implementations when you are ready to connect production sources.
