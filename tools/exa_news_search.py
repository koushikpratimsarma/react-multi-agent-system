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

    writer({
        "event_type": "tool_start",
        "agent": "news_agent",
        "tool": "exa_news_search",
        "message": "Searching Exa News...",
        "input": {
            "query": query,
        },
    })

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
        writer({
            "event_type": "tool_progress",
            "agent": "news_agent",
            "tool": "exa_news_search",
            "message": "Sending request to Exa API",
        })

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        # STREAM SOURCES ONE BY ONE
        for index, result in enumerate(
            results,
            start=1,
        ):

            source = {
                "title": result.get(
                    "title",
                    "No title",
                ),

                "url": result.get(
                    "url",
                    "",
                ),

                "published_date": result.get(
                    "publishedDate",
                    "Not available",
                ),

                "author": result.get(
                    "author",
                    "Not available",
                ),
            }

            # Send this source immediately
            writer({
                "event_type": "source",
                "agent": "news_agent",
                "source_type": "news",
                "index": index,
                "source": source,
            })

        clean_results = format_exa_results(data)
        writer({
            "event_type": "tool_complete",
            "agent": "news_agent",
            "tool": "exa_news_search",
            "message": "Exa News search completed",
            "result_count": len(results),
        })
        # results_output = (
        #     f"\n========== EXA NEWS RESULTS ==========\n"
        #     f"Search query: {query}\n"
        #     f"Total results: {len(data.get('results', []))}\n\n"
        #     f"{clean_results}\n"
        #     f"======================================"
        # )

        # writer(results_output)

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="news_agent",
            tool_name="news_search",
            tool_input=query,
            tool_output=clean_results,
        )

        return clean_results

    except httpx.HTTPStatusError as error:

        status_code = error.response.status_code

        if status_code == 429:

            error_message = (
                "Exa API is rate-limiting requests "
                "(429 Too Many Requests). Try again later."
            )

        elif status_code == 401 or status_code == 403:

            error_message = (
                "Exa API authentication failed "
                f"({status_code}). Check the API key."
            )

        else:

            error_message = (
                f"Exa news search failed with HTTP "
                f"status {status_code}: {error}"
            )

        writer({
            "event_type": "tool_error",
            "agent": "news_agent",
            "tool": "exa_news_search",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="news_agent",
            tool_name="news_search",
            tool_input=query,
            tool_output=error_message,
        )

        return error_message

    except httpx.RequestError as error:

        error_message = (
            f"Exa news search failed: {error}"
        )

        writer({
            "event_type": "tool_error",
            "agent": "news_agent",
            "tool": "exa_news_search",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="news_agent",
            tool_name="news_search",
            tool_input=query,
            tool_output=error_message,
        )

        return error_message
