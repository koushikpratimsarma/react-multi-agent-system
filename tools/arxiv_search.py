import arxiv
import json
from langchain.tools import ToolRuntime, tool



with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["arxiv_search_tool"])
def arxiv_search(
    query: str,
    runtime: ToolRuntime,
) -> str:

    writer = runtime.stream_writer

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

        return clean_results

    except Exception as error:
        writer(f"arXiv search failed: {error}")
        return f"arXiv search failed: {error}"