---
name: structured-data-entity-audit
description: Audit website structured data, Schema.org JSON-LD and Microdata implementations, entity disambiguation, and knowledge graph corroboration. Use when diagnosing why AI assistants cannot extract structured product attributes, pricing, or brand knowledge triples.
license: Apache-2.0
allowed-tools: [python, bash]
metadata:
  version: "2.1.0"
  category: "ai-discoverability"
  framework: "agentskills.io"
---

# Structured Data & Entity Authority Audit

Audits whether a website exposes semantic, machine-readable factual triples via Schema.org JSON-LD and grounds its identity in external authoritative knowledge bases.

## When to use
- When AI assistants fail to provide accurate answers about product pricing, features, or company ownership.
- When brand identity is frequently confused with similarly-named competitors or generic terms.
- When preparing an e-commerce or SaaS site for AI search indexing (Perplexity, SearchGPT).

## Inputs
- `target_url` (string, required): The URL to audit.
- `html_content` (string, optional): Raw HTML string for offline evaluation.

## Procedure
1. **Script Block Extraction**:
   - Extract all `<script type="application/ld+json">` tags and Microdata attributes from the HTML.
   - Catch and flag any JSON syntax errors (trailing commas, unescaped quotes).
2. **Schema Type Inventory**:
   - Unpack `@graph` arrays and nested objects.
   - Catalog all Schema.org entity types present (`Organization`, `Product`, `WebSite`, `FAQPage`, `BreadcrumbList`).
3. **Entity Disambiguation & Authority Verification**:
   - Check `Organization` schema for authoritative `sameAs` links pointing to recognized knowledge graphs (Wikidata, Wikipedia, LinkedIn, Crunchbase).
   - Evaluate whether brand claims are grounded to prevent AI hallucination and semantic drift.
4. **Commercial & Pricing Completeness**:
   - Compare page commercial signals (e.g. pricing, currency signs) against presence of `Product` and `Offer` schema.
5. **Action Generation**:
   - Synthesize prioritized fixes with ready-to-use JSON-LD code templates.

## Output
Emits finding objects matching the standardized audit schema:
```json
[
  {
    "title": "Missing 'sameAs' entity corroboration links in Organization schema",
    "severity": "medium",
    "evidence": {
      "detail": "Organization schema found, but 'sameAs' property is missing or empty.",
      "count": 0,
      "fetched_url": "https://example.com"
    },
    "suggested_action": {
      "summary": "Add 'sameAs' array linking to verified external knowledge bases (Wikidata, Wikipedia, LinkedIn).",
      "priority": "medium"
    }
  }
]
```

## References & Scripts
- Schema Templates: [`references/json_ld_templates.md`](references/json_ld_templates.md)
- Entity Disambiguation Guide: [`references/entity_corroboration.md`](references/entity_corroboration.md)
- Executable Inspector: [`scripts/schema_inspector.py`](scripts/schema_inspector.py)
