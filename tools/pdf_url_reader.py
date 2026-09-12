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

    writer({
        "event_type": "tool_start",
        "agent": "research_agent",
        "tool": "extract_pdf_text",
        "message": "Opening PDF document...",
        "input": {
            "url": url,
        },
    })

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
            "tool": "extract_pdf_text",
            "message": "Downloading PDF",
        })

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

            error_message = (
                "This URL does not appear to contain "
                "a PDF. "
                f"Content type: {content_type}"
            )

            writer({
                "event_type": "tool_error",
                "agent": "research_agent",
                "tool": "extract_pdf_text",
                "message": error_message,
            })

            return error_message

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

        writer({
            "event_type": "tool_complete",
            "agent": "research_agent",
            "tool": "extract_pdf_text",
            "message": "PDF extraction completed",
            "url": url,
            "pages_extracted": len(extracted_pages),
            "extracted_characters": len(full_text),
        })
        # pdf_output = (
        #     f"\n========== PDF EXTRACTION RESULT ==========\n"
        #     f"URL: {url}\n"
        #     f"Pages extracted: {len(extracted_pages)}\n"
        #     f"Extracted characters: {len(full_text)}\n\n"
        #     f"{full_text[:1500]}\n"
        #     f"==========================================="
        # )

        # writer(pdf_output)

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

    except httpx.HTTPStatusError as error:

        status_code = error.response.status_code

        if status_code == 429:

            error_message = (
                "The website is rate-limiting requests "
                "(429 Too Many Requests). Try again later "
                "or use a different source."
            )

        elif status_code == 403:

            error_message = (
                "The website blocked access "
                "(403 Forbidden). Try a different source."
            )

        elif status_code == 404:

            error_message = (
                "The PDF was not found "
                "(404 Not Found). Try a different URL."
            )

        else:

            error_message = (
                f"PDF download failed with HTTP "
                f"status {status_code}: {error}"
            )

        writer({
            "event_type": "tool_error",
            "agent": "research_agent",
            "tool": "extract_pdf_text",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="extract_pdf_text",
            tool_input=url,
            tool_output=error_message,
        )

        return error_message

    except httpx.RequestError as error:

        error_message = (
            f"PDF download failed: {error}"
        )

        writer({
            "event_type": "tool_error",
            "agent": "research_agent",
            "tool": "extract_pdf_text",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="extract_pdf_text",
            tool_input=url,
            tool_output=error_message,
        )

        return error_message

    except Exception as error:

        error_message = (
            f"PDF extraction failed: {error}"
        )

        writer({
            "event_type": "tool_error",
            "agent": "research_agent",
            "tool": "extract_pdf_text",
            "message": error_message,
        })

        await async_save_tool_call(
            thread_id=thread_id,
            agent_name="research_agent",
            tool_name="extract_pdf_text",
            tool_input=url,
            tool_output=error_message,
        )

        return error_message