import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

ROOT = Path(__file__).resolve().parent
CRAWLER = ROOT / "cli" / "crawler.py"
PYTHON = sys.executable

st.set_page_config(page_title="WebPilot AI", page_icon="🌐", layout="wide")

st.markdown("""
<style>
.main {max-width: 1100px; padding-top: 1.5rem;}
.hero {padding: 1.2rem 1.4rem; border-radius: 16px; background: linear-gradient(120deg,#172554,#0f766e); color:white; margin-bottom:1rem;}
.hero h1 {margin:0; color:white;}
.hero p {margin:.35rem 0 0 0; color:#dbeafe;}
.small-muted {color: #64748b; font-size:.9rem;}
.stChatMessage {border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🌐 WebPilot AI</h1>
<p>Turn natural-language website research requests into controlled CLI execution and structured results.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("How it works")
    st.write("1. Enter a public website URL.")
    st.write("2. Describe what information you need.")
    st.write("3. The backend validates the URL and starts the crawler CLI.")
    st.write("4. WebPilot captures the process output and displays a summary and JSON.")
    st.divider()
    st.subheader("Execution safeguards")
    st.write("• HTTP/HTTPS URLs only")
    st.write("• Same-host crawling")
    st.write("• Robots.txt checked")
    st.write("• Maximum 5 pages")
    st.write("• 15-second request timeout")
    st.write("• 60-second process timeout")
    st.caption("Website text is treated as untrusted data. It cannot issue commands.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("json"):
            st.json(msg["json"])
        if msg.get("logs"):
            with st.expander("Execution details"):
                st.code(msg["logs"])

st.info("Try: “Crawl this website, extract the important information, summarize it, and return JSON.”")

with st.form("crawl_form", clear_on_submit=False):
    url = st.text_input("Website URL", placeholder="https://example.com")
    prompt = st.text_area(
        "Your task",
        value="Crawl this website, extract the important information, summarize it, and return JSON.",
        height=90
    )
    submitted = st.form_submit_button("Run website task", type="primary", use_container_width=True)

if submitted:
    st.session_state.messages.append({
        "role": "user",
        "content": f"**Website:** {url.strip()}\n\n**Task:** {prompt.strip()}"
    })
    with st.chat_message("user"):
        st.markdown(f"**Website:** {url.strip()}\n\n**Task:** {prompt.strip()}")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        answer = "The URL is invalid. Please enter a public URL beginning with http:// or https://."
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.error(answer)
    elif not prompt.strip():
        answer = "Please describe what you want the crawler to do."
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.warning(answer)
    else:
        with st.chat_message("assistant"):
            status = st.status("Preparing controlled CLI execution...", expanded=True)
            start = time.time()
            try:
                task_lower = prompt.lower()
                detected_actions = []
                if any(word in task_lower for word in ("crawl", "website", "webpage", "url")):
                    detected_actions.append("website_crawl")
                if any(word in task_lower for word in ("summar", "overview", "important")):
                    detected_actions.append("summarization")
                if any(word in task_lower for word in ("json", "structured", "extract", "data")):
                    detected_actions.append("structured_extraction")
                if not detected_actions:
                    detected_actions.append("website_crawl")
                status.write("Intent understood: " + ", ".join(detected_actions))
                status.write("Validating URL and preparing approved crawler arguments.")
                # Arguments are passed as a list; shell=True is deliberately not used.
                completed = subprocess.run(
                    [PYTHON, str(CRAWLER), "--url", url.strip(), "--max-pages", "5"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(ROOT),
                    check=False
                )
                elapsed = round(time.time() - start, 2)
                status.write(f"CLI process finished with exit code {completed.returncode}.")
                if completed.returncode == 0:
                    data = json.loads(completed.stdout)
                    summary = data.get("summary", "No summary was generated.")
                    status.update(label="Website crawl completed", state="complete", expanded=False)
                    st.success(f"Success • {data.get('pages_crawled', 0)} page(s) crawled • {elapsed}s")
                    st.markdown("### Website summary")
                    st.write(summary)
                    st.markdown("### Extracted JSON")
                    st.json(data)
                    st.download_button(
                        "Download extracted JSON",
                        data=json.dumps(data, ensure_ascii=False, indent=2),
                        file_name="webpilot_extraction.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    logs = (
                        f"$ {PYTHON} cli/crawler.py --url {url.strip()} --max-pages 5\n"
                        f"Exit code: {completed.returncode}\n"
                        f"Duration: {elapsed}s\n\nSTDERR:\n{completed.stderr or '(empty)'}"
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"**Crawl completed successfully.** {data.get('pages_crawled', 0)} page(s) were processed in {elapsed} seconds.\n\n### Summary\n{summary}",
                        "json": data,
                        "logs": logs
                    })
                    with st.expander("Execution details"):
                        st.code(logs)
                else:
                    status.update(label="CLI execution failed", state="error", expanded=True)
                    error_text = completed.stderr.strip() or completed.stdout.strip() or "Crawler returned a non-zero exit code."
                    st.error("The crawler could not complete the task.")
                    st.code(error_text)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"**Execution failed.** The crawler returned exit code {completed.returncode}.",
                        "logs": f"Exit code: {completed.returncode}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                    })
            except subprocess.TimeoutExpired:
                status.update(label="Execution timed out", state="error", expanded=True)
                st.error("The task exceeded the 60-second execution limit.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Execution timed out after 60 seconds. Try a smaller or faster website."
                })
            except json.JSONDecodeError:
                status.update(label="Invalid CLI output", state="error", expanded=True)
                st.error("The crawler returned output that was not valid JSON.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "The crawler output could not be parsed as JSON. Check the execution logs."
                })
            except Exception as exc:
                status.update(label="Unexpected error", state="error", expanded=True)
                st.error(f"Unexpected application error: {exc}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Unexpected application error: {exc}"
                })

st.divider()
st.caption("BuildSprint implementation prototype • Real CLI process execution • Results are based on pages successfully fetched")
