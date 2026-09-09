#!/usr/bin/env python3
"""
Structured Data & Entity Authority Inspector
Extracts, parses, and validates JSON-LD schemas and Microdata.
Audits entity disambiguation (sameAs), organization identity, and product schemas.
"""

import sys
import re
import json
import ssl
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser


class JSONLDExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.json_ld_blocks = []
        self.microdata_items = []
        self._in_json_ld = False
        self._current_buffer = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "script":
            script_type = attr_dict.get("type", "").strip().lower()
            if script_type == "application/ld+json":
                self._in_json_ld = True
                self._current_buffer = []

        if "itemtype" in attr_dict:
            self.microdata_items.append(attr_dict.get("itemtype"))

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._in_json_ld:
            content = "".join(self._current_buffer).strip()
            if content:
                self.json_ld_blocks.append(content)
            self._in_json_ld = False
            self._current_buffer = []

    def handle_data(self, data):
        if self._in_json_ld:
            self._current_buffer.append(data)


def fetch_page(url, timeout=7):
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
    except Exception as e:
        return ""


def flatten_json_ld(obj):
    """Recursively yields all schema objects from nested objects or @graph arrays."""
    if isinstance(obj, list):
        for item in obj:
            yield from flatten_json_ld(item)
    elif isinstance(obj, dict):
        yield obj
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                yield from flatten_json_ld(v)


