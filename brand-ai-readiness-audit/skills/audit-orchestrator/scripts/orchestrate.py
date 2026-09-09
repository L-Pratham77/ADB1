#!/usr/bin/env python3
"""
Audit Orchestrator (Entrypoint Skill Execution Engine)
Coordinates domain skills, aggregates findings across Discoverability & Engagement,
generates proactive recommendations, and emits the standardized audit report.
"""

import sys
import os
import re
import json
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

try:
    from crawler import run_crawl_audit, fetch_url
    from schema_inspector import run_schema_audit
    from quotability_analyzer import run_quotability_audit
    from engagement_evaluator import run_engagement_audit
    from report_formatter import build_final_report, render_markdown_report
except ImportError as e:
    # Graceful fallback if invoked in different paths
    pass


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


def run_full_audit(target_input, raw_html=None, raw_robots=None):
    """
    Executes the multi-skill audit across all 4 domain skills,
    aggregates results, and builds the finalized compliant report.
    """
    target_url, site_name = normalize_target_url(target_input)

    # 1. Fetch live page once if offline content not provided
    cached_html = raw_html
    cached_robots = raw_robots

    if cached_html is None:
        try:
            _, _, cached_html = fetch_url(target_url, timeout=7)
        except Exception:
            cached_html = ""

    all_findings = []

    # 2. Execute Skill 1: Crawl & Render Audit
    try:
        from crawler import run_crawl_audit
        crawl_findings = run_crawl_audit(target_url, raw_html=cached_html, raw_robots=cached_robots)
        all_findings.extend(crawl_findings)
    except Exception as e:
        all_findings.append({
            "title": "Crawl & Render audit encountered execution exception",
            "severity": "low",
            "evidence": str(e),
            "suggested_action": {"summary": "Verify network connectivity and retry.", "priority": "low"}
        })

    # 3. Execute Skill 2: Structured Data & Entity Authority Audit
    try:
        from schema_inspector import run_schema_audit
        schema_findings = run_schema_audit(target_url, raw_html=cached_html)
        all_findings.extend(schema_findings)
    except Exception as e:
        all_findings.append({
            "title": "Structured Data audit encountered execution exception",
            "severity": "low",
            "evidence": str(e),
            "suggested_action": {"summary": "Verify JSON-LD parser and retry.", "priority": "low"}
        })

    # 4. Execute Skill 3: Content Quotability & RAG Retrieval Audit
    try:
        from quotability_analyzer import run_quotability_audit
        quotability_findings = run_quotability_audit(target_url, raw_html=cached_html)
        all_findings.extend(quotability_findings)
    except Exception as e:
        all_findings.append({
            "title": "Content Quotability audit encountered execution exception",
            "severity": "low",
            "evidence": str(e),
            "suggested_action": {"summary": "Verify content tokenizer and retry.", "priority": "low"}
        })

    # 5. Execute Skill 4: On-Site Engagement & Orientation Audit
    try:
        from engagement_evaluator import run_engagement_audit
        engagement_findings = run_engagement_audit(target_url, raw_html=cached_html)
        all_findings.extend(engagement_findings)
    except Exception as e:
        all_findings.append({
            "title": "On-Site Engagement audit encountered execution exception",
            "severity": "low",
            "evidence": str(e),
            "suggested_action": {"summary": "Verify engagement extractor and retry.", "priority": "low"}
        })

    # 6. Deduplicate and harmonize findings
    seen_titles = set()
    deduped_findings = []
    for f in all_findings:
        title_key = f.get("title", "").strip().lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            deduped_findings.append(f)

    # 7. Synthesize proactive recommendations
    proactive = generate_proactive_recommendations(site_name, deduped_findings)

    # 8. Build final schema-conforming report
    from report_formatter import build_final_report
    report = build_final_report(
        site=site_name,
        findings=deduped_findings,
        proactive_recommendations=proactive
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

    report = run_full_audit(args.target, raw_html=raw_html, raw_robots=raw_robots)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report successfully saved to {args.output}")

    if args.format in ["json", "both"]:
        print(json.dumps(report, indent=2))

    if args.format in ["markdown", "both"]:
        from report_formatter import render_markdown_report
        print("\n" + render_markdown_report(report))


if __name__ == "__main__":
    main()
