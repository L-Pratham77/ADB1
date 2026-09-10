#!/usr/bin/env python3
"""
Audit Report Formatter & Schema Validator
Enforces the standardized JSON schema, assigns sequential IDs,
calculates severity counts, and generates markdown summaries.

Phase 1 additions:
  - Accepts structured evidence objects { "detail", "count", "fetched_url" }.
  - Includes checks_skipped, degraded, pages_by_type in the summary block.
  - Includes audit_metadata (version, skills_run, mode) at the top level.
  - Renders a prominent score banner in the markdown output.
"""

from datetime import datetime, timezone
import json

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

_VERSION = "2.1.0"


def _evidence_detail(evidence):
    """
    Normalise evidence to a display string regardless of whether it is
    a plain string (legacy) or a structured dict.
    """
    if isinstance(evidence, dict):
        return evidence.get("detail", "")
    return str(evidence)


def validate_report_schema(report_dict):
    """
    Validates that report_dict satisfies the minimum required schema:
    - site (str)
    - audited_at (str)
    - summary (dict with total_findings, critical, high, medium)
    - findings (list of dicts with id, title, severity, evidence, suggested_action)
    Evidence may be a string OR a structured dict { detail, count, fetched_url }.
    """
    errors = []
    if "site" not in report_dict or not isinstance(report_dict["site"], str):
        errors.append("Missing or invalid 'site' field.")
    if "audited_at" not in report_dict or not isinstance(report_dict["audited_at"], str):
        errors.append("Missing or invalid 'audited_at' field.")
    if "summary" not in report_dict or not isinstance(report_dict["summary"], dict):
        errors.append("Missing or invalid 'summary' object.")
    else:
        for k in ["total_findings", "critical", "high", "medium"]:
            if k not in report_dict["summary"]:
                errors.append(f"Missing '{k}' in summary.")

    if "findings" not in report_dict or not isinstance(report_dict["findings"], list):
        errors.append("Missing or invalid 'findings' list.")
    else:
        for idx, f in enumerate(report_dict["findings"]):
            for req in ["id", "title", "severity", "evidence", "suggested_action"]:
                if req not in f:
                    errors.append(f"Finding #{idx} missing required field '{req}'.")
            # Evidence must be a non-empty string OR a dict with a 'detail' key
            if "evidence" in f:
                ev = f["evidence"]
                if isinstance(ev, dict):
                    if "detail" not in ev:
                        errors.append(f"Finding #{idx} structured evidence missing 'detail' key.")
                    if "count" not in ev:
                        errors.append(f"Finding #{idx} structured evidence missing 'count' key.")
                    if "fetched_url" not in ev:
                        errors.append(f"Finding #{idx} structured evidence missing 'fetched_url' key.")
                elif not isinstance(ev, str) or not ev.strip():
                    errors.append(f"Finding #{idx} evidence must be a non-empty string or structured dict.")
            if "suggested_action" in f and isinstance(f["suggested_action"], dict):
                for act_req in ["summary", "priority"]:
                    if act_req not in f["suggested_action"]:
                        errors.append(f"Finding #{idx} suggested_action missing '{act_req}'.")

    return len(errors) == 0, errors


