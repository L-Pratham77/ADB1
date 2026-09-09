---
name: content-quotability-audit
description: Audit web content for AI assistant retrieval (RAG) quotability, signal-to-noise ratio, marketing buzzword bloat, facts trapped in raster images, opening definition clarity, and /llms.txt support. Use when diagnosing why an AI assistant drops or fails to quote facts from a website.
license: Apache-2.0
metadata:
  version: "1.0.0"
  category: "ai-discoverability"
  framework: "agentskills.io"
---

# Content Quotability & RAG Retrieval Audit

Audits the degree to which on-page content can be parsed, extracted, and accurately quoted by AI search engines and RAG retrieval pipelines.

## When to use
- When an AI assistant recognizes a brand but hallucinates details or cannot quote pricing/features accurately.
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
5. **Modern AI Discovery Standards (`/llms.txt`)**:
   - Verify if domain serves an `/llms.txt` file at the root.

## Output
Emits finding dictionaries complying with the standardized schema:
```json
[
  {
    "title": "Critical factual data (pricing/specs/tables) locked in raster images without alt text",
    "severity": "high",
    "evidence": "Discovered image(s) matching pricing/tables lacking alt text.",
    "suggested_action": {
      "summary": "Convert visual diagrams and pricing graphics into native semantic HTML tables.",
      "priority": "high"
    }
  }
]
```

## References & Scripts
- RAG Quotability Rules: [`references/rag_quotability_rules.md`](references/rag_quotability_rules.md)
- `/llms.txt` Specification: [`references/llms_txt_standard.md`](references/llms_txt_standard.md)
- Executable Analyzer: [`scripts/quotability_analyzer.py`](scripts/quotability_analyzer.py)