def run_schema_audit(target_url, raw_html=None):
    findings = []
    html = raw_html
    if html is None:
        html = fetch_page(target_url)

    if not html:
        return findings

    extractor = JSONLDExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass

    parsed_schemas = []
    syntax_errors = []

    for idx, block in enumerate(extractor.json_ld_blocks):
        try:
            data = json.loads(block)
            parsed_schemas.extend(list(flatten_json_ld(data)))
        except json.JSONDecodeError as e:
            syntax_errors.append((idx + 1, str(e)))

    # 1. Report JSON-LD Syntax Errors
    if syntax_errors:
        for block_num, err in syntax_errors:
            findings.append({
                "title": f"Malformed JSON-LD syntax in script block #{block_num}",
                "severity": "high",
                "evidence": f"Failed to parse JSON-LD block #{block_num}: {err}.",
                "suggested_action": {
                    "summary": "Fix JSON syntax errors (e.g. unescaped quotes, trailing commas) so AI crawlers can parse schema triples.",
                    "priority": "high",
                    "remediation_details": (
                        "Validate and correct JSON-LD syntax in <head>:\n"
                        '<script type="application/ld+json">\n'
                        '{\n'
                        '  "@context": "https://schema.org",\n'
                        '  "@type": "Organization",\n'
                        '  "name": "Brand Name",\n'
                        '  "url": "https://example.com"\n'
                        '}\n'
                        '</script>'
                    )
                }
            })

    # 2. Complete absence of Structured Data
    if not parsed_schemas and not extractor.microdata_items:
        findings.append({
            "title": "No Schema.org structured data (JSON-LD or Microdata) found",
            "severity": "high",
            "evidence": "Crawled page; found 0 JSON-LD blocks and 0 Microdata itemscope tags. AI assistants cannot extract structured factual triples without inference.",
            "suggested_action": {
                "summary": "Inject Schema.org JSON-LD structured data for Organization, WebSite, and primary offerings.",
                "priority": "high",
                "remediation_details": "Add an <script type='application/ld+json'> block in <head> defining Organization and WebSite schemas."
            }
        })
        return findings

    # Extract schema types
    schema_types = set()
    for s in parsed_schemas:
        stype = s.get("@type")
        if isinstance(stype, list):
            schema_types.update(stype)
        elif isinstance(stype, str):
            schema_types.add(stype)

    # 3. Check Organization / Entity Presence
    org_schemas = [
        s for s in parsed_schemas
        if s.get("@type") in ["Organization", "Corporation", "LocalBusiness", "NGO"]
    ]

    if not org_schemas:
        findings.append({
            "title": "Missing Organization Schema for brand identity and authority",
            "severity": "high",
            "evidence": f"Structured data contains schemas: {list(schema_types)}, but lacks an Organization or Corporation entity definition.",
            "suggested_action": {
                "summary": "Add Schema.org Organization markup with legal name, official logo, founding date, and sameAs links.",
                "priority": "high",
                "remediation_details": 'Add Organization JSON-LD to <head>: <script type="application/ld+json">{"@context": "https://schema.org", "@type": "Organization", "name": "Brand Name", "url": "https://example.com", "logo": "https://example.com/logo.png"}</script>'
            }
        })
    else:
        # Check Entity Disambiguation and sameAs links
        all_same_as = []
        for org in org_schemas:
            same_as = org.get("sameAs", [])
            if isinstance(same_as, str):
                all_same_as.append(same_as)
            elif isinstance(same_as, list):
                all_same_as.extend([s for s in same_as if isinstance(s, str)])

        authoritative_sources = ["wikidata.org", "wikipedia.org", "linkedin.com", "crunchbase.com"]
        matched_auth = [
            source for source in authoritative_sources
            if any(source in link.lower() for link in all_same_as)
        ]

        if not all_same_as:
            findings.append({
                "title": "Missing 'sameAs' entity corroboration links in Organization schema",
                "severity": "medium",
                "evidence": "Organization schema found, but 'sameAs' property is missing or empty. Increases risk of entity ambiguity and hallucination.",
                "suggested_action": {
                    "summary": "Add 'sameAs' array linking to verified external knowledge bases (Wikidata, Wikipedia, LinkedIn, Crunchbase).",
                    "priority": "medium",
                    "remediation_details": 'Include "sameAs": ["https://www.wikidata.org/wiki/...", "https://www.linkedin.com/company/..."] in Organization JSON-LD.'
                }
            })
        elif not matched_auth:
            findings.append({
                "title": "Organization 'sameAs' links lack authoritative knowledge bases (Wikidata/Wikipedia/LinkedIn)",
                "severity": "low",
                "evidence": f"Discovered sameAs links: {all_same_as[:3]}, but none point to Wikidata, Wikipedia, Crunchbase, or LinkedIn.",
                "suggested_action": {
                    "summary": "Corroborate brand identity by linking to your Wikidata QID or Crunchbase profile.",
                    "priority": "low",
                    "remediation_details": 'Ground brand identity in external knowledge graphs: add Wikidata URL (e.g. "https://www.wikidata.org/wiki/Q...") to the "sameAs" array.'
                }
            })

    # 4. Check Product / Offer schema if commercial signals exist
    pricing_pattern = re.compile(r'((\$|€|£|¥|₹|\bUSD\b|\bEUR\b|\bGBP\b|\bINR\b)\s*\d+|\b(pricing|subscription|plans|buy\s+now|billed\s+annually)\b)', re.IGNORECASE)
    has_pricing_signals = bool(pricing_pattern.search(html))
    has_product_schema = any(t in ["Product", "Offer", "SoftwareApplication", "Service"] for t in schema_types)

    if has_pricing_signals and not has_product_schema:
        findings.append({
            "title": "Commercial or pricing content present without Product/Offer JSON-LD",
            "severity": "high",
            "evidence": "Page contains commercial pricing keywords/indicators but lacks Product, SoftwareApplication, or Offer structured data.",
            "suggested_action": {
                "summary": "Add Product/Offer JSON-LD with price, priceCurrency, and description so AI search can directly answer pricing queries.",
                "priority": "high",
                "remediation_details": 'Define @type: "Product" with offers: { @type: "Offer", price: "...", priceCurrency: "USD" }.'
            }
        })

    # 5. Check BreadcrumbList schema
    if "BreadcrumbList" not in schema_types:
        findings.append({
            "title": "Missing BreadcrumbList Schema for topical hierarchy",
            "severity": "low",
            "evidence": "No BreadcrumbList schema found. Limits AI understanding of site hierarchy and parent category relationships.",
            "suggested_action": {
                "summary": "Implement BreadcrumbList JSON-LD to explicitly communicate site navigation taxonomy.",
                "priority": "low",
                "remediation_details": 'Add BreadcrumbList JSON-LD: <script type="application/ld+json">{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com"}]}</script>'
            }
        })

    return findings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schema_inspector.py <URL>")
        sys.exit(1)
    target = sys.argv[1]
    res = run_schema_audit(target)
    print(json.dumps(res, indent=2))
