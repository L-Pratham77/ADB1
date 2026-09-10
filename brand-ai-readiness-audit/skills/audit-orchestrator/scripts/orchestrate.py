#!/usr/bin/env python3
"""
Audit Orchestrator (Entrypoint Skill Execution Engine)
Coordinates domain skills, aggregates findings across Discoverability & Engagement,
generates proactive recommendations, and emits the standardized audit report.

Gap fixes (Phase 1):
  - Import errors are now logged explicitly instead of silently swallowed.
  - Skills that throw exceptions are tracked and surfaced in checks_skipped.
  - checks_skipped and degraded are propagated to the final report summary.
"""

import sys
import os
import re
import json
import logging
import argparse
from urllib.parse import urlparse
from datetime import datetime, timezone

# Ensure sibling skill script directories are importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

sys.path.insert(0, os.path.join(SKILLS_DIR, "crawl-render-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "structured-data-entity-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "content-quotability-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "on-site-engagement-audit", "scripts"))
sys.path.insert(0, CURRENT_DIR)

# --- Import skills with explicit error reporting (no bare except: pass) ---
_import_errors = []

try:
    from crawler import run_crawl_audit, fetch_url
except ImportError as e:
    _import_errors.append(f"crawl-render-audit: {e}")
    run_crawl_audit = None
    fetch_url = None

try:
    from schema_inspector import run_schema_audit
except ImportError as e:
    _import_errors.append(f"structured-data-entity-audit: {e}")
    run_schema_audit = None

try:
    from quotability_analyzer import run_quotability_audit
except ImportError as e:
    _import_errors.append(f"content-quotability-audit: {e}")
    run_quotability_audit = None

try:
    from engagement_evaluator import run_engagement_audit
except ImportError as e:
    _import_errors.append(f"on-site-engagement-audit: {e}")
    run_engagement_audit = None

try:
    from report_formatter import build_final_report, render_markdown_report
except ImportError as e:
    _import_errors.append(f"report_formatter: {e}")
    build_final_report = None
    render_markdown_report = None

if _import_errors:
    logging.warning("Skill import failures detected: %s", "; ".join(_import_errors))


def normalize_target_url(raw_target):
    """Ensures target has standard scheme and extracts clean host."""
    target = raw_target.strip()
    if not re.match(r'^https?://', target, re.IGNORECASE):
        target = f"https://{target}"
    parsed = urlparse(target)
    host = parsed.netloc or parsed.path
    # Strip any port or trailing slashes for site name
    site_name = host.split(":")[0].strip("/")
    return target, site_name


def generate_proactive_recommendations(site_name, findings):
    """
    Synthesizes forward-looking proactive improvements that strengthen
    AI discoverability and on-site engagement even where no defect was found.
    """
    recommendations = [
        {
            "area": "AI Discoverability",
            "title": "Publish Curated /llms.txt Machine Index",
            "impact": "Enables emerging AI agents (ChatGPT Search, Perplexity, Claude) to ingest documentation and product specs without parsing complex HTML/CSS layouts.",
            "action": f"Create https://{site_name}/llms.txt containing structured markdown summaries of products, pricing, and API endpoints."
        },
        {
            "area": "AI Discoverability",
            "title": "Canonical Wikidata & Knowledge Graph Grounding",
            "impact": "Eliminates entity ambiguity across foundation models and establishes permanent corporate entity authority in Google Knowledge Graph and Microsoft Satori.",
            "action": f"Link your organization's official Wikidata item (QID) and Wikipedia entry in the 'sameAs' array of Schema.org Organization JSON-LD."
        },
        {
            "area": "On-Site Engagement",
            "title": "Context-Preserving Landing Experience for AI Referrals",
            "impact": "Prevents immediate bounce for users arriving from AI assistant search citations by greeting them with modular, scannable proof points.",
            "action": "Ensure key feature and pricing pages display clear breadcrumbs and a 3-second value proposition directly confirming the topic highlighted in AI citations."
        },
        {
            "area": "AI Discoverability",
            "title": "Proactive FAQ Schema for High-Intent Conversational Queries",
            "impact": "Directly feeds question-and-answer pairs into AI search engines, securing featured snippets and conversational citation cards.",
            "action": "Deploy Schema.org FAQPage structured data on key product pages answering top customer queries (pricing, integrations, enterprise security)."
        }
    ]
    return recommendations


def run_full_audit(target_input, raw_html=None, raw_robots=None, previous_score=None):
    """
    Executes the multi-skill audit across all 4 domain skills,
    aggregates results, and builds the finalized compliant report.
    """
    from urllib.parse import urljoin
    target_url, site_name = normalize_target_url(target_input)

    # 1. Fetch live page once if offline content not provided
    cached_html = raw_html
    cached_robots = raw_robots
    live_fetch = raw_html is None  # True when we go to the network

    urls_to_audit = [(target_url, cached_html, cached_robots)]

    if cached_html is None and fetch_url is not None:
        try:
            _, _, cached_html = fetch_url(target_url, timeout=7)
            # Fetch robots.txt once globally to prevent redundant requests
            if cached_robots is None:
                robots_url = urljoin(target_url, "/robots.txt")
                try:
                    _, _, cached_robots = fetch_url(robots_url, timeout=5)
                except Exception:
                    cached_robots = ""
                    
            urls_to_audit[0] = (target_url, cached_html, cached_robots)
            
            # Find subpages for a true Multi-Page Audit
            if cached_html:
                sub_links = []
                for match in re.finditer(r'href=["\'](/[^"\']+)["\']', cached_html):
                    path = match.group(1)
                    if any(kw in path.lower() for kw in ["/pricing", "/about", "/product", "/features", "/docs"]):
                        sub_url = urljoin(target_url, path)
                        if sub_url not in sub_links and sub_url != target_url:
                            sub_links.append(sub_url)
                            if len(sub_links) >= 2:
                                break
                                
                if sub_links:
                    import concurrent.futures
                    def fetch_subpage(s_url):
                        try:
                            _, _, s_html = fetch_url(s_url, timeout=5)
                            return (s_url, s_html, cached_robots)
                        except Exception:
                            return (s_url, "", cached_robots)
                            
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        results = list(executor.map(fetch_subpage, sub_links))
                        urls_to_audit.extend(results)
                        
        except Exception:
            urls_to_audit[0] = (target_url, "", cached_robots)

    all_findings = []
    skills_run = set()
    checks_skipped = set()

    # Run skills across all discovered URLs
    for url, html, robots in urls_to_audit:

        if run_crawl_audit is not None:
            try:
                crawl_findings = run_crawl_audit(url, raw_html=html, raw_robots=robots)
                for f in crawl_findings:
                    f["area"] = "AI Discoverability"
                all_findings.extend(crawl_findings)
                skills_run.add("crawl-render-audit")
            except Exception as e:
                checks_skipped.add("crawl-render-audit")
                all_findings.append({
                    "title": "Crawl & Render audit encountered execution exception",
                    "severity": "low",
                    "area": "AI Discoverability",
                    "evidence": {"detail": str(e), "count": 0, "fetched_url": url},
                    "suggested_action": {"summary": "Verify network connectivity and retry.", "priority": "low", "remediation_details": "Ensure target URL is reachable via HTTPS."}
                })
        else:
            checks_skipped.add("crawl-render-audit")

        # 3. Execute Skill 2: Structured Data & Entity Authority Audit
        if run_schema_audit is not None:
            try:
                schema_findings = run_schema_audit(url, raw_html=html)
                for f in schema_findings:
                    f["area"] = "AI Discoverability"
                all_findings.extend(schema_findings)
                skills_run.add("structured-data-entity-audit")
            except Exception as e:
                checks_skipped.add("structured-data-entity-audit")
                all_findings.append({
                    "title": "Structured Data audit encountered execution exception",
                    "severity": "low",
                    "area": "AI Discoverability",
                    "evidence": {"detail": str(e), "count": 0, "fetched_url": url},
                    "suggested_action": {"summary": "Verify JSON-LD parser and retry.", "priority": "low", "remediation_details": "Ensure structured data is valid JSON."}
                })
        else:
            checks_skipped.add("structured-data-entity-audit")

        # 4. Execute Skill 3: Content Quotability & RAG Retrieval Audit
        if run_quotability_audit is not None:
            try:
                quotability_findings = run_quotability_audit(url, raw_html=html)
                for f in quotability_findings:
                    f["area"] = "AI Discoverability"
                all_findings.extend(quotability_findings)
                skills_run.add("content-quotability-audit")
            except Exception as e:
                checks_skipped.add("content-quotability-audit")
                all_findings.append({
                    "title": "Content Quotability audit encountered execution exception",
                    "severity": "low",
                    "area": "AI Discoverability",
                    "evidence": {"detail": str(e), "count": 0, "fetched_url": url},
                    "suggested_action": {"summary": "Verify content tokenizer and retry.", "priority": "low", "remediation_details": "Check HTML content encoding."}
                })
        else:
            checks_skipped.add("content-quotability-audit")

        # 5. Execute Skill 4: On-Site Engagement & Orientation Audit
        if run_engagement_audit is not None:
            try:
                engagement_findings = run_engagement_audit(url, raw_html=html)
                for f in engagement_findings:
                    f["area"] = "On-Site Engagement"
                all_findings.extend(engagement_findings)
                skills_run.add("on-site-engagement-audit")
            except Exception as e:
                checks_skipped.add("on-site-engagement-audit")
                all_findings.append({
                    "title": "On-Site Engagement audit encountered execution exception",
                    "severity": "low",
                    "area": "On-Site Engagement",
                    "evidence": {"detail": str(e), "count": 0, "fetched_url": url},
                    "suggested_action": {"summary": "Verify engagement extractor and retry.", "priority": "low", "remediation_details": "Ensure DOM contains valid HTML elements."}
                })
        else:
            checks_skipped.add("on-site-engagement-audit")

    # 6. Harmonize cross-cutting findings and deduplicate
    has_crawl_h1 = any("Missing semantic <h1> heading in initial HTML response" in f.get("title", "") for f in all_findings)
    has_engagement_h1 = any("Missing above-the-fold <h1> headline for immediate visitor orientation" in f.get("title", "") for f in all_findings)

    harmonized_list = []
    if has_crawl_h1 and has_engagement_h1:
        harmonized_list.append({
            "title": "Missing primary <h1> headline",
            "severity": "medium",
            "area": "Cross-Cutting",
            "evidence": {
                "detail": "Initial HTML response contains 0 <h1> elements. Both AI citation bots and arriving visitors lack a primary subject anchor to confirm topic match.",
                "count": 0,
                "fetched_url": target_url
            },
            "suggested_action": {
                "summary": "Add a prominent, server-rendered <h1> headline above the fold clearly defining the product and topic.",
                "priority": "high",
                "remediation_details": "Include a single descriptive <h1> (6–12 words) in the initial server HTML payload."
            }
        })
        for f in all_findings:
            if "Missing semantic <h1> heading in initial HTML response" not in f.get("title", "") and \
               "Missing above-the-fold <h1> headline for immediate visitor orientation" not in f.get("title", ""):
                harmonized_list.append(f)
    else:
        harmonized_list = all_findings

    seen_titles = set()
    deduped_findings = []
    for f in harmonized_list:
        title_key = f.get("title", "").strip().lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped_findings.append(f)

    # 7. Synthesize proactive recommendations
    proactive = generate_proactive_recommendations(site_name, deduped_findings)

    # 8. Build final schema-conforming report
    degraded = len(checks_skipped) > 0
    report = build_final_report(
        site=site_name,
        findings=deduped_findings,
        proactive_recommendations=proactive,
        checks_skipped=list(checks_skipped),
        degraded=degraded,
        skills_run=list(skills_run),
        mode="offline" if not live_fetch else "live",
        previous_score=previous_score,
        pages_audited=len(urls_to_audit)
    )

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Brand AI-Readiness Audit Orchestrator (Adobe University Hackathon 2026 Round 3)"
    )
    parser.add_argument("target", help="Website URL or domain to audit (e.g. example.com or https://example.com)")
    parser.add_argument("--offline-html", help="Path to local HTML file for offline testing", default=None)
    parser.add_argument("--offline-robots", help="Path to local robots.txt file for offline testing", default=None)
    parser.add_argument("--output", "-o", help="Path to save JSON audit report", default=None)
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="json", help="Output format")

    args = parser.parse_args()

    raw_html = None
    if args.offline_html and os.path.exists(args.offline_html):
        with open(args.offline_html, "r", encoding="utf-8", errors="replace") as f:
            raw_html = f.read()

    raw_robots = None
    if args.offline_robots and os.path.exists(args.offline_robots):
        with open(args.offline_robots, "r", encoding="utf-8", errors="replace") as f:
            raw_robots = f.read()
            
    previous_score = None
    if args.output and os.path.exists(args.output):
        try:
            with open(args.output, "r", encoding="utf-8") as f:
                old_report = json.load(f)
                previous_score = old_report.get("summary", {}).get("ai_readiness_score")
        except Exception:
            pass

    report = run_full_audit(args.target, raw_html=raw_html, raw_robots=raw_robots, previous_score=previous_score)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report successfully saved to {args.output}")

    if args.format in ["json", "both"]:
        print(json.dumps(report, indent=2))

    if args.format in ["markdown", "both"]:
        md_text = "\n" + render_markdown_report(report)
        try:
            print(md_text)
        except UnicodeEncodeError:
            print(md_text.encode("utf-8", errors="replace").decode("cp1252", errors="replace"))


if __name__ == "__main__":
    main()
