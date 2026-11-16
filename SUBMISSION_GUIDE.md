# Final submission checklist and short demo script

## Before submitting
- [ ] Run the app locally and complete a real crawl of `https://example.com`.
- [ ] Confirm the summary and JSON appear.
- [ ] Test an invalid URL such as `ftp://example.com`.
- [ ] Create a public GitHub repository and push this project.
- [ ] Record one 4–7 minute video showing the real app execution.
- [ ] Paste the GitHub link, demo video link, and any required access instructions into the official form.

## Suggested video script (speak naturally)

**Introduction (30–45 seconds)**  
"Hello, this is WebPilot AI. It is a chat-based website research prototype. It converts a user's website research request into a controlled command-line task, executes it, and returns extracted information in a readable summary and JSON."

**Architecture (60 seconds)**  
"The Streamlit interface collects the website URL and task. The backend validates the URL and identifies the requested actions. It then starts the Python crawler as a separate CLI process using subprocess. The crawler uses Requests and BeautifulSoup to fetch public HTML pages and extract titles, descriptions, headings, text, and links."

**Live demo (2–3 minutes)**  
"I will use https://example.com as the test website. I enter the request and run it. The backend launches the CLI, captures standard output and errors, checks the exit code, and parses the JSON. The interface shows the actual crawl status, summary, extracted JSON, and execution details."

**Reliability and security (45–60 seconds)**  
"The prototype accepts only HTTP and HTTPS URLs, rejects embedded credentials and local hostnames, checks robots.txt, stays on the original host, limits the crawl to five pages, uses request and process timeouts, and does not pass user text into a shell command. Invalid input and execution failures are shown as errors."

**Closing (15 seconds)**  
"This is the current working prototype. The summary is extractive and the crawler may not work on websites that block automated requests or require JavaScript."

## Important disclosure
In your README and video, accurately mention any AI coding assistants or external services you actually used. Do not claim that an LLM API is integrated: this version uses a lightweight local intent-understanding layer and extractive summarization.
