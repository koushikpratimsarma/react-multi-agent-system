import json
import httpx
from langchain.tools import ToolRuntime, tool
from config import TAVILY_API_KEY
from db.database import async_save_tool_call

def format_tavily_results(data: dict) -> str:

    results = data.get("results", [])

    if not results:
        return "No search results found."

    formatted_results = []

    for index, result in enumerate(results, start=1):

        title = result.get(
            "title",
            "No title"
        )

        url = result.get(
            "url",
            "No URL"
        )

        content = result.get(
            "content",
            "No content"
        )[:250]

        score = result.get("score")

        score_text = (
            f"{score:.3f}"
            if score is not None
            else "Not available"
        )

        formatted_result = f"""
Source: {index}
Title: {title}
Summary: {content}
Score: {score_text}
URL: {url}
""".strip()

        formatted_results.append(
            formatted_result
        )

    return "\n\n".join(formatted_results)

with open(
    "descriptions.json",
    "r",
    encoding="utf-8"
) as f:

    descriptions = json.load(f)

@tool(description=descriptions["tavily_tool"])
async def tavily_web_search(
    query: str,
    runtime: ToolRuntime,
) -> str:

    writer = runtime.stream_writer
    thread_id = runtime.config["configurable"]["thread_id"]

    writer({
        "event_type": "tool_start",
        "agent": "web_agent",
        "tool": "tavily_web_search",
        "message": "Searching Tavily...",
        "input": {
            "query": query,
        },
    })

    url = "https://api.tavily.com/search"

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "auto_parameters": False,
        "topic": "general",
        "search_depth": "advanced",
        "chunks_per_source": 3,
        "max_results": 5,
        "time_range": None,
        "start_date": None,
        "end_date": None,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "include_favicon": False,
        "include_domains": [],
        "exclude_domains": [],
        "country": None,
        "include_usage": False,
    }

    try:
        writer({
            "event_type": "tool_progress",
            "agent": "web_agent",
            "tool": "tavily_web_search",
            "message": "Sending request to Tavily API",
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

        # STREAM WEB SOURCES ONE BY ONE
        results = data.get("results", [])

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
                    "published_date",
                    "Not available",
                ),
                "author": result.get(
                    "author",
                    "Not available",
                ),
            }

            writer({
                "event_type": "source",
                "agent": "web_agent",
                "source_type": "web",
                "index": index,
                "source": source,
            })

        clean_results = format_tavily_results(
            data
        )

        writer({
            "event_type": "tool_complete",
            "agent": "web_agent",
            "tool": "tavily_web_search",
            "message": "Tavily search completed",
            "result_count": len(results),
        })

        # results_output = (
        #     f"\n========== TAVILY SEARCH RESULTS ==========\n"
        #     f"Search query: {query}\n"
        #     f"Total results: {len(data.get('results', []))}\n\n"
        #     f"{clean_results}\n"
        #     f"==========================================="
        # )

        # writer(results_output)

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="web_agent",
            tool_name="tavily_web_search",
            tool_input=query,
            tool_output=clean_results,
        )

        return clean_results

    except httpx.HTTPStatusError as error:

        status_code = error.response.status_code

        if status_code == 429:

            error_message = (
                "Tavily API is rate-limiting requests "
                "(429 Too Many Requests). Try again later."
            )

        elif status_code == 401 or status_code == 403:

            error_message = (
                "Tavily API authentication failed "
                f"({status_code}). Check the API key."
            )

        else:

            error_message = (
                f"Tavily search failed with HTTP "
                f"status {status_code}: {error}"
            )

        writer({
            "event_type": "tool_error",
            "agent": "web_agent",
            "tool": "tavily_web_search",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="web_agent",
            tool_name="tavily_web_search",
            tool_input=query,
            tool_output=error_message,
        )

        return error_message

    except httpx.RequestError as error:

        error_message = (
            f"Tavily search failed: {error}"
        )

        writer({
            "event_type": "tool_error",
            "agent": "web_agent",
            "tool": "tavily_web_search",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="web_agent",
            tool_name="tavily_web_search",
            tool_input=query,
            tool_output=error_message,
        )

        return error_message