def build_final_report(
    site,
    findings,
    proactive_recommendations=None,
    audited_at=None,
    checks_skipped=None,
    degraded=False,
    skills_run=None,
    mode="live",
    previous_score=None,
    pages_audited=1
):
    """
    Sorts findings by severity, assigns sequential IDs (F-001, F-002, ...),
    counts severities, and attaches proactive recommendations.
    Adds checks_skipped, degraded, pages_by_type to summary.
    Adds audit_metadata block.
    """
    if audited_at is None:
        audited_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    checks_skipped = checks_skipped or []
    skills_run = skills_run or []

    # Sort findings by severity
    sorted_findings = sorted(
        findings,
        key=lambda x: SEVERITY_ORDER.get(x.get("severity", "low").lower(), 99)
    )

    formatted_findings = []
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    
    page_ded = {}
    page_disc = {}
    page_eng = {}

    for idx, f in enumerate(sorted_findings, 1):
        sev = f.get("severity", "low").lower()
        if sev not in counts:
            sev = "low"
        counts[sev] += 1

        val = 0
        if sev == "critical": val = 25
        elif sev == "high": val = 15
        elif sev == "medium": val = 6
        elif sev == "low": val = 2

        area = f.get("area", "")
        is_eng = "engagement" in area.lower() or any(k in f.get("title", "").lower() for k in ["cta", "heading", "navigation", "paragraph", "headline"])
        is_disc = not is_eng or "cross" in area.lower() or "both" in f.get("title", "").lower()

        ev = f.get("evidence", {})
        url = ev.get("fetched_url", "global") if isinstance(ev, dict) else "global"
        # If it's robots.txt, treat as global
        if url.endswith("robots.txt"):
            url = "global"

        if url not in page_ded:
            page_ded[url] = 0
            page_disc[url] = 0
            page_eng[url] = 0
            
        page_ded[url] += val
        if is_eng: page_eng[url] += val
        if is_disc: page_disc[url] += val

        suggested_action = f.get("suggested_action", {})
        if not isinstance(suggested_action, dict):
            suggested_action = {"summary": str(suggested_action), "priority": sev}
        elif "priority" not in suggested_action:
            suggested_action["priority"] = sev

        formatted_findings.append({
            "id": f"F-{idx:03d}",
            "title": f.get("title", "Untitled Finding"),
            "severity": sev,
            "evidence": ev if isinstance(ev, dict) else {"detail": str(ev), "count": 0, "fetched_url": ""},
            "suggested_action": suggested_action
        })

    # Calculate average of per-page scores
    total_pages = max(1, pages_audited)
    all_scores, all_disc, all_eng = [], [], []
    
    global_ded = page_ded.get("global", 0)
    global_disc = page_disc.get("global", 0)
    global_eng = page_eng.get("global", 0)
    
    distinct_urls = [u for u in page_ded.keys() if u != "global"]
    
    for u in distinct_urls:
        all_scores.append(max(0, 100 - global_ded - page_ded[u]))
        all_disc.append(max(0, 100 - global_disc - page_disc[u]))
        all_eng.append(max(0, 100 - global_eng - page_eng[u]))
        
    perfect_pages = max(0, total_pages - len(distinct_urls))
    for _ in range(perfect_pages):
        all_scores.append(max(0, 100 - global_ded))
        all_disc.append(max(0, 100 - global_disc))
        all_eng.append(max(0, 100 - global_eng))
        
    ai_readiness_score = int(sum(all_scores) / len(all_scores)) if all_scores else 100
    discoverability_score = int(sum(all_disc) / len(all_disc)) if all_disc else 100
    engagement_score = int(sum(all_eng) / len(all_eng)) if all_eng else 100

    score_basis = (
        f"Averaged across {total_pages} page(s). Total findings: "
        f"critical={counts['critical']}, high={counts['high']}, "
        f"medium={counts['medium']}, low={counts['low']}"
    )

    report = {
        "site": site,
        "audited_at": audited_at,
        "audit_metadata": {
            "version": _VERSION,
            "skills_run": skills_run,
            "checks_skipped": checks_skipped,
            "mode": mode
        },
        "summary": {
            "total_findings": len(formatted_findings),
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
            "info": counts["info"],
            "checks_skipped": len(checks_skipped),
            "degraded": degraded,
            "pages_by_type": {
                "home": 1,
                "subpages": pages_audited - 1,
                "checked_live": pages_audited if mode == "live" else 0
            },
            "ai_readiness_score": ai_readiness_score,
            "previous_score": previous_score,
            "score_trend": (ai_readiness_score - previous_score) if previous_score is not None else None,
            "score_basis": score_basis,
            "scores": {
                "discoverability": discoverability_score,
                "engagement": engagement_score
            }
        },
        "findings": formatted_findings
    }

    if proactive_recommendations:
        report["proactive_recommendations"] = proactive_recommendations

    is_valid, validation_errors = validate_report_schema(report)
    if not is_valid:
        raise ValueError(f"Generated report failed schema validation: {validation_errors}")

    return report


def _score_emoji(score):
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    return "🔴"


