---
name: content-quotability-audit
description: Audit web content for AI assistant retrieval (RAG) quotability, signal-to-noise ratio, marketing buzzword bloat, facts trapped in raster images, opening definition clarity, OpenGraph citation card metadata, and /llms.txt support. Use when diagnosing why an AI assistant drops or fails to quote facts from a website.
license: Apache-2.0
allowed-tools: [python, bash]
metadata:
  version: "1.0.0"
  category: "ai-discoverability"
  framework: "agentskills.io"
---

# Content Quotability & RAG Retrieval Audit

Audits the degree to which on-page content can be parsed, extracted, cited, and previewed by AI search engines (ChatGPT Search, Perplexity, Claude Web) and RAG retrieval pipelines.

## When to use
- When an AI assistant recognizes a brand but hallucinates details or cannot quote pricing/features accurately.
- When AI search citation cards show empty preview cards or missing snippets.
- When key product matrices, diagrams, or comparisons are represented in images without text equivalents.
- When text suffers from high marketing jargon density that dilutes vector embedding relevance.

## Inputs
- `target_url` (string, required): URL of the page to evaluate.
- `html_content` (string, optional): Raw HTML string for offline evaluation.

## Procedure
1. **Non-Text Locked Fact Detection**:
   - Inspect all `<img>` tags for missing or placeholder `alt` text.
   - Specifically flag images whose filenames or context indicate architecture diagrams, pricing tables, or feature lists.
2. **Signal-to-Noise & Jargon Density**:
   - Tokenize visible text and compute the density percentage of high-abstraction filler buzzwords.
   - Flag pages exceeding the 2.0% jargon threshold that risk dilution during LLM chunking.
3. **Atomic Entity Definition Check**:
   - Inspect opening content for a clear declarative definition sentence stating the brand's identity and primary domain.
4. **Conversational Q&A / FAQ Structure**:
   - Check for question-format headings matching natural-language user queries.
5. **OpenGraph Citation Card Metadata**:
   - Inspect `<head>` for `<meta property="og:title">`, `<meta property="og:description">`, and `<meta property="og:image">` tags used by AI assistants to construct rich citation cards.
6. **Modern AI Discovery Standards (`/llms.txt`)**:
   - Verify if domain serves a valid `/llms.txt` file at the root.

## Output
Emits finding dictionaries complying with the standardized schema:
```json
[
  {
    "title": "Missing OpenGraph (og:title, og:description) metadata for AI search citation cards",
    "severity": "medium",
    "evidence": "Page lacks og:title and og:description. AI assistant search cards rely on OpenGraph tags to render rich preview snippets.",
    "suggested_action": {
      "summary": "Add OpenGraph meta tags in <head> for crisp, branded citation card previews in AI assistants.",
      "priority": "medium",
      "remediation_details": "<meta property=\"og:title\" content=\"Page Title\">\n<meta property=\"og:description\" content=\"1-2 sentence overview.\">\n<meta property=\"og:image\" content=\"https://example.com/og-card.png\">"
    }
  }
]
```

## References & Scripts
- RAG Quotability Rules: [`references/rag_quotability_rules.md`](references/rag_quotability_rules.md)
- `/llms.txt` Specification: [`references/llms_txt_standard.md`](references/llms_txt_standard.md)
- Executable Analyzer: [`scripts/quotability_analyzer.py`](scripts/quotability_analyzer.py)
