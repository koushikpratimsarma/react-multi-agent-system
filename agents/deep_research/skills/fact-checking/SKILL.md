---
name: fact-checking
description: Verify important research claims using multiple independent sources, identify conflicting evidence, and distinguish confirmed facts from unsupported assertions. Use when comparing frameworks, evaluating techniques, or making evidence-based claims.
---

# Fact-Checking Skill

## Purpose

Improve research reliability by verifying important claims against trustworthy sources.

## When to Apply

Use this skill when:
- Comparing AI frameworks, models, or technologies.
- Evaluating technical approaches.
- Making claims that require evidence.
- Multiple sources may disagree.
- Producing research reports with traceable references.

## Available Tools

- `tavily_web_search`: Discover independent sources.
- `crawl_html_page`: Inspect original webpages and primary sources.

Use only tools that are actually available to the agent.

## Verification Workflow

1. Extract important factual claims from the research findings.
2. Search for evidence supporting each claim.
3. Search for contradictory evidence.
4. Prefer official documentation, original research, and primary sources.
5. Check publication dates and whether information is current.
6. Verify that each source actually supports the claim.
7. Avoid relying on multiple websites that merely repeat the same original source.
8. Record disagreements and unresolved uncertainty.

## Verification Status

Assign one of these statuses to each important claim:

- CONFIRMED: Supported by reliable and sufficiently independent evidence.
- DISPUTED: Credible sources provide conflicting evidence.
- INSUFFICIENT EVIDENCE: Available sources do not establish the claim.

## Output Requirements

For every important claim, provide:

- Claim
- Verification status
- Supporting evidence
- Contradictory evidence, if any
- Source title
- Source URL
- Verification notes

Never describe an unsupported claim as confirmed.

Do not invent sources, URLs, or citations.