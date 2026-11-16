# WebPilot AI — BuildSprint Implementation Challenge

WebPilot AI is a chat-style website research prototype. A user describes a website task, and the backend invokes a real Python CLI crawler using `subprocess`. The crawler fetches public HTML pages, extracts useful information, returns structured JSON, and the interface displays the result and execution status.

## Features

- Chat-style task interface
- URL and request validation
- Real CLI invocation through Python `subprocess.run`
- Website crawling with Requests and BeautifulSoup
- Same-host page discovery (maximum 5 pages)
- `robots.txt` check before each page request
- Title, meta description, headings, page text, and links extraction
- JSON parsing and display
- Captured stdout, stderr, exit code, duration, and timeout handling
- Download-ready JSON displayed in the interface (use the JSON panel's copy option)

## Technology

- Python 3
- Streamlit
- Requests
- BeautifulSoup
- Python subprocess

## Requirements

- macOS, Windows, or Linux
- Python 3.10 or newer
- Internet connection for crawling public websites

## Run locally on macOS

Open Terminal and run:

```bash
cd WebPilot_AI_BuildSprint
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL, normally `http://localhost:8501`. Open it in your browser.

## Mandatory demo test

1. Open the application.
2. Enter `https://example.com`.
3. Keep the suggested task or enter: `Crawl this website, extract the important information, summarize it, and return JSON.`
4. Click **Run website task**.
5. Show the summary, extracted JSON, success status, and execution details.

The application invokes the crawler as a separate process similar to:

```bash
python cli/crawler.py --url https://example.com --max-pages 5
```

The backend does not use `shell=True`. URL and page-limit values are passed as separate process arguments. The backend captures standard output, standard error, and the exit code, applies a 60-second process timeout, and parses the CLI's JSON output before displaying it.

## Architecture

```text
User
 |
 v
Streamlit Chat UI (app.py)
 |
 v
Input validation
 |
 v
Backend orchestrator
 |
 | subprocess.run([...], capture_output=True, timeout=60)
 v
Approved Python CLI (cli/crawler.py)
 |
 +--> Validate HTTP/HTTPS URL
 +--> Check robots.txt
 +--> Fetch public HTML pages
 +--> Stay on original hostname (max 5 pages)
 +--> Extract title, description, headings, text, links
 |
 v
JSON on stdout + errors on stderr + exit code
 |
 v
Backend parses and validates JSON
 |
 v
Chat summary + structured JSON + execution status
```

## Security and reliability

- Only HTTP and HTTPS URLs are accepted.
- URLs with embedded credentials and local hostnames are rejected.
- The crawler remains on the original hostname and limits crawling to five pages.
- `robots.txt` is checked before each page.
- Request timeouts and an overall process timeout are configured.
- The backend passes arguments as a list and does not invoke an unrestricted shell.
- Website text is extracted as data only; it is never executed as instructions or commands.
- Failures are surfaced as errors rather than fabricated success results.

**Limitations:** This prototype creates a concise extractive summary from fetched page content. It does not call an external LLM API. Some websites may block automated requests, require JavaScript, or disallow crawling. In those cases the app reports a failure or partial result.

## GitHub upload

Create a new empty GitHub repository, for example `webpilot-ai-buildsprint`.

Then run these commands inside the project folder:

```bash
git init
git add .
git commit -m "Build WebPilot AI CLI website crawler"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/webpilot-ai-buildsprint.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Do not commit API keys, passwords, or `.env` files.

## Demo video checklist (4–7 minutes)

1. Introduce WebPilot AI and the problem it solves.
2. Show the architecture in this README.
3. Open the app and enter `https://example.com`.
4. Run the task live and show the crawler execution.
5. Show the summary and valid JSON result.
6. Show execution details and explain subprocess, stdout/stderr, exit code, and timeout.
7. Demonstrate an invalid URL such as `ftp://example.com` and show validation.
8. Mention that the crawler uses Requests and BeautifulSoup and that the main coding assistance used should be disclosed accurately.

## Responsible use

Only crawl websites you are permitted to access. Respect site terms, robots restrictions, and applicable laws. Do not use this prototype to bypass authentication or access controls.
