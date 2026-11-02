---
name: academic-research
description: Search, retrieve, and analyze academic papers, scientific publications, technical reports, and PDFs. Use when users request literature reviews, academic research, scientific techniques, or research-paper-based answers with citations.
---

# Academic Research Skill

## Purpose

Ground research investigations in academic literature, technical papers, and scientific publications.

## When to Apply

Use this skill when:
- The user asks about academic papers or scientific publications.
- A literature review is required.
- Comparing scientific methods or technical approaches.
- Research findings need academic evidence.
- The user requests citations from research publications.

## Available Tools

- `arxiv_search`: Search academic papers on arXiv.
- `extract_pdf_text`: Extract content from PDF research papers.
- `deep_research_arxiv_search`: Use if this specialized wrapper is available.

Do not assume a tool exists just because it is mentioned here. Check the available tools before using it.

## Research Workflow

1. Identify the main research topic and relevant keywords.
2. Search for relevant academic publications.
3. Prioritize original research papers and primary sources.
4. Examine paper metadata:
   - Title
   - Authors
   - Publication date
   - Abstract
   - URL
5. Extract relevant PDF content when available.
6. Identify the methodology, experiments, results, and limitations.
7. Compare findings across multiple papers.
8. Avoid treating preprints as peer-reviewed publications unless their review status is verified.

## Output Requirements

Provide:
- Paper title
- Authors
- Publication date
- Abstract or a concise summary
- Research methodology
- Important findings
- Limitations
- Original source URL

Clearly distinguish between verified publication details and unavailable information.

Never fabricate paper metadata, citations, or experimental results.