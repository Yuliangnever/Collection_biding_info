# Energy Tender Monitor

Energy Tender Monitor is a small Python project for collecting tender notices,
matching them against configurable keywords and companies, storing the results,
and optionally sending pending notifications to a webhook.

## 中文使用指南

这个项目用于监控招投标信息，按照配置里的关键词和公司名称进行匹配，把结果保存到本地 SQLite 数据库，并可以通过企业微信机器人发送通知。

### 1. 在哪里输入命令

命令不是写在 `main.py` 代码文件里，而是输入在 VS Code 的终端里。

操作步骤：

1. 打开 VS Code。
2. 打开项目文件夹：

   ```text
   D:\Python Code\Tender Information
   ```

3. 在 VS Code 顶部菜单点击：

   ```text
   终端 -> 新建终端
   ```

4. 看到下面这样的提示符，说明位置正确：

   ```powershell
   PS D:\Python Code\Tender Information>
   ```

5. 把下面的命令复制到这个终端里，然后按回车。

### 2. 推荐使用的 Python 命令

你当前电脑上可以使用 Spyder 自带的 Python。后面的命令都可以用这个格式：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" 命令名称
```

例如：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" crawl-only
```

### 3. 常用命令说明

只抓取并保存，不发送招标通知。第一次测试建议用这个：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" crawl-only
```

抓取、保存，并尝试发送待通知的信息：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" run-once
```

发送数据库里还没有推送过的通知：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" push-pending
```

查看最近保存的 10 条记录：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" list-latest --limit 10
```

测试企业微信机器人是否能收到消息：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" test-wecom
```

每 30 分钟自动运行一次。停止时在终端里按 `Ctrl+C`：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" schedule --interval-minutes 30
```

### 4. 企业微信 Webhook 配置

真实的企业微信 Webhook 不建议写进 `.env.example`，因为这个文件可能会被上传到 GitHub。

推荐做法：

1. 在项目根目录新建一个 `.env` 文件。
2. 把真实 Webhook 写进 `.env`：

   ```text
   WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key
   DATABASE_PATH=data/tenders.sqlite3
   REQUEST_TIMEOUT=20
   ```

3. `.env` 已经在 `.gitignore` 里，不会被上传到 GitHub。

### 5. 运行测试

在 VS Code 终端里运行：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe -m pytest -q
```

看到下面结果就说明测试通过：

```text
3 passed
```

### 6. 当前注意事项

目前项目里的抓取器还是示例数据源，用于验证流程是否跑通。它不是正式招投标网站数据。

下一阶段如果要抓取真实信息，需要指定优先抓取的网站，例如：

- 国家电网电子商务平台
- 南方电网供应链统一服务平台
- 中国招标投标公共服务平台
- 中国政府采购网

不同网站页面结构不同，需要分别编写对应的抓取逻辑。

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
