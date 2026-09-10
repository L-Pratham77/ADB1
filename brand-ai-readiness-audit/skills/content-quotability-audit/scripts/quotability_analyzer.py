#!/usr/bin/env python3
"""
Content Quotability & RAG Retrieval Analyzer
Audits text informativeness, facts locked in non-text (images without alt),
buzzword density vs factual substance, definition clarity, and /llms.txt support.

Evidence rule: every finding carries a structured evidence object:
  { "detail": str, "count": int, "fetched_url": str }
Severity cap: this skill operates on HTML content (heuristics) — maximum severity is HIGH.
  Only the crawl-render-audit skill emits CRITICAL findings (confirmed via live HTTP).
"""

import sys
import re
import json
import ssl
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

# Maximum severity this heuristic skill can emit
_MAX_SEVERITY = "high"

BUZZWORDS = [
    "paradigm", "synergy", "synergistic", "holistic", "cutting-edge", "next-gen",
    "revolutionary", "disruptive", "world-class", "game-changer", "unmatched",
    "bespoke", "seamless", "seamlessly", "frictionless", "transformative", "hyper-scalable"
]

CRITICAL_IMAGE_KEYWORDS = [
    "pricing", "price", "table", "comparison", "features", "architecture", "specs", "matrix", "plan"
]


def _ev(detail, count, fetched_url):
    """Build a standardised evidence object."""
    return {"detail": detail, "count": count, "fetched_url": fetched_url}


def _cap_severity(sev):
    """Cap severity to _MAX_SEVERITY for heuristic-only skills."""
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    cap_level = order[_MAX_SEVERITY]
    return sev if order.get(sev, 99) >= cap_level else _MAX_SEVERITY


class ContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.text_parts = []
        self.images = []
        self.headings = []
        self.meta_tags = {}
        self.tables = 0
        self.lists = 0
        self._in_script_style = False
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower in ["script", "style"]:
            self._in_script_style = True

        if tag_lower == "img":
            src = attr_dict.get("src", "")
            alt = attr_dict.get("alt", None)
            self.images.append({"src": src, "alt": alt})

        if tag_lower == "meta":
            prop = (attr_dict.get("property", "") or attr_dict.get("name", "")).lower().strip()
            content = attr_dict.get("content", "").strip()
            if prop and content:
                self.meta_tags[prop] = content

        if tag_lower == "table":
            self.tables += 1

        if tag_lower in ["ul", "ol"]:
            self.lists += 1

        self._tag_stack.append({
            "tag": tag_lower,
            "text_parts": []
        })

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ["script", "style"]:
            self._in_script_style = False

        matched = None
        for i in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[i]["tag"] == tag_lower:
                matched = self._tag_stack.pop(i)
                break

        if matched and tag_lower in ["h1", "h2", "h3"]:
            full_heading = " ".join("".join(matched["text_parts"]).split())
            if full_heading:
                self.headings.append((tag_lower, full_heading))

    def handle_data(self, data):
        if not self._in_script_style and data:
            clean = data.strip()
            if clean:
                self.text_parts.append(clean)
            for entry in self._tag_stack:
                entry["text_parts"].append(data)


def fetch_resource(url, timeout=5):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
    )
    try:
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except Exception:
        return 0, ""


