---
name: crawl-render-audit
description: Audit a website's technical crawlability, robots.txt directives for AI search bots (ChatGPT-User, OAI-SearchBot, Claude-Web, PerplexityBot), HTTP indexation headers, sitemaps, and client-side JavaScript rendering hydration gaps. Use when diagnosing why AI assistants cannot discover, fetch, or render a domain's pages.
license: Apache-2.0
allowed-tools: [python, bash]
metadata:
  version: "1.0.0"
  category: "ai-discoverability"
  framework: "agentskills.io"
---

# Crawl & Render Audit

Evaluates whether automated AI crawlers, retrieval bots, and web assistants can access, parse, and render a website's pages without encountering access blocks or JavaScript rendering traps.

## When to use
- When diagnosing why a brand is missing from AI search engine results (SearchGPT, Perplexity, Claude Web).
- When a website built with client-side frameworks (React, Vue, Angular) fails to appear in AI citations.
- Before launching new domain sections or re-architecting robots.txt rules.

## Inputs
- `target_url` (string, required): Fully qualified URL of the target page (e.g. `https://example.com`).
- `robots_content` (string, optional): Raw robots.txt content for offline simulation.
- `html_content` (string, optional): Raw server-rendered HTML for offline simulation.

## Procedure
1. **Robots.txt Inspection**:
   - Fetch `{domain}/robots.txt`.
   - Parse rules for specific AI search bots (`ChatGPT-User`, `OAI-SearchBot`, `Claude-Web`, `PerplexityBot`) and model training bots (`GPTBot`, `Google-Extended`, `CCBot`).
   - Identify any `Disallow: /` directives that prevent live AI search citations.
   - Verify canonical XML sitemap location is declared.
2. **HTTP Header & Meta Tag Analysis**:
   - Inspect response headers for restrictive `X-Robots-Tag` (`noindex`, `nosnippet`, `noarchive`).
   - Parse raw HTML for `<meta name="robots">` restricting indexing or snippet generation.
3. **Client-Side Rendering (CSR) Hydration Gap Detection**:
   - Analyze initial unhydrated HTML payload.
   - Detect empty single-page application root containers (`#root`, `#app`, `#__next`).
   - Calculate visible text-to-HTML ratio. Flag pages where crucial text is absent from initial response payload.
   - Check for presence of server-rendered semantic `<h1>` headings.
4. **Action Synthesis**:
   - Formulate prioritized, mechanism-sound remediation steps for each detected defect.

## Output
Emits a list of finding dictionaries conforming to the standard schema:
```json
[
  {
    "title": "AI search and citation bots explicitly blocked in robots.txt (ChatGPT-User, PerplexityBot)",
    "severity": "critical",
    "evidence": "robots.txt disallows root access for live assistant citation agents.",
    "suggested_action": {
      "summary": "Allow citation crawlers in robots.txt so AI assistants can verify and cite your domain in user answers.",
      "priority": "critical",
      "remediation_details": "Add explicit permissions for OAI-SearchBot and PerplexityBot."
    }
  }
]
```

## References & Scripts
- AI Bot Index: [`references/ai_bot_user_agents.md`](references/ai_bot_user_agents.md)
- Hydration Pitfalls: [`references/rendering_pitfalls.md`](references/rendering_pitfalls.md)
- Executable Engine: [`scripts/crawler.py`](scripts/crawler.py)
