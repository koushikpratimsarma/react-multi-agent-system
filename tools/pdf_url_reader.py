import json
import httpx
import pymupdf

from langchain.tools import ToolRuntime, tool

from db.database import async_save_tool_call


with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)


@tool(description=descriptions["pdf_reader_tool"])
async def extract_pdf_text(
    url: str,
    runtime: ToolRuntime,
) -> str:

    writer = runtime.stream_writer

    thread_id = runtime.config[
        "configurable"
    ]["thread_id"]

    writer(
        f"Opening PDF document: {url}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
        )
    }

    try:

        writer("Downloading PDF")

        async with httpx.AsyncClient(
            timeout=60.0,
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

        if "application/pdf" not in content_type:

            return (
                "This URL does not appear to contain "
                "a PDF. "
                f"Content type: {content_type}"
            )

        writer("PDF downloaded")

        pdf_document = pymupdf.open(
            stream=response.content,
            filetype="pdf",
        )

        extracted_pages = []

        for page_number, page in enumerate(
            pdf_document,
            start=1,
        ):

            page_text = page.get_text(
                "text",
                sort=True,
            )

            if page_text.strip():

                extracted_pages.append(
                    f"""
--- Page {page_number} ---
{page_text}
""".strip()
                )

        pdf_document.close()

        full_text = "\n\n".join(
            extracted_pages
        )

        max_characters = 40_000

        full_text = full_text[
            :max_characters
        ]

        writer(
            "\n========== PDF EXTRACTION RESULT =========="
        )

        writer(
            f"URL: {url}"
        )

        writer(
            f"Pages extracted: "
            f"{len(extracted_pages)}"
        )

        writer(
            f"Extracted characters: "
            f"{len(full_text)}"
        )

        writer(
            full_text[:1500]
        )

        writer(
            "==========================================="
        )

        tool_output = f"""
PDF URL: {url}
Pages extracted: {len(extracted_pages)}

Extracted content:
{full_text}
""".strip()

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="extract_pdf_text",
            tool_input=url,
            tool_output=tool_output,
        )

        return tool_output

    except httpx.RequestError as error:

        writer(
            f"PDF download failed: {error}"
        )

        return (
            f"PDF download failed: {error}"
        )

    except Exception as error:

        writer(
            f"PDF extraction failed: {error}"
        )

        return (
            f"PDF extraction failed: {error}"
        )