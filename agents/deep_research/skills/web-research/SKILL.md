---
name: web-research
description: Decompose complex questions into searchable sub-questions and conduct multi-source web research. Use for current information, technical comparisons, framework evaluations, product comparisons, and recent developments.
---

# Web Research Skill

## Purpose

Conduct structured, multi-step web research and collect reliable evidence for synthesis.

## When to Apply

Use this skill when:
- A question requires multiple research steps.
- Current information or recent developments are needed.
- Comparing products, frameworks, or technologies.
- Investigating technical topics using multiple webpages.
- Gathering information from different sources.

## Available Tools

- `tavily_web_search`: Search the web for relevant information.
- `crawl_html_page`: Extract content from relevant webpages.
- `deep_research_web_search`: Use if this specialized wrapper is available.

Use only tools actually available to the agent.

## Research Workflow

1. Understand the user's research question.
2. Identify the main objectives.
3. Break the question into smaller searchable sub-questions.
4. Search each sub-question separately.
5. Prioritize official documentation, original sources, and trustworthy publications.
6. Open and examine relevant webpages.
7. Collect supporting evidence and source URLs.
8. Identify outdated information and conflicting findings.
9. Organize the results for final synthesis.

## Output Requirements

For each important finding, provide:

- Finding or claim
- Source title
- Source URL
- Concise summary
- Relevant evidence
- Publication date, when available

Avoid duplicate sources and unsupported conclusions.

Clearly distinguish current information from historical information.