import requests
import pymupdf
import json
from langchain.tools import ToolRuntime, tool


with open("descriptions.json", "r", encoding="utf-8") as f:
    descriptions = json.load(f)

@tool(description=descriptions["pdf_reader_tool"])
def extract_pdf_text(
    url: str,
    runtime: ToolRuntime,
) -> str:
    writer = runtime.stream_writer

    writer(f"Opening PDF document: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0 Safari/537.36"
        )
    }

    try:
        writer("Downloading PDF")

        response = requests.get(
            url=url,
            headers=headers,
            timeout=60,
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "application/pdf" not in content_type:
            return (
                "This URL does not appear to contain a PDF. "
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
            page_text = page.get_text("text", sort=True)

            if page_text.strip():
                extracted_pages.append(
                    f"""
--- Page {page_number} ---
{page_text}
""".strip()
                )

        pdf_document.close()

        full_text = "\n\n".join(extracted_pages)

        max_characters = 40_000
        full_text = full_text[:max_characters]

        writer("\n========== PDF EXTRACTION RESULT ==========")
        writer(f"URL: {url}")
        writer(f"Pages extracted: {len(extracted_pages)}")
        writer(f"Extracted characters: {len(full_text)}")
        writer(full_text[:1500])
        writer("===========================================")

        return f"""
PDF URL: {url}
Pages extracted: {len(extracted_pages)}

Extracted content:
{full_text}
""".strip()

    except requests.exceptions.RequestException as error:
        writer(f"PDF download failed: {error}")

        return f"PDF download failed: {error}"

    except Exception as error:
        writer(f"PDF extraction failed: {error}")

        return f"PDF extraction failed: {error}"