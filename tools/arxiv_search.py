import arxiv
import json
from langchain.tools import ToolRuntime, tool
from db.database import save_tool_call



with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["arxiv_search_tool"])
def arxiv_search(
    query: str,
    runtime: ToolRuntime,
) -> str:

    writer = runtime.stream_writer
    thread_id = runtime.config["configurable"]["thread_id"]

    writer(f"Searching arXiv for: {query}")

    try:
        client = arxiv.Client()

        search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending,
        )

        results = client.results(search)

        papers = []

        for index, result in enumerate(results, start=1):
            authors = ", ".join(
                author.name
                for author in result.authors
            )

            papers.append(
                f"""
Paper: {index}
Title: {result.title}
Authors: {authors}
Published: {result.published}
Abstract: {result.summary}
arXiv ID: {result.get_short_id()}
PDF URL: {result.pdf_url}
""".strip()
            )

        if not papers:
            return "No arXiv papers found."

        clean_results = "\n\n".join(papers)

        writer("\n========== ARXIV SEARCH RESULTS ==========")
        writer(clean_results)
        writer("==========================================")

        save_tool_call(
            thread_id=thread_id,
            agent_name="arxiv_agent",
            tool_name="arxiv_search",
            tool_input=query,
            tool_output=clean_results,
        )

        return clean_results

    except Exception as error:
        writer(f"arXiv search failed: {error}")
        return f"arXiv search failed: {error}"