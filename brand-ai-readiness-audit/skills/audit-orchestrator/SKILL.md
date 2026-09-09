---
name: audit-orchestrator
description: Master entrypoint skill for Brand AI-Readiness and On-Site Engagement audits. Coordinates specialized domain skills (crawl-render, structured data, content quotability, on-site engagement), aggregates empirical evidence, normalizes severity ratings, prioritizes corrective actions, and emits the standardized JSON audit report.
license: Apache-2.0
allowed-tools: [python, bash]
metadata:
  version: "1.0.0"
  category: "orchestration"
  entrypoint: true
  framework: "agentskills.io"
---

# Audit Orchestrator (Entrypoint Skill)

The designated entrypoint skill for the Brand AI-Readiness Audit Marketplace. It manages the full lifecycle of an automated website audit, invoking domain-specific skills, assembling evidence-backed findings, prioritizing remediation actions, synthesizing proactive beyond-defect improvements, and emitting a validated JSON report.

## When to use
- Whenever auditing any website domain for AI discoverability and on-site visitor retention.
- When an AI agent receives an audit prompt or URL to evaluate.
- As the single entrypoint invoked by the marketplace runtime.

## Inputs
- `target` (string, required): Domain or URL to audit (e.g. `https://example.com` or `example.com`).
- `offline_html` (string, optional): Local path or raw string of server-rendered HTML for offline/sandboxed evaluation.
- `offline_robots` (string, optional): Local path or raw string of robots.txt content for offline evaluation.

## Procedure
1. **Target Ingestion & Preflight**:
   - Normalize target URL to standard `https://` protocol.
   - Extract canonical hostname for site identity.
2. **Execute Domain Audits**:
   - **Crawl & Render**: Invoke `crawl-render-audit` to detect AI bot directives in `robots.txt`, HTTP headers (`X-Robots-Tag`), meta tags, and client-side rendering (CSR) hydration gaps.
   - **Structured Data & Entity Authority**: Invoke `structured-data-entity-audit` to inspect Schema.org JSON-LD, entity disambiguation via `sameAs`, and product/pricing schemas.
   - **Content Quotability & RAG Retrieval**: Invoke `content-quotability-audit` to assess fact-to-jargon ratio, non-text locked facts, definition statements, and `/llms.txt`.
   - **On-Site Engagement & Retention**: Invoke `on-site-engagement-audit` to evaluate above-the-fold value proposition, CTA clarity, heading hierarchy, and cognitive friction.
3. **Harmonize & Deduplicate**:
   - Combine all findings, remove duplicate or overlapping alerts, and assign unique sequential identifiers (`F-001`, `F-002`, ...).
   - Order findings deterministically by severity (`critical` -> `high` -> `medium` -> `low`).
4. **Synthesize Proactive Improvements**:
   - Generate proactive recommendations that strengthen AI discoverability and engagement even where no defect was detected (e.g. curated `/llms.txt` and Wikidata entity linking).
5. **Enforce Schema & Emit Report**:
   - Compute severity totals (`total_findings`, `critical`, `high`, `medium`, `low`).
   - Validate structure against [`references/audit_report_schema.json`](references/audit_report_schema.json).
   - Emit standard JSON output.

## Output
Emits the standardized audit report matching the hackathon specification:
```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "title": "No JSON-LD structured data on product pages",
      "severity": "high",
      "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
      "suggested_action": {
        "summary": "Add Product/Offer JSON-LD to every product page.",
        "priority": "high"
      }
    }
  ],
  "proactive_recommendations": [
    {
      "area": "AI Discoverability",
      "title": "Publish Curated /llms.txt Machine Index",
      "impact": "Enables AI agents to ingest product specs without parsing complex HTML/CSS.",
      "action": "Create https://example.com/llms.txt with markdown summaries."
    }
  ]
}
```

## References & Scripts
- JSON Schema Specification: [`references/audit_report_schema.json`](references/audit_report_schema.json)
- Scoring Rubric: [`references/scoring_methodology.md`](references/scoring_methodology.md)
- Executable Runner: [`scripts/orchestrate.py`](scripts/orchestrate.py)
- Report Formatter: [`scripts/report_formatter.py`](scripts/report_formatter.py)
