import json
import requests
from langchain.tools import ToolRuntime, tool

from config import EXA_API_KEY


EXA_NEWS_TOOL_DESCRIPTION = """
Search recent news using the Exa Search API.

Use this tool for:
- latest news
- breaking news
- recent events
- company announcements
- financial news
- technology news
- political developments

The tool returns article titles, publication dates, authors,
relevant highlights, extracted text, and source URLs.
"""

def format_exa_results(data: dict) -> str:
    results = data.get("results", [])

    if not results:
        return "No news results found."

    formatted_results = []

    for index, result in enumerate(results, start=1):
        title = result.get("title", "No title")
        url = result.get("url", "No URL")
        published_date = result.get(
            "publishedDate",
            "Not available",
        )
        author = result.get(
            "author",
            "Not available",
        )

        highlights = result.get("highlights", [])
        text = result.get("text", "")

        if highlights:
            content = " ".join(highlights)
        elif text:
            content = text
        else:
            content = "No content available."

        content = content[:500]

        formatted_result = f"""
Source: {index}
Title: {title}
Published Date: {published_date}
Author: {author}
Summary: {content}
URL: {url}
""".strip()

        formatted_results.append(formatted_result)

    return "\n\n".join(formatted_results)


@tool(description=EXA_NEWS_TOOL_DESCRIPTION)
def exa_news_search(
    query: str,
    runtime: ToolRuntime,
) -> str:
    writer = runtime.stream_writer

    writer(f"Searching Exa News for: {query}")

    url = "https://api.exa.ai/search"

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "type": "auto",
        "numResults": 5,
        "contents": {
            "highlights": True,
            "text": {
                "maxCharacters": 300,
            },
        },
    }

    try:
        writer("Sending request to Exa API")

        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        writer("Exa response received")

        data = response.json()

        clean_results = format_exa_results(data)

        writer("\n========== EXA NEWS RESULTS ==========")
        writer(f"Search query: {query}")
        writer(f"Total results: {len(data.get('results', []))}")
        writer(clean_results)
        writer("======================================")

        return json.dumps(data, indent=2)

    except requests.exceptions.RequestException as error:
        writer(f"Exa news search failed: {error}")

        return f"Exa news search failed: {error}"