def render_markdown_report(report):
    """Generates an executive-ready Markdown summary of the audit report."""
    summary = report["summary"]
    site = report["site"]
    audited_at = report["audited_at"]
    score = summary.get("ai_readiness_score", 0)
    scores = summary.get("scores", {})
    disc_score = scores.get("discoverability", "N/A")
    eng_score = scores.get("engagement", "N/A")
    emoji = _score_emoji(score)
    degraded = summary.get("degraded", False)
    skipped = summary.get("checks_skipped", 0)
    metadata = report.get("audit_metadata", {})

    trend_str = ""
    trend_val = summary.get("score_trend")
    if trend_val is not None:
        if trend_val > 0:
            trend_str = f" (↑ +{trend_val} since last run)"
        elif trend_val < 0:
            trend_str = f" (↓ {trend_val} since last run)"
        else:
            trend_str = " (= No change since last run)"

    lines = [
        f"# AI-Readiness & Engagement Audit Report: `{site}`",
        f"*Audited at: {audited_at}*",
        "",
        "```",
        f"╔══════════════════════════════════════════════════════════════════╗",
        f"║   AI READINESS SCORE:  {score:>3} / 100   {emoji} {trend_str:<30} ║",
        f"║   Discoverability: {disc_score:<3}   Engagement: {eng_score:<3}                              ║",
        f"╚══════════════════════════════════════════════════════════════════╝",
        "```",
        "",
    ]

    if degraded:
        lines += [
            f"> ⚠️ **Degraded run** — {skipped} skill(s) skipped: `{', '.join(metadata.get('checks_skipped', []))}`. Results may be incomplete.",
            ""
        ]

    lines += [
        "## Executive AI-Readiness Score",
        f"> **Overall Score: `{score}/100`** *(Critical: {summary.get('critical', 0)}, High: {summary.get('high', 0)}, Medium: {summary.get('medium', 0)}, Low: {summary.get('low', 0)})*",
        f"> - **AI Discoverability Score**: `{disc_score}/100` (Crawlability, Entity Knowledge Graph, Quotability & OpenGraph)",
        f"> - **On-Site Engagement Score**: `{eng_score}/100` (Headline Clarity, CTA Conversion Triggers, Scannability)",
        f"> - **Score Basis**: {summary.get('score_basis', '')}",
        "",
        "## Summary Overview",
        f"- **Total Findings**: {summary['total_findings']}",
        f"- **Critical**: {summary.get('critical', 0)}",
        f"- **High**: {summary.get('high', 0)}",
        f"- **Medium**: {summary.get('medium', 0)}",
        f"- **Low**: {summary.get('low', 0)}",
        f"- **Checks Skipped**: {skipped}",
        f"- **Degraded Run**: {'Yes' if degraded else 'No'}",
        "",
        "## Detailed Findings & Suggested Actions",
        ""
    ]

    for f in report["findings"]:
        sev_badge = f"**[{f['severity'].upper()}]**"
        action = f["suggested_action"]
        ev = f["evidence"]
        # Handle both string evidence (legacy) and structured evidence
        if isinstance(ev, dict):
            ev_display = ev.get("detail", "")
            ev_meta = f" *(count: {ev.get('count', '?')}, source: `{ev.get('fetched_url', '')}`)* " if ev.get("fetched_url") else ""
        else:
            ev_display = str(ev)
            ev_meta = ""

        lines.extend([
            f"### {f['id']}: {f['title']} {sev_badge}",
            f"- **Evidence**: {ev_display}{ev_meta}",
            f"- **Suggested Action**: {action.get('summary')}",
            f"- **Priority**: `{action.get('priority')}`",
            ""
        ])
        if "remediation_details" in action:
            lines.extend([
                "**Remediation Steps**:",
                f"```\n{action['remediation_details']}\n```",
                ""
            ])

    if "proactive_recommendations" in report and report["proactive_recommendations"]:
        lines.extend([
            "## Proactive Beyond-Defect Recommendations",
            ""
        ])
        for p in report["proactive_recommendations"]:
            lines.extend([
                f"### {p.get('title')} ({p.get('area')})",
                f"- **Impact**: {p.get('impact')}",
                f"- **Recommended Action**: {p.get('action')}",
                ""
            ])

    if metadata:
        lines.extend([
            "---",
            f"*Audit engine v{metadata.get('version', '?')} · Skills run: {', '.join(metadata.get('skills_run', []))} · Mode: {metadata.get('mode', '?')}*",
            ""
        ])

    return "\n".join(lines)
