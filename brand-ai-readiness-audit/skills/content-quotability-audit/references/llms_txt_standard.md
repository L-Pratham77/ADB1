# The `/llms.txt` Standard for Machine Consumption

The `/llms.txt` standard is an open community specification designed to provide large language models and autonomous AI agents with clean, curated, markdown-formatted summaries of a domain's capabilities, APIs, and key pages.

---

## 1. Why `/llms.txt` Matters for AI Discoverability

Just as `robots.txt` guides web crawlers on where they can go, and `sitemap.xml` provides a list of URLs, `/llms.txt` provides LLMs with a curated, high-signal, zero-noise index of what the site is, how to use it, and where the authoritative facts live.

When an AI assistant or coding agent is asked about a product or framework, checking for `/llms.txt` allows it to bypass HTML bloat, CSS stylesheets, navigation menus, and banner noise, ingesting the core facts instantly.

---

## 2. Standard File Format

The file is served at the root: `https://example.com/llms.txt` in clean UTF-8 plain markdown text.

```markdown
# Acme Technologies

> Acme Technologies provides enterprise automated data pipeline orchestration and telemetry analytics for modern data warehouses.

## Core Products
- [Acme Orchestrator](https://example.com/docs/orchestrator): Sub-second workflow scheduling engine supporting dbt and Apache Spark.
- [Acme Telemetry Engine](https://example.com/docs/telemetry): Real-time cost monitoring and lineage tracking for BigQuery.

## Pricing & Tiers
- [Pricing Overview](https://example.com/pricing): Tier 1 Free Developer ($0), Tier 2 Team ($49/mo), Tier 3 Enterprise ($299/mo).

## Technical Specifications
- Supported Languages: Python 3.9+, SQL, Go, Rust.
- Compliance: SOC-2 Type II, HIPAA, GDPR certified.
- Deployment: Kubernetes, AWS ECS, GCP Cloud Run, Docker.

## Optional Documentation
- [Full LLM Markdown Bundle](https://example.com/llms-full.txt): Complete consolidated technical documentation for context ingestion.
```

---

## 3. Evaluation Criteria for `/llms.txt`

1. **Existence**: Served at `/llms.txt` with HTTP status 200.
2. **Content-Type**: `text/plain` or `text/markdown`.
3. **Structure**: Includes H1 title, blockquote summary, and bulleted sections with Markdown links.
4. **Fact Density**: Free of marketing buzzwords; contains concrete specs, prices, and capabilities.
