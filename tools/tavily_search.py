import json
import requests

from langchain.tools import ToolRuntime, tool

from config import TAVILY_API_KEY

TAVILY_TOOL_DESCRIPTION = """
Search the web using the Tavily Search API.

Use this tool for:

- weather
- live information
- general web search
- internet facts
- company information
- fact verification
- current web content

Returns:
- title
- summary
- URL
- relevance score

Do not use this tool for breaking news or deep research.

"""


def format_tavily_results(data: dict) -> str:
    results = data.get("results", [])

    if not results:
        return "No search results found."

    formatted_results = []

    for index, result in enumerate(results, start=1):
        title = result.get("title", "No title")
        url = result.get("url", "No URL")
        content = result.get("content", "No content")[:250]
        score = result.get("score")

        score_text = f"{score:.3f}" if score is not None else "Not available"

        formatted_result = f"""
Source: {index}
Title: {title}
Summary: {content}
Score: {score_text}
URL: {url}
""".strip()
    

        formatted_results.append(formatted_result)

    return "\n\n".join(formatted_results)

@tool(description=TAVILY_TOOL_DESCRIPTION)
def tavily_web_search(
    query: str,
    runtime: ToolRuntime,
) -> str:
    writer = runtime.stream_writer

    writer(f"Searching Tavily for: {query}")

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
        writer("Sending request to Tavily API")

        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        writer("Tavily response received")

        data = response.json()

        clean_results = format_tavily_results(data)

        writer("\n========== TAVILY SEARCH RESULTS ==========")
        writer(f"Search query: {query}")
        writer(f"Total results: {len(data.get('results', []))}")
        writer(clean_results)
        writer("===========================================")

        return json.dumps(data, indent=2)

    except requests.exceptions.RequestException as error:
        writer(f"Tavily search failed: {error}")

        return f"Tavily search failed: {error}"
