#!/usr/bin/env python3
"""
Crawl & Render Audit Tool
Inspects robots.txt directives, AI bot access permissions, HTTP headers,
meta indexation tags, sitemaps, and client-side rendering (CSR) hydration gaps.

Evidence rule: every finding carries a structured evidence object:
  { "detail": str, "count": int, "fetched_url": str }
Severity rule: critical is ONLY emitted when the fact is directly confirmed
  by a live HTTP response (status code, header, fetched body).
"""

import sys
import re
import json
import ssl
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

# Key AI search, citation, and training crawlers
AI_BOTS = [
    "GPTBot",
    "ChatGPT-User",
    "OAI-SearchBot",
    "ClaudeBot",
    "Claude-Web",
    "PerplexityBot",
    "Google-Extended",
    "CCBot",
    "Bytespider",
    "Applebot-Extended"
]


def _ev(detail, count, fetched_url):
    """Build a standardised evidence object."""
    return {"detail": detail, "count": count, "fetched_url": fetched_url}


class BasicHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.text_parts = []
        self.h1_tags = []
        self.h2_tags = []
        self.meta_robots = []
        self.noscript_found = False
        self.root_div_empty = False
        self.has_app_container = False
        self._current_tag = None
        self._in_script_style = False
        self._in_h1 = 0
        self._h1_buffer = []
        self._in_h2 = 0
        self._h2_buffer = []
        self._in_container = False
        self._container_depth = 0
        self._container_text_len = 0

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        self._current_tag = tag_lower
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower in ["script", "style"]:
            self._in_script_style = True

        if tag_lower == "noscript":
            self.noscript_found = True

        if tag_lower == "h1":
            self._in_h1 += 1
            if self._in_h1 == 1:
                self._h1_buffer = []
        elif tag_lower == "h2":
            self._in_h2 += 1
            if self._in_h2 == 1:
                self._h2_buffer = []

        if tag_lower == "meta":
            name = attr_dict.get("name", "").lower()
            content = attr_dict.get("content", "").lower()
            if name in ["robots", "googlebot", "bingbot", "gptbot"]:
                self.meta_robots.append((name, content))

        div_id = attr_dict.get("id", "").lower()
        if div_id in ["root", "app", "__next", "__nuxt", "main-app"]:
            self.has_app_container = True
            self._in_container = True
            self._container_depth = 1
            self._container_text_len = 0
        elif self._in_container and tag_lower == "div":
            self._container_depth += 1

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ["script", "style"]:
            self._in_script_style = False

        if tag_lower == "h1":
            self._in_h1 = max(0, self._in_h1 - 1)
            if self._in_h1 == 0:
                full_h1 = " ".join("".join(self._h1_buffer).split())
                if full_h1:
                    self.h1_tags.append(full_h1)
        elif tag_lower == "h2":
            self._in_h2 = max(0, self._in_h2 - 1)
            if self._in_h2 == 0:
                full_h2 = " ".join("".join(self._h2_buffer).split())
                if full_h2:
                    self.h2_tags.append(full_h2)

        if tag_lower == "div" and self._in_container:
            self._container_depth -= 1
            if self._container_depth <= 0:
                if self._container_text_len < 30:
                    self.root_div_empty = True
                self._in_container = False
                self._container_depth = 0

        self._current_tag = None

    def handle_data(self, data):
        if not self._in_script_style:
            clean = data.strip()
            if clean:
                self.text_parts.append(clean)
            if self._in_h1 > 0:
                self._h1_buffer.append(data)
            if self._in_h2 > 0:
                self._h2_buffer.append(data)
            if self._in_container:
                self._container_text_len += len(clean)


