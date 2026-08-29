from turtle import title

import requests
import json

from urllib.parse import urlparse
from bs4 import BeautifulSoup

from db.database import save_tool_call

from langchain.tools import ToolRuntime, tool


with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["html_crawler_tool"])
def crawl_html_page(
    url: str,
    runtime: ToolRuntime,
) -> str:
    writer = runtime.stream_writer
    thread_id = runtime.config["configurable"]["thread_id"]

    writer(f"Opening HTML page: {url}")

    parsed_url = urlparse(url)

    if parsed_url.scheme not in ("http", "https"):
        return "Invalid URL. Only HTTP and HTTPS URLs are supported."

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
        )
    }

    try:
        writer("Sending request to webpage")

        response = requests.get(
            url=url,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/pdf" in content_type:
            return (
                "This URL contains a PDF document. "
                "Use the PDF extraction tool instead."
            )

        if "text/html" not in content_type:
            return f"Unsupported content type: {content_type}"

        writer("HTML page received")

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove content that is normally not useful.
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "nav",
                "footer",
                "header",
                "form",
                "svg",
            ]
        ):
            tag.decompose()

        title = "No title"

        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        page_text = soup.get_text(
            separator="\n",
            strip=True,
        )

        # Remove empty and repeated-looking whitespace.
        clean_lines = []

        for line in page_text.splitlines():
            line = line.strip()

            if line:
                clean_lines.append(line)

        clean_text = "\n".join(clean_lines)

        # Avoid sending an extremely large page to the agent.
        max_characters = 20_000
        clean_text = clean_text[:max_characters]

        writer("\n========== HTML CRAWL RESULT ==========")
        writer(f"Title: {title}")
        writer(f"URL: {url}")
        writer(f"Extracted characters: {len(clean_text)}")
        writer(clean_text[:500])
        writer("=======================================")

        tool_output = f"""
Title: {title}
URL: {url}

Extracted content:
{clean_text}
""".strip()

        save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="crawl_html_page",
            tool_input=url,
            tool_output=tool_output,
        )

        return tool_output

    except requests.exceptions.RequestException as error:
        writer(f"HTML crawling failed: {error}")

        return f"HTML crawling failed: {error}"