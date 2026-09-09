# Entity Corroboration & Knowledge Graph Authority

This reference explains how modern AI assistants and large language models (LLMs) establish entity identity, resolve ambiguity, and verify factual truth across the open web.

---

## 1. The Core AI Entity Problem: Mistaken Identity & Ambiguity

Large language models represent entities as nodes in high-dimensional semantic spaces and structured knowledge graphs (e.g., Google Knowledge Graph, Microsoft Satori, Wikidata).

When an entity shares a name with other companies, products, or historical terms (e.g. "Apex", "Prism", "Beacon", "Acme"):
1. **Semantic Drift / Bleed**: The AI merges properties of different entities into a single hallucinated entity.
2. **Confidence Drop**: When an AI assistant cannot confidently disambiguate which entity the user is referring to, it hedges or omits the brand from top recommendations.
3. **Stale / Conflicting Claims**: If the brand's own website states one founding date, headquarters, or pricing model, but third-party business directories state another, AI systems downweight the claim due to lack of web consensus.

---

## 2. The Web Agreement Principle

Machines treat a fact as authoritative when:
1. **Independent Corroboration**: Multiple independent, reputable web domains state identical factual triples (e.g. `[Acme] - [Founded In] - [2021]`).
2. **Explicit Canonical Grounding**: The entity's primary domain explicitly links itself to recognized global entity databases via `sameAs`.

---

## 3. The Role of `sameAs` in Schema.org

The `sameAs` attribute in Schema.org is the explicit machine link for entity reconciliation.

### High-Authority Corroboration Targets:
- **Wikidata (`wikidata.org/wiki/Q...`)**: The primary open knowledge base used by Google, Apple, Perplexity, and OpenAI. Having a Wikidata entity linked via `sameAs` provides near-instantaneous knowledge graph disambiguation.
- **Wikipedia (`wikipedia.org/wiki/...`)**: Core pre-training corpus for all foundation models.
- **Crunchbase (`crunchbase.com/organization/...`)**: Authoritative corroboration for venture funding, executive leadership, founding date, and employee count.
- **LinkedIn (`linkedin.com/company/...`)**: High trust for corporate existence and verified headquarters.
- **GitHub (`github.com/...`)**: Essential for technical credibility and developer products.

---

## 4. Entity Disambiguation Checklist

1. Does the homepage include an `Organization` JSON-LD schema?
2. Does the schema contain a `@id` URI (e.g., `https://example.com/#organization`)?
3. Are there at least 3 authoritative `sameAs` URLs pointing to verified external third-party profiles?
4. Is there a clear, single-sentence canonical boilerplate defining the entity's core domain, category, and target audience?
5. Are key company facts (founding year, headquarters location, key offerings) consistent between the footer, about page, and JSON-LD schema?