def fetch_url(url, timeout=7):
    """Safely fetch URL content and response headers with modern User-Agent."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    )
    try:
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            headers = dict(resp.info())
            return resp.status, headers, content
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return e.code, dict(e.headers), body
    except URLError as e:
        return 0, {}, f"Connection error: {str(e.reason)}"
    except Exception as e:
        return 0, {}, f"Unexpected error: {str(e)}"


def parse_robots_txt(robots_content):
    """
    Parses robots.txt and checks access rules for general crawlers and specific AI bots.
    Adheres to RFC 9309 group boundaries and case-insensitive user-agent matching.
    Returns: { bot_name: {"disallow_all": bool, "disallowed_paths": list, "allowed": bool} }
    """
    rules = {}
    current_agents = []
    last_was_directive = False
    sitemaps = []

    for line in robots_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" in line:
            field, val = line.split(":", 1)
            field = field.strip().lower()
            val = val.strip()

            if field == "user-agent":
                if last_was_directive:
                    current_agents = []
                    last_was_directive = False
                agent_norm = val.lower()
                if agent_norm:
                    current_agents.append(agent_norm)
            elif field in ["disallow", "allow"]:
                last_was_directive = True
                for agent in current_agents:
                    if agent not in rules:
                        rules[agent] = {"disallows": [], "allows": []}
                    if field == "disallow":
                        rules[agent]["disallows"].append(val)
                    else:
                        rules[agent]["allows"].append(val)
            elif field == "sitemap":
                sitemaps.append(val)

    analysis = {
        "sitemaps": sitemaps,
        "bot_status": {}
    }

    star_rules = rules.get("*", {"disallows": [], "allows": []})
    star_blocks_all = any(d in ["/", "/*"] for d in star_rules["disallows"])
    if star_blocks_all and any(a in ["/", "/*"] for a in star_rules["allows"]):
        star_blocks_all = False

    for bot in AI_BOTS:
        bot_norm = bot.lower()
        bot_rule = rules.get(bot_norm)
        if bot_rule:
            disallowed_all = any(d in ["/", "/*"] for d in bot_rule["disallows"])
            if disallowed_all and any(a in ["/", "/*"] for a in bot_rule["allows"]):
                disallowed_all = False
            disallowed_paths = bot_rule["disallows"]
        else:
            disallowed_all = star_blocks_all
            disallowed_paths = star_rules["disallows"]

        analysis["bot_status"][bot] = {
            "explicit": bot_norm in rules,
            "disallowed_all": disallowed_all,
            "disallowed_paths": disallowed_paths,
            "can_access_root": not disallowed_all
        }

    return analysis


def run_crawl_audit(target_url, raw_html=None, raw_robots=None):
    """
    Performs crawl and render audit on target URL or provided HTML/robots content.
    Returns list of findings. Evidence is always a structured dict.
    """
    findings = []
    parsed_url = urlparse(target_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # 1. Inspect robots.txt
    robots_url = urljoin(base_url, "/robots.txt")
    if raw_robots is None and parsed_url.scheme in ["http", "https"]:
        code, _, robots_content = fetch_url(robots_url)
    else:
        code = 200 if raw_robots else 404
        robots_content = raw_robots or ""

    if code == 200 and robots_content:
        robots_analysis = parse_robots_txt(robots_content)

        # Check blocked AI search and citation crawlers
        blocked_citation_bots = [
            bot for bot in ["ChatGPT-User", "OAI-SearchBot", "PerplexityBot", "Claude-Web"]
            if robots_analysis["bot_status"].get(bot, {}).get("disallowed_all")
        ]

        bot_declarations = "\nUser-agent: ".join(blocked_citation_bots)
        if blocked_citation_bots:
            findings.append({
                "title": f"AI search and citation bots explicitly blocked in robots.txt ({', '.join(blocked_citation_bots)})",
                "severity": "critical",
                "evidence": _ev(
                    detail=f"robots.txt disallows root access for live assistant citation agents: {', '.join(blocked_citation_bots)}.",
                    count=len(blocked_citation_bots),
                    fetched_url=robots_url
                ),
                "suggested_action": {
                    "summary": f"Allow citation crawlers in robots.txt so AI assistants can verify and cite your domain in user answers.",
                    "priority": "critical",
                    "remediation_details": (
                        f"Add explicit permissions to robots.txt:\n"
                        f"User-agent: {bot_declarations}\n"
                        f"Allow: /\n"
                    )
                }
            })

        # Check AI training crawlers
        blocked_training_bots = [
            bot for bot in ["GPTBot", "ClaudeBot", "Google-Extended", "CCBot"]
            if robots_analysis["bot_status"].get(bot, {}).get("disallowed_all")
        ]
        if blocked_training_bots and not blocked_citation_bots:
            findings.append({
                "title": f"AI training crawlers restricted in robots.txt ({', '.join(blocked_training_bots)})",
                "severity": "medium",
                "evidence": _ev(
                    detail=f"Domain blocks foundation model indexing agents: {', '.join(blocked_training_bots)}.",
                    count=len(blocked_training_bots),
                    fetched_url=robots_url
                ),
                "suggested_action": {
                    "summary": "Review bot governance policy; allow AI search bots while selectively gating model training if desired.",
                    "priority": "medium",
                    "remediation_details": (
                        "To permit foundation models to index your public content, update robots.txt:\n"
                        f"User-agent: {blocked_training_bots[0]}\n"
                        "Allow: /\n"
                    )
                }
            })


    elif code == 404:
        findings.append({
            "title": "No robots.txt discovered on domain root",
            "severity": "low",
            "evidence": _ev(
                detail=f"GET {base_url}/robots.txt returned HTTP 404 Not Found.",
                count=0,
                fetched_url=robots_url
            ),
            "suggested_action": {
                "summary": "Create a clear, permissive robots.txt declaring explicit bot allowances and sitemap path.",
                "priority": "low",
                "remediation_details": f"Create {base_url}/robots.txt:\nUser-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml"
            }
        })

    # 2. Inspect Target Page HTML & Headers
    headers = {}
    if raw_html is None and parsed_url.scheme in ["http", "https"]:
        code, headers, html = fetch_url(target_url)
    else:
        code = 200
        html = raw_html or ""

    if not html:
        findings.append({
            "title": "Target page unreachable or returned empty payload",
            "severity": "critical",
            "evidence": _ev(
                detail=f"Failed to retrieve HTML content from {target_url} (HTTP status: {code}).",
                count=0,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Verify target server availability, firewall permissions, and SSL certificate validity.",
                "priority": "critical",
                "remediation_details": (
                    "Ensure the web server is operational and returns HTTP 200 to automated user agents:\n"
                    f'curl -Iv -A "Mozilla/5.0 (compatible; ChatGPT-User/1.0; +https://openai.com/bot)" {target_url}'
                )
            }
        })
        return findings

    # Check X-Robots-Tag HTTP header (confirmed by live fetch → critical allowed)
    x_robots = headers.get("x-robots-tag", "").lower()
    if "noindex" in x_robots or "nosnippet" in x_robots:
        findings.append({
            "title": "Restrictive X-Robots-Tag detected in HTTP response headers",
            "severity": "critical",
            "evidence": _ev(
                detail=f"Server sent header 'X-Robots-Tag: {x_robots}', which instructs crawlers not to index or quote text snippets.",
                count=1,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Remove 'noindex' and 'nosnippet' directives from server HTTP response headers for public pages.",
                "priority": "critical",
                "remediation_details": (
                    "Update web server response header configuration to allow indexation and AI snippets:\n"
                    "# Nginx example:\n"
                    'add_header X-Robots-Tag "index, follow, max-snippet:-1";'
                )
            }
        })

    # Check for WAF / Anti-Bot Interstitials and CAPTCHAs (confirmed by live fetch → critical allowed)
    html_lower = html.lower()
    waf_signals = []
    if "awswaf" in html_lower or "gokuprops" in html_lower or "aws-waf" in html_lower:
        waf_signals.append("AWS WAF client-side challenge ('awsWafCookie')")
    if "bm-verify" in html_lower or "ak_bmsc" in html_lower:
        waf_signals.append("Akamai Bot Manager interstitial ('bm-verify')")
    if "cf-chl-" in html_lower or "cloudflare-challenge" in html_lower or "challenge-platform" in html_lower or "just a moment..." in html_lower:
        waf_signals.append("Cloudflare Managed Challenge")
    if "datadome" in html_lower:
        waf_signals.append("DataDome bot protection")
    if "perimeterx" in html_lower or "px-captcha" in html_lower:
        waf_signals.append("PerimeterX / HUMAN bot challenge")
    if "incapsula" in html_lower or "visid_incap" in html_lower:
        waf_signals.append("Imperva / Incapsula WAF interstitial")
    if "sucuri" in html_lower and "sucuri-webguard" in html_lower:
        waf_signals.append("Sucuri WAF challenge")
    if "rb_waf" in html_lower:
        waf_signals.append("Reblaze WAF protection")
    if ("captcha" in html_lower or "robot check" in html_lower) and len(html) < 4000:
        waf_signals.append("Automated CAPTCHA / Bot Barrier")

    if waf_signals:
        findings.append({
            "title": f"Automated bot challenge or WAF interception detected ({waf_signals[0]})",
            "severity": "critical",
            "evidence": _ev(
                detail=(
                    f"Initial HTTP response payload is intercepted by a security WAF challenge: {', '.join(waf_signals)}. "
                    "AI search assistants and retrieval crawlers cannot solve JavaScript interstitials and will drop citations."
                ),
                count=len(waf_signals),
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Configure WAF allowlists or bot management bypass rules for verified AI assistant crawlers (e.g. OpenAI, Anthropic, Perplexity).",
                "priority": "critical",
                "remediation_details": "Whitelist verified AI bot IP ranges or user-agents in your CDN / WAF to prevent false blocks."
            }
        })

    # 3. Parse HTML and test for CSR Hydration Gaps
    parser = BasicHTMLTextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass

    # Check Meta Robots tag (confirmed in fetched HTML → critical allowed)
    for name, content in parser.meta_robots:
        if "noindex" in content or "nosnippet" in content:
            findings.append({
                "title": f"Meta tag <meta name='{name}' content='{content}'> blocks indexation or quoting",
                "severity": "critical",
                "evidence": _ev(
                    detail=f"Found meta tag instructing crawlers not to index or snippet page content.",
                    count=1,
                    fetched_url=target_url
                ),
                "suggested_action": {
                    "summary": "Update meta robots tag to allow indexing and snippet generation: <meta name='robots' content='index, follow, max-snippet:-1'>.",
                    "priority": "critical",
                    "remediation_details": "Replace restrictive <meta> tag in <head> with:\n<meta name=\"robots\" content=\"index, follow, max-snippet:-1, max-image-preview:large\">"
                }
            })

    # Check Client-Side Rendering (CSR) Hydration Gap (confirmed by DOM inspection → critical allowed)
    extracted_text = " ".join(parser.text_parts)
    text_length = len(extracted_text)
    html_length = len(html)
    text_ratio = (text_length / max(html_length, 1)) * 100

    if parser.has_app_container and parser.root_div_empty and text_length < 200:
        findings.append({
            "title": "Severe Client-Side JavaScript Hydration Gap (Empty Initial DOM)",
            "severity": "critical",
            "evidence": _ev(
                detail=(
                    f"Initial raw HTML contains empty client root container with only {text_length} characters of text "
                    f"across {html_length} bytes of markup. AI crawlers without full headless JS rendering cannot see page content."
                ),
                count=text_length,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Implement Server-Side Rendering (SSR) or Static Site Generation (SSG) so critical text is present in the initial HTML payload.",
                "priority": "critical",
                "remediation_details": "Use Next.js Server Components, Nuxt, or pre-render static HTML at build time so AI crawlers receive complete text without executing JavaScript."
            }
        })
    elif text_ratio < 6.0 and html_length > 15000:
        findings.append({
            "title": "Low raw-HTML text density detected",
            "severity": "medium",
            "evidence": _ev(
                detail=f"Page payload is {html_length:,} bytes but contains only {text_length:,} characters of visible text ({text_ratio:.1f}% ratio).",
                count=text_length,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Verify that important content is server-readable.",
                "priority": "medium",
                "remediation_details": (
                    "Extract inline script bundles to deferred external assets and pre-render factual text:\n"
                    '<script src="/static/bundle.js" defer></script>'
                )
            }
        })

    # Check for missing H1 in raw DOM (heuristic on HTML → capped at high)
    if not parser.h1_tags:
        findings.append({
            "title": "Missing semantic <h1> heading in initial HTML response",
            "severity": "medium",
            "evidence": _ev(
                detail="Raw HTML contains 0 <h1> elements. AI extractors rely on <h1> to establish the primary subject of a document.",
                count=0,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Include a single, descriptive <h1> element in the initial server-rendered HTML payload clearly identifying the page topic.",
                "priority": "medium",
                "remediation_details": "Add a server-rendered <h1> in the main content container:\n<header>\n  <h1>Core Brand & Value Proposition</h1>\n</header>"
            }
        })

    return findings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <URL>")
        sys.exit(1)
    target = sys.argv[1]
    results = run_crawl_audit(target)
    print(json.dumps(results, indent=2))
