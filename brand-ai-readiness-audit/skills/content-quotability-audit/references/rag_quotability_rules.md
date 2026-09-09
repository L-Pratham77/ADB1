# RAG Quotability Rules & Fact Extraction Dynamics

This reference documents how modern Retrieval-Augmented Generation (RAG) pipelines in AI assistants (ChatGPT, Perplexity, Claude, Copilot) process web content and select sources to quote in generated answers.

---

## 1. How RAG Pipelines Ingest and Quote Web Pages

When an AI assistant retrieves a web page during a live search query:

```mermaid
graph LR
    A[Raw Web Page] --> B[HTML Stripper & Markdown Converter]
    B --> C[Chunking Engine (256-512 Tokens)]
    C --> D[Embedding & Dense Retrieval]
    D --> E[Cross-Encoder Reranker]
    E --> F[Top-K Context Ingestion]
    F --> G[Synthesizer / Generator]
```

1. **Chunk Splitting**: The retriever splits page text into small chunks (typically 256–512 tokens).
2. **Dense Vector Matching**: If a factual assertion (e.g. *"Acme starts at $29/user/month and supports PostgreSQL 15"*) is diluted across 300 words of generic marketing jargon, the cosine similarity of the chunk to the user's question drops below the retrieval threshold.
3. **Cross-Encoder Reranking**: Rerankers score chunks based on direct answerability. A chunk that starts with a clear answer sentence is heavily prioritized over one requiring multi-paragraph inference.
4. **Context Truncation**: When generating the final answer, LLMs select short, high-confidence snippets to quote and cite with bracketed links `[1]`.

---

## 2. The Three Core Quotability Principles

### Principle 1: Inverted Pyramid & Atomic Definitions
- **Bad (Unquotable)**:
  > "In today's fast-paced, hyper-connected digital landscape, modern teams demand next-generation paradigms to unlock true synergy across workflows." *(0 extractable facts)*
- **Good (Highly Quotable)**:
  > "Acme Orchestrator is a cloud-native workflow scheduler designed for Python and SQL data pipelines. It supports automated retry policies, OpenLineage tracking, and sub-second task triggers." *(5 clear extractable facts in 2 sentences)*

### Principle 2: Self-Contained Factual Triples
Each paragraph or section must retain its subject. Avoid dangling pronouns ("It allows you to...", "We offer..."). State the brand or feature name explicitly so chunks stand alone when isolated during retrieval.

### Principle 3: Structured Tabular Specifications
RAG engines convert HTML `<table>` elements into Markdown tables or JSON strings. Tables comparing features, pricing tiers, or system requirements are overwhelmingly favored by LLMs when answering comparison queries.

---

## 3. The Non-Text Trap (Locked Facts)

AI search engines cannot reliably run OCR on images during sub-second web searches.

- **Failure Pattern**: Publishing pricing tiers, technical architectures, or feature comparison matrices inside PNG/JPEG screenshots or SVG diagrams without complete semantic HTML equivalents or detailed `alt` text.
- **Rule**: Every infographic, architecture diagram, or comparison matrix must have an accompanying HTML table or descriptive textual breakdown.
