import json
import httpx
import xml.etree.ElementTree as ET
from langchain.tools import ToolRuntime, tool
from db.database import async_save_tool_call

with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["arxiv_search_tool"])
async def arxiv_search(
    query: str,
    runtime: ToolRuntime,
) -> str:
   
    thread_id = runtime.config["configurable"]["thread_id"]
    writer = runtime.stream_writer

    writer({
        "event_type": "tool_start",
        "agent": "arxiv_agent",
        "tool": "arxiv_search",
        "message": "Searching arXiv...",
        "input": {
            "query": query,
        },
    })

    url = "https://export.arxiv.org/api/query"

    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": 5,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.get(
                url,
                params=params,
            )
            response.raise_for_status()
            xml_data = response.text

        # PARSE ARXIV XML
        root = ET.fromstring(xml_data)
        namespace = {
            "atom": "http://www.w3.org/2005/Atom"
        }
        results = []

        for index, entry in enumerate(
            root.findall("atom:entry", namespace),
            start=1,
        ):
            title = entry.findtext(
                "atom:title",
                default="",
                namespaces=namespace,
            ).strip()

            summary = entry.findtext(
                "atom:summary",
                default="",
                namespaces=namespace,
            ).strip()

            published = entry.findtext(
                "atom:published",
                default="",
                namespaces=namespace,
            ).strip()

            paper_url = entry.findtext(
                "atom:id",
                default="",
                namespaces=namespace,
            ).strip()

            authors = []

            for author in entry.findall(
                "atom:author",
                namespace,
            ):

                name = author.findtext(
                    "atom:name",
                    default="",
                    namespaces=namespace,
                )

                if name:
                    authors.append(name)

            # STREAM ONE SOURCE AT A TIME
            source = {
                "title": title or "Untitled paper",

                "url": paper_url,

                "published_date": (
                    published
                    if published
                    else "Not available"
                ),

                "author": (
                    ", ".join(authors)
                    if authors
                    else "Not available"
                ),
            }

            writer({
                "event_type": "source",

                "agent": "arxiv_agent",

                "source_type": "paper",

                "index": index,

                "source": source,
            })

            # STORE RESULT FOR LLM
            results.append(
                f"""
Title: {title}
Authors: {", ".join(authors)}
Published: {published}
Summary: {summary}
URL: {paper_url}
""".strip()
            )

        # FINAL TOOL RESULT
        if not results:

            final_answer = (
                f"No arXiv papers found for: {query}"
            )

        else:

            final_answer = "\n\n".join(
                results
            )
        writer({
            "event_type": "tool_complete",
            "agent": "arxiv_agent",
            "tool": "arxiv_search",
            "message": "arXiv search completed",
            "result_count": len(results),
        })
        # DATABASE
        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="arxiv_agent",
            tool_name="arxiv_search",
            tool_input=query,
            tool_output=final_answer,
        )
        return final_answer
    
    except httpx.RequestError as error:

        error_message = (
            f"arXiv request failed: {error}"
        )

        writer({
        "event_type": "tool_error",
        "agent": "arxiv_agent",
        "tool": "arxiv_search",
        "message": error_message,
    })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="arxiv_agent",
            tool_name="arxiv_search",
            tool_input=query,
            tool_output=error_message,
        )

        return error_message

    except Exception as error:

        error_message = (
            f"arXiv search failed: {error}"
        )
        writer({
            "event_type": "tool_error",
            "agent": "arxiv_agent",
            "tool": "arxiv_search",
            "message": error_message,
        })
       
        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="arxiv_agent",
            tool_name="arxiv_search",
            tool_input=query,
            tool_output=error_message,
        )

        return error_message