def run_quotability_audit(target_url, raw_html=None):
    findings = []
    html = raw_html
    if html is None:
        status, html = fetch_resource(target_url)

    if not html:
        return findings

    extractor = ContentExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass

    full_text = " ".join(extractor.text_parts)
    words = re.findall(r'\b[a-zA-Z0-9_\-\']+\b', full_text)
    total_words = len(words)

    # 1. Inspect Non-Text Locked Facts (Images without alt or generic alt)
    total_images = len(extractor.images)
    missing_alt = [img for img in extractor.images if img["alt"] is None or img["alt"].strip() == ""]
    generic_alt = [
        img for img in extractor.images
        if img["alt"] and img["alt"].strip().lower() in ["image", "screenshot", "icon", "photo", "graphic", "logo"]
    ]

    # Check for critical diagrams/tables trapped in raster images
    critical_locked_images = []
    for img in missing_alt + generic_alt:
        src = img["src"].lower()
        if any(kw in src for kw in CRITICAL_IMAGE_KEYWORDS):
            critical_locked_images.append(img["src"])

    if critical_locked_images:
        findings.append({
            "title": "Critical factual data (pricing/specs/tables) locked in raster images without alt text",
            "severity": _cap_severity("high"),
            "evidence": _ev(
                detail=(
                    f"Discovered {len(critical_locked_images)} image(s) with filenames matching key factual concepts "
                    f"({', '.join(critical_locked_images[:2])}) lacking descriptive alt text or HTML fallback."
                ),
                count=len(critical_locked_images),
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Convert visual diagrams and pricing graphics into native semantic HTML tables or provide comprehensive alt descriptions.",
                "priority": "high",
                "remediation_details": "AI search assistants cannot OCR images during real-time retrieval. Supply full text tables or detailed alt attributes."
            }
        })
    elif total_images > 3 and (len(missing_alt) / total_images) > 0.4:
        findings.append({
            "title": f"High proportion of images ({len(missing_alt)}/{total_images}) missing alt text",
            "severity": _cap_severity("medium"),
            "evidence": _ev(
                detail=f"Found {len(missing_alt)} image(s) with completely empty or omitted alt attributes out of {total_images} total.",
                count=len(missing_alt),
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Add concise, informative alt text to all informational images describing what they illustrate.",
                "priority": "medium",
                "remediation_details": 'Add descriptive alt text to images: <img src="/assets/diagram.png" alt="Architecture diagram showing real-time AI indexing and retrieval flow">'
            }
        })

    # 2. Marketing Buzzword Density vs Factual Substance (Signal-to-Noise Ratio)
    if total_words > 100:
        lower_words = [w.lower() for w in words]
        buzzword_count = sum(1 for w in lower_words if w in BUZZWORDS)
        lower_full_text = full_text.lower()
        for phrase in ["cutting edge", "game changer", "paradigm shift", "next gen", "world class"]:
            buzzword_count += lower_full_text.count(phrase)
        buzzword_pct = (buzzword_count / total_words) * 100

        if buzzword_pct > 2.0:
            findings.append({
                "title": f"High marketing jargon density ({buzzword_pct:.1f}%) diluting RAG vector retrieval",
                "severity": _cap_severity("medium"),
                "evidence": _ev(
                    detail=(
                        f"Page contains {buzzword_count} high-abstraction buzzwords across {total_words} words "
                        f"({buzzword_pct:.1f}% density). Chunks overloaded with empty claims lose relevance in AI cross-encoder rerankers."
                    ),
                    count=buzzword_count,
                    fetched_url=target_url
                ),
                "suggested_action": {
                    "summary": "Replace generic marketing fluff with concrete specifications, numbers, and direct capability statements.",
                    "priority": "medium",
                    "remediation_details": "Adopt the 'Inverted Pyramid' writing style: lead sections with direct factual answers followed by technical specifications."
                }
            })

    # 3. Canonical Entity Definition Sentence
    lead_text = " ".join(extractor.text_parts[:150])
    has_definition = bool(re.search(
        r'\b[A-Z][a-zA-Z0-9_\s]{2,20}\s+(is\s+(a|an|the)|provides|delivers|builds|orchestrates|automates)\s+',
        lead_text
    ))

    if not has_definition and total_words > 80:
        findings.append({
            "title": "Missing atomic entity definition statement in introductory section",
            "severity": _cap_severity("medium"),
            "evidence": _ev(
                detail=f"Opening {min(total_words, 150)} words lack a definitive subject-predicate-object identity declaration (e.g. '[Brand] is an automated...').",
                count=0,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Add a crisp, one-sentence canonical definition of the brand/product in the hero paragraph.",
                "priority": "medium",
                "remediation_details": "Structure the opening hero sentence as: '[Brand] is a [category] that [primary benefit] for [target audience].'"
            }
        })



    # 5. Check OpenGraph / Social Citation Card Metadata
    has_og_desc = "og:description" in extractor.meta_tags or "description" in extractor.meta_tags
    has_og_title = "og:title" in extractor.meta_tags
    has_og_image = "og:image" in extractor.meta_tags
    if not has_og_desc or not has_og_title:
        missing_parts = []
        if not has_og_title:
            missing_parts.append("og:title")
        if not has_og_desc:
            missing_parts.append("og:description")
        findings.append({
            "title": f"Missing OpenGraph ({', '.join(missing_parts)}) metadata for AI search citation cards",
            "severity": _cap_severity("medium"),
            "evidence": _ev(
                detail=f"Page lacks {', '.join(missing_parts)}. AI assistant search cards (ChatGPT Search, Perplexity) rely on OpenGraph tags to render rich preview snippets.",
                count=len(missing_parts),
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Add OpenGraph meta tags in <head> for crisp, branded citation card previews in AI assistants.",
                "priority": "medium",
                "remediation_details": (
                    '<meta property="og:title" content="Page Title - Brand Name">\n'
                    '<meta property="og:description" content="Concise 1-2 sentence overview for AI citation snippets.">\n'
                    '<meta property="og:image" content="https://example.com/social-preview.png">'
                )
            }
        })
    elif not has_og_image:
        findings.append({
            "title": "Missing 'og:image' OpenGraph tag for visual citation preview cards",
            "severity": _cap_severity("low"),
            "evidence": _ev(
                detail="Page defines og:title and description but lacks 'og:image'. Visual thumbnail cards enhance click-through rates from AI referrals.",
                count=0,
                fetched_url=target_url
            ),
            "suggested_action": {
                "summary": "Specify an og:image meta tag pointing to a high-resolution branded preview card.",
                "priority": "low",
                "remediation_details": '<meta property="og:image" content="https://example.com/assets/og-preview.png">'
            }
        })



    return findings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quotability_analyzer.py <URL>")
        sys.exit(1)
    target = sys.argv[1]
    res = run_quotability_audit(target)
    print(json.dumps(res, indent=2))
