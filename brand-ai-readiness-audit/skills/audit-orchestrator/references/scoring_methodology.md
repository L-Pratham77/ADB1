# Scoring Methodology & Prioritization Rubric

This reference defines how findings are classified by severity, how suggested actions are prioritized, how composite scores and domain sub-scores are computed, and how proactive recommendations are synthesized.

---

## 1. Severity Classification Matrix

| Severity Level | Definition | AI Discoverability Impact | On-Site Engagement Impact | Typical Example |
|---|---|---|---|---|
| **Critical** | Fatal blocker preventing content ingestion, rendering, or crawler access. | 100% invisible to AI search; citation agents fail retrieval or receive 4xx/5xx/WAF barrier. | Site crashes or serves blank white page to users without client JavaScript hydration. | `Disallow: /` for `ChatGPT-User` or `PerplexityBot`; WAF interstitial challenge; empty `#root` container. |
| **High** | Major structural defect severely degrading machine understanding or visitor retention. | AI assistants hallucinate facts or miss key products/pricing due to lack of schema or locked facts. | Visitors bounce within 5 seconds due to missing value proposition or missing primary CTA. | 0 JSON-LD schemas; pricing data trapped in images without alt text; missing H1 headline. |
| **Medium** | Measurable friction or dilution causing suboptimal retrieval ranking or cognitive load. | Lower cosine similarity in RAG embeddings; entity confusion across competitors; missing OpenGraph snippet tags. | Slower comprehension due to dense walls of text, vague CTA copy, or multiple competing H1s. | Missing `sameAs` entity links; marketing buzzword density > 2%; dense paragraphs > 95 words; missing OpenGraph metadata. |
| **Low** | Non-critical hygiene or forward-looking optimization. | Minor indexation delay or loss of secondary metadata. | Minor scannability defect or accessibility warning. | Skipped heading level (H1->H3) or orphaned structural tags. |
| **Info** | Informational baseline confirmation or positive engagement signal. | No impact on score; serves as empirical evidence of positive baseline. | No impact on score. | Excellent On-Site Engagement & Visitor Orientation; Clear Call-to-Action detected. |

---

## 2. Quantitative Scoring Model (0–100)

To provide non-experts and executive stakeholders with immediate clarity, the audit calculates a weighted **AI-Readiness Score** alongside domain sub-scores:

### Severity Deductions
* **Critical**: -25 points per finding
* **High**: -15 points per finding
* **Medium**: -6 points per finding
* **Low**: -2 points per finding
* **Info**: -0 points per finding

$$\text{Score} = \max(0, \min(100, 100 - \sum \text{Deductions}))$$

### Domain Sub-Scores
1. **`discoverability` (0–100)**:
   - Evaluates crawler access (robots.txt, WAFs, CSR hydration), semantic Schema.org entity authority, factual quotability, and OpenGraph citation preview tags.
2. **`engagement` (0–100)**:
   - Evaluates above-the-fold value proposition clarity, headline hierarchy, call-to-action (CTA) prominence, and layout scannability.

---

## 3. Action Prioritization Logic

Remediation priority directly mirrors defect severity:
1. **Critical Actions First**: Clear crawler blocks and ensure server-rendered HTML delivery. If machines cannot read the page, no downstream optimization matters.
2. **High Actions Second**: Expose core entities, pricing, and products via Schema.org JSON-LD; unlock non-text facts; establish above-the-fold value proposition.
3. **Medium Actions Third**: Implement OpenGraph preview tags, reduce marketing buzzwords, add structured FAQ blocks, and clean up cognitive friction points.
4. **Low Actions / Proactive Improvements**: Implement `/llms.txt`, add breadcrumb schemas, and refine heading hierarchies.

---

## 4. Proactive Beyond-Defect Recommendations

In accordance with the hackathon specification, suggestions go beyond detected problems to proactively strengthen AI discoverability and engagement even where no defect was found:
* **Curated `/llms.txt` Index**: Providing clean markdown indexes for AI agents.
* **Canonical Wikidata Knowledge Graph Triples**: Connecting corporate entities to permanent Wikidata QIDs.
* **Direct FAQ Schema Injection**: Pre-formatting answers to high-frequency conversational search queries.
* **Context-Preserving Landing Experience**: Ensuring AI-referred visitors land on pages with clear breadcrumbs and immediate value reinforcement.
