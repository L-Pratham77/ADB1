# Scoring Methodology & Prioritization Rubric

This reference defines how findings are classified by severity, how suggested actions are prioritized, and how proactive recommendations are synthesized.

---

## 1. Severity Classification Matrix

| Severity Level | Definition | AI Discoverability Impact | On-Site Engagement Impact | Typical Example |
|---|---|---|---|---|
| **Critical** | Fatal blocker preventing content ingestion, rendering, or user access. | 100% invisible to AI search; assistants fail retrieval or report domain error. | Site crashes, returns 4xx/5xx, or serves blank page to users without JS. | `Disallow: /` for `ChatGPT-User` or `PerplexityBot`; empty root container in raw HTML. |
| **High** | Major structural defect severely degrading machine understanding or visitor retention. | AI assistants hallucinate facts or miss key products/pricing due to lack of schema or locked facts. | Visitors bounce within 5 seconds due to missing value proposition or missing primary CTA. | 0 JSON-LD schemas; pricing data trapped in images without alt text; missing H1 headline. |
| **Medium** | Measurable friction or dilution causing suboptimal retrieval ranking or cognitive load. | Lower cosine similarity in RAG embeddings; entity confusion across competitors. | Slower comprehension due to dense walls of text, vague CTA copy, or multiple competing H1s. | Missing `sameAs` entity links; marketing buzzword density > 2%; dense paragraphs > 95 words. |
| **Low** | Non-critical hygiene or forward-looking optimization. | Minor indexation delay or loss of secondary metadata. | Minor scannability defect or accessibility warning. | Missing XML sitemap in robots.txt; skipped heading level (H1->H3); missing `/llms.txt`. |

---

## 2. Action Prioritization Logic

Remediation priority mirrors defect severity:
1. **Critical Actions First**: Clear crawler blocks and ensure basic server-rendered HTML delivery. If machines cannot read the page, no other optimization matters.
2. **High Actions Second**: Expose core entities, pricing, and products via Schema.org JSON-LD; unlock non-text facts; establish above-the-fold value proposition.
3. **Medium Actions Third**: Reduce marketing buzzword fluff, add structured FAQ blocks, and clean up cognitive friction points.
4. **Low Actions / Proactive Improvements**: Implement `/llms.txt`, add breadcrumb schemas, and refine heading hierarchies.

---

## 3. Proactive Beyond-Defect Recommendations

In accordance with the hackathon specification, suggestions may go beyond detected problems to proactively strengthen AI discoverability and engagement even where no defect was found:
- **Autonomous `/llms.txt` Generation**: Providing clean markdown indexes for AI agents.
- **Entity Knowledge Graph Triples**: Proactively connecting corporate entities to Wikidata QIDs.
- **Direct FAQ Schema Injection**: Pre-formatting answers to high-frequency conversational search queries.
- **AI Citation Pre-rendering**: Employing edge caching to guarantee sub-500ms response times for AI fetchers.
