import json
import httpx

from langchain.tools import ToolRuntime, tool
from db.database import async_save_tool_call

from config import EXA_API_KEY


def format_exa_results(data: dict) -> str:

    results = data.get("results", [])

    if not results:
        return "No news results found."

    formatted_results = []

    for index, result in enumerate(results, start=1):

        title = result.get(
            "title",
            "No title",
        )

        url = result.get(
            "url",
            "No URL",
        )

        published_date = result.get(
            "publishedDate",
            "Not available",
        )

        author = result.get(
            "author",
            "Not available",
        )

        highlights = result.get(
            "highlights",
            [],
        )

        text = result.get(
            "text",
            "",
        )

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

        formatted_results.append(
            formatted_result
        )

    return "\n\n".join(
        formatted_results
    )


with open(
    "descriptions.json",
    "r",
    encoding="utf-8",
) as f:

    descriptions = json.load(f)


@tool(description=descriptions["exa_news_tool"])
async def exa_news_search(
    query: str,
    runtime: ToolRuntime,
) -> str:

    writer = runtime.stream_writer

    thread_id = runtime.config[
        "configurable"
    ]["thread_id"]

    writer(
        f"Searching Exa News for: {query}"
    )

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

        writer(
            "Sending request to Exa API"
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        writer(
            "Exa response received"
        )

        data = response.json()

        clean_results = format_exa_results(
            data
        )

        writer(
            "\n========== EXA NEWS RESULTS =========="
        )

        writer(
            f"Search query: {query}"
        )

        writer(
            f"Total results: "
            f"{len(data.get('results', []))}"
        )

        writer(clean_results)

        writer(
            "======================================"
        )

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="news_agent",
            tool_name="news_search",
            tool_input=query,
            tool_output=clean_results,
        )

        return clean_results

    except httpx.RequestError as error:

        writer(
            f"Exa news search failed: {error}"
        )

        return (
            f"Exa news search failed: {error}"
        )