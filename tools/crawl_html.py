import json
import httpx
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from db.database import async_save_tool_call
from langchain.tools import ToolRuntime, tool

with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["html_crawler_tool"])
async def crawl_html_page(
    url: str,
    runtime: ToolRuntime,
) -> str:

    writer = runtime.stream_writer
    thread_id = runtime.config[
        "configurable"
    ]["thread_id"]

    writer({
        "event_type": "tool_start",
        "agent": "research_agent",
        "tool": "crawl_html_page",
        "message": "Opening HTML page...",
        "input": {
            "url": url,
        },
    })

    parsed_url = urlparse(url)

    if parsed_url.scheme not in (
        "http",
        "https",
    ):
        error_message = (
            "Invalid URL. Only HTTP and HTTPS "
            "URLs are supported."
        )

        writer({
            "event_type": "tool_error",
            "agent": "research_agent",
            "tool": "crawl_html_page",
            "message": error_message,
        })

        return error_message

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
        )
    }

    try:
        writer({
            "event_type": "tool_progress",
            "agent": "research_agent",
            "tool": "crawl_html_page",
            "message": "Sending request to webpage",
        })

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
        ) as client:

            response = await client.get(
                url,
                headers=headers,
            )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "application/pdf" in content_type:

            error_message = (
                "This URL contains a PDF document. "
                "Use the PDF extraction tool instead."
            )

            writer({
                "event_type": "tool_error",
                "agent": "research_agent",
                "tool": "crawl_html_page",
                "message": error_message,
            })

            return error_message

        if "text/html" not in content_type:

            error_message = (
                f"Unsupported content type: "
                f"{content_type}"
            )

            writer({
                "event_type": "tool_error",
                "agent": "research_agent",
                "tool": "crawl_html_page",
                "message": error_message,
            })

            return error_message
        
        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

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

        page_title = "No title"

        if soup.title and soup.title.string:

            page_title = (
                soup.title.string.strip()
            )

        page_text = soup.get_text(
            separator="\n",
            strip=True,
        )

        # Remove empty lines.
        clean_lines = []

        for line in page_text.splitlines():

            line = line.strip()

            if line:
                clean_lines.append(line)

        clean_text = "\n".join(
            clean_lines
        )

        # Avoid sending an extremely large page.
        max_characters = 20_000

        clean_text = clean_text[
            :max_characters
        ]

        writer({
            "event_type": "tool_complete",
            "agent": "research_agent",
            "tool": "crawl_html_page",
            "message": "HTML page crawled successfully",
            "title": page_title,
            "url": url,
            "extracted_characters": len(clean_text),
        })
        
        # crawl_output = (
        #     f"\n========== HTML CRAWL RESULT ==========\n"
        #     f"Title: {page_title}\n"
        #     f"URL: {url}\n"
        #     f"Extracted characters: {len(clean_text)}\n\n"
        #     f"{clean_text[:500]}\n"
        #     f"======================================="
        # )

        #writer(crawl_output)

        tool_output = f"""
Title: {page_title}
URL: {url}

Extracted content:
{clean_text}
""".strip()

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="crawl_html_page",
            tool_input=url,
            tool_output=tool_output,
        )

        return tool_output

    except httpx.RequestError as error:

        error_message = (
            f"HTML crawling failed: {error}"
        )

        writer({
            "event_type": "tool_error",
            "agent": "research_agent",
            "tool": "crawl_html_page",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="crawl_html_page",
            tool_input=url,
            tool_output=error_message,
        )

        return error_message

    