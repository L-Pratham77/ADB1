#!/usr/bin/env python3
"""
On-Site Engagement & Visitor Retention Evaluator
Audits above-the-fold value proposition, heading hierarchy,
Call-to-Action (CTA) hierarchy, readability/walls-of-text, and navigation cues.
"""

import sys
import re
import json
import ssl
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from html.parser import HTMLParser

ACTION_VERBS = [
    "start", "get started", "free trial", "try", "sign up", "demo", "book a demo",
    "schedule", "request", "buy", "purchase", "download", "join", "contact sales"
]

VAGUE_CTAS = ["click here", "learn more", "read more", "continue", "submit"]


class EngagementExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.headings = []
        self.paragraphs = []
        self.buttons = []
        self.links = []
        self.has_nav = False
        self.has_breadcrumbs = False
        self.has_modal_markup = False
        self._in_script_style = False
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower in ["script", "style"]:
            self._in_script_style = True

        if tag_lower == "nav":
            self.has_nav = True

        classes_and_ids = f"{attr_dict.get('class', '')} {attr_dict.get('id', '')}".lower()
        if "breadcrumb" in classes_and_ids or attr_dict.get("aria-label", "").lower() in ["breadcrumb", "breadcrumbs"]:
            self.has_breadcrumbs = True

        if any(term in classes_and_ids for term in ["modal-popup", "newsletter-overlay", "popup-wrapper", "exit-intent"]):
            self.has_modal_markup = True

        self._tag_stack.append({
            "tag": tag_lower,
            "attrs": attr_dict,
            "text_parts": []
        })

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ["script", "style"]:
            self._in_script_style = False

        matched_entry = None
        for i in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[i]["tag"] == tag_lower:
                matched_entry = self._tag_stack.pop(i)
                break

        if matched_entry:
            text_content = " ".join("".join(matched_entry["text_parts"]).split())
            attr_dict = matched_entry["attrs"]

            if tag_lower in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if text_content:
                    self.headings.append((tag_lower, text_content))
            elif tag_lower == "p":
                if text_content:
                    self.paragraphs.append(text_content)
            elif tag_lower == "button":
                if text_content:
                    self.buttons.append(text_content)
            elif tag_lower == "a":
                classes = attr_dict.get("class", "").lower()
                role = attr_dict.get("role", "").lower()
                is_button_styled = role == "button" or any(btn_cls in classes for btn_cls in ["btn", "button", "cta"])
                if text_content:
                    if is_button_styled:
                        self.buttons.append(text_content)
                    else:
                        self.links.append(text_content)

    def handle_data(self, data):
        if not self._in_script_style and data:
            for entry in self._tag_stack:
                entry["text_parts"].append(data)


