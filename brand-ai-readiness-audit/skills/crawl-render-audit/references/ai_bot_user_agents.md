# AI Bot User-Agents Reference Guide

This reference documents the key AI search and training web crawlers operating across the ecosystem. When auditing website discoverability for AI assistants, understanding which bot is responsible for what behavior is critical.

---

## 1. Primary AI Web Crawlers & Assistant Fetchers

| Bot User-Agent Token | Operator | Primary Function | Discovery Impact if Blocked |
|---|---|---|---|
| `GPTBot` | OpenAI | Data collection for OpenAI foundation models & search | Blocks OpenAI models from indexing domain content. |
| `ChatGPT-User` | OpenAI | Real-time browsing initiated by ChatGPT user prompts | **Critical**: ChatGPT fails live web-fetch; cannot cite or quote the page in real-time answers. |
| `OAI-SearchBot` | OpenAI | SearchGPT / ChatGPT Search indexation engine | **Critical**: Site completely absent from SearchGPT search results and citations. |
| `ClaudeBot` | Anthropic | Crawling for Claude model training & system context | Prevents Anthropic models from training on or indexing domain data. |
| `Claude-Web` | Anthropic | Real-time web retrieval during Claude user sessions | **Critical**: Claude cannot fetch page content when asked to analyze a URL. |
| `PerplexityBot` | Perplexity AI | Real-time search indexation and verification for Perplexity | **Critical**: Perplexity will not cite the site in answer summaries. |
| `Google-Extended` | Google | Training data collection for Gemini & Vertex AI models | Prevents Gemini training while leaving standard Google Search unaffected. |
| `GoogleOther` | Google | General Google internal automated fetching & RAG | May degrade AI Overviews grounding if blocked. |
| `Applebot-Extended` | Apple | Training data for Apple Intelligence & Siri LLMs | Prevents Apple Intelligence from learning domain knowledge. |
| `Bytespider` | ByteDance | Crawling for Doubao and ByteDance LLMs | Excludes site from ByteDance AI applications. |
| `CCBot` | Common Crawl | Public web crawl used by hundreds of open-source models | Excludes site from Llama, Mistral, DeepSeek, and open model training sets. |
| `cohere-ai` | Cohere | Enterprise RAG and retrieval models | Excludes domain from enterprise AI knowledge bases. |

---

## 2. Common Robots.txt Misconfigurations

### Unintended Blanket Blocks
```txt
# DANGEROUS: Blocks all AI search assistants completely
User-agent: *
Disallow: /api/
Disallow: /private/

# Explicitly blocking AI bots will prevent citations
User-agent: GPTBot
Disallow: /

User-agent: PerplexityBot
Disallow: /
```

### Optimal Configuration for Maximum AI Discoverability
```txt
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /checkout/
Disallow: /cart/

# Explicitly welcome AI Search and citation bots
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Claude-Web
Allow: /

Sitemap: https://example.com/sitemap.xml
```

---

## 3. Crawler-Specific Headers (`X-Robots-Tag`)

Crawlers also obey HTTP headers sent by web servers:
- `X-Robots-Tag: noindex` -> Completely drops the page from AI indices.
- `X-Robots-Tag: nosnippet` -> Prevents AI assistants from quoting text or generating answer snippets.
- `X-Robots-Tag: noarchive` -> May prevent caching in search RAG stores.