def fetch_page(url, timeout=5):
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
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def run_engagement_audit(target_url, raw_html=None):
    findings = []
    html = raw_html
    if html is None:
        html = fetch_page(target_url)

    if not html:
        return findings

    extractor = EngagementExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass

    # 1. Evaluate Value Proposition & <h1> Heading
    h1_list = [text for tag, text in extractor.headings if tag == "h1"]

    if not h1_list:
        findings.append({
            "title": "Missing above-the-fold <h1> headline for immediate visitor orientation",
            "severity": "high",
            "evidence": "0 <h1> elements found. AI-referred visitors cannot quickly confirm whether the landing page matches the answer summary they just read.",
            "suggested_action": {
                "summary": "Add a prominent <h1> headline clearly stating what the product does and for whom.",
                "priority": "high",
                "remediation_details": "Ensure the <h1> appears above the fold and directly answers the visitor's core question."
            }
        })
    elif len(h1_list) > 2:
        findings.append({
            "title": f"Multiple ({len(h1_list)}) <h1> headings create cognitive confusion",
            "severity": "medium",
            "evidence": f"Found {len(h1_list)} separate <h1> tags: {h1_list[:2]}... Competing primary headlines dilute topical focus.",
            "suggested_action": {
                "summary": "Consolidate into a single canonical <h1> and demote secondary headlines to <h2>.",
                "priority": "medium",
                "remediation_details": "Retain exactly one canonical <h1> in the hero section and demote all other section headlines to <h2>."
            }
        })
    else:
        # Check H1 length and clarity
        h1_text = h1_list[0]
        words = h1_text.split()
        if len(words) < 3:
            findings.append({
                "title": f"Overly brief or vague <h1> headline ('{h1_text}')",
                "severity": "medium",
                "evidence": f"Primary heading has only {len(words)} word(s). Fails to convey a complete value proposition.",
                "suggested_action": {
                    "summary": "Expand the <h1> to explicitly state the category, core benefit, and target user.",
                    "priority": "medium",
                    "remediation_details": "Update <h1> to include a clear benefit and category statement (e.g., 'Automated Cloud Telemetry & AI Readiness Auditing for Enterprise Engineering Teams')."
                }
            })
        elif len(words) > 25:
            findings.append({
                "title": "Excessively verbose <h1> headline exceeding 25 words",
                "severity": "low",
                "evidence": f"Primary heading contains {len(words)} words, increasing cognitive load and reading friction.",
                "suggested_action": {
                    "summary": "Shorten the <h1> to 6–12 impactful words and move explanatory details into a subheadline.",
                    "priority": "low",
                    "remediation_details": "Place the core value proposition in <h1> (6–12 words) and move secondary qualifications into a companion <p class='hero-subtext'>."
                }
            })

    # 2. Heading Hierarchy Skip Detection
    heading_levels = [int(tag[1]) for tag, _ in extractor.headings]
    skipped_levels = []
    for i in range(len(heading_levels) - 1):
        curr, nxt = heading_levels[i], heading_levels[i + 1]
        if nxt > curr + 1:
            skipped_levels.append((curr, nxt))

    if skipped_levels:
        findings.append({
            "title": "Disordered heading hierarchy (skipped heading levels)",
            "severity": "low",
            "evidence": f"Detected jumps in heading hierarchy: {skipped_levels[:2]} (e.g. H{skipped_levels[0][0]} directly to H{skipped_levels[0][1]}).",
            "suggested_action": {
                "summary": "Maintain sequential heading progression (H1 -> H2 -> H3) for accessibility and document scannability.",
                "priority": "low",
                "remediation_details": "Re-level heading tags sequentially so an <h2> is followed by an <h3> rather than jumping directly to an <h4> or <h5>."
            }
        })

    # 3. Call to Action (CTA) Clarity & Presence
    all_ctas = extractor.buttons
    actionable_ctas = []
    vague_ctas_found = []

    for cta in all_ctas:
        cta_lower = cta.lower().strip()
        if any(verb in cta_lower for verb in ACTION_VERBS):
            actionable_ctas.append(cta)
        elif any(cta_lower == vague for vague in VAGUE_CTAS):
            vague_ctas_found.append(cta)

    if not actionable_ctas and not all_ctas:
        findings.append({
            "title": "No primary Call-to-Action (CTA) buttons detected on page",
            "severity": "high",
            "evidence": "Audited interactive elements; found 0 prominent action buttons or CTA links. Arriving visitors have no clear next step.",
            "suggested_action": {
                "summary": "Place a prominent, high-contrast Call-to-Action button above the fold (e.g. 'Start Free Trial' or 'Book a Demo').",
                "priority": "high",
                "remediation_details": "Add an above-the-fold conversion element: <a href='/signup' class='btn btn-primary'>Start Free 14-Day Trial</a>."
            }
        })
    elif vague_ctas_found and not actionable_ctas:
        findings.append({
            "title": f"Generic, low-intent Call to Action ({vague_ctas_found[0]})",
            "severity": "medium",
            "evidence": f"Buttons rely on low-information phrases like '{vague_ctas_found[0]}' instead of specifying the tangible outcome or offer.",
            "suggested_action": {
                "summary": "Replace generic labels with outcome-oriented copy (e.g., change 'Learn More' to 'Explore Interactive Demo').",
                "priority": "medium",
                "remediation_details": "Replace generic copy like 'Click Here' or 'Learn More' with tangible value triggers like 'Start Free Tier' or 'Request 15-Minute Architecture Review'."
            }
        })

    # 4. Content Chunking & Walls of Text
    long_paragraphs = [p for p in extractor.paragraphs if len(p.split()) > 95]
    if long_paragraphs:
        findings.append({
            "title": f"Dense 'walls of text' ({len(long_paragraphs)} paragraphs > 95 words) impeding scannability",
            "severity": "medium",
            "evidence": f"Discovered {len(long_paragraphs)} paragraph(s) exceeding 95 words without structural breaks. Increases reader drop-off.",
            "suggested_action": {
                "summary": "Break long text blocks into 2–3 sentence paragraphs supplemented by bulleted lists or callout cards.",
                "priority": "medium",
                "remediation_details": "Split paragraphs exceeding 90 words into 2-3 sentence blocks, utilizing <ul> bullet points and bold leading terms to support F-pattern reading."
            }
        })

    # 5. Navigation & Context Orientation
    if not extractor.has_nav:
        findings.append({
            "title": "Missing semantic <nav> navigation container",
            "severity": "medium",
            "evidence": "Page lacks an explicit <nav> element. Makes secondary exploration difficult for visitors seeking additional context.",
            "suggested_action": {
                "summary": "Wrap header navigation in a semantic <nav> element with links to Home, Products, Docs, and Pricing.",
                "priority": "medium",
                "remediation_details": "Enclose header menu links in a semantic <nav aria-label='Main Navigation'> element: <nav><ul><li><a href='/'>Home</a></li><li><a href='/products'>Products</a></li><li><a href='/pricing'>Pricing</a></li></ul></nav>."
            }
        })

    return findings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engagement_evaluator.py <URL>")
        sys.exit(1)
    target = sys.argv[1]
    res = run_engagement_audit(target)
    print(json.dumps(res, indent=2))
