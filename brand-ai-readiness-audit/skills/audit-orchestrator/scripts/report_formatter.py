#!/usr/bin/env python3
"""
Audit Report Formatter & Schema Validator
Enforces the standardized JSON schema, assigns sequential IDs,
calculates severity counts, and generates markdown summaries.
"""

from datetime import datetime, timezone
import json


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def validate_report_schema(report_dict):
    """
    Validates that report_dict satisfies the minimum required schema:
    - site (str)
    - audited_at (str)
    - summary (dict with total_findings, critical, high, medium)
    - findings (list of dicts with id, title, severity, evidence, suggested_action)
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
            if "suggested_action" in f and isinstance(f["suggested_action"], dict):
                for act_req in ["summary", "priority"]:
                    if act_req not in f["suggested_action"]:
                        errors.append(f"Finding #{idx} suggested_action missing '{act_req}'.")

    return len(errors) == 0, errors


def build_final_report(site, findings, proactive_recommendations=None, audited_at=None):
    """
    Sorts findings by severity, assigns sequential IDs (F-001, F-002, ...),
    counts severities, and attaches proactive recommendations.
    """
    if audited_at is None:
        audited_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Sort findings by severity
    sorted_findings = sorted(
        findings,
        key=lambda x: SEVERITY_ORDER.get(x.get("severity", "low").lower(), 99)
    )

    formatted_findings = []
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for idx, f in enumerate(sorted_findings, 1):
        sev = f.get("severity", "low").lower()
        if sev not in counts:
            sev = "low"
        counts[sev] += 1

        suggested_action = f.get("suggested_action", {})
        if not isinstance(suggested_action, dict):
            suggested_action = {
                "summary": str(suggested_action),
                "priority": sev
            }
        else:
            if "priority" not in suggested_action:
                suggested_action["priority"] = sev

        formatted_findings.append({
            "id": f"F-{idx:03d}",
            "title": f.get("title", "Untitled Finding"),
            "severity": sev,
            "evidence": f.get("evidence", "No evidence recorded."),
            "suggested_action": suggested_action
        })

    report = {
        "site": site,
        "audited_at": audited_at,
        "summary": {
            "total_findings": len(formatted_findings),
            "critical": counts["critical"],
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"]
        },
        "findings": formatted_findings
    }

    if proactive_recommendations:
        report["proactive_recommendations"] = proactive_recommendations

    is_valid, validation_errors = validate_report_schema(report)
    if not is_valid:
        raise ValueError(f"Generated report failed schema validation: {validation_errors}")

    return report


def render_markdown_report(report):
    """Generates an executive-ready Markdown summary of the audit report."""
    summary = report["summary"]
    site = report["site"]
    audited_at = report["audited_at"]

    lines = [
        f"# AI-Readiness & Engagement Audit Report: `{site}`",
        f"*Audited at: {audited_at}*",
        "",
        "## Summary Overview",
        f"- **Total Findings**: {summary['total_findings']}",
        f"- **Critical**: {summary.get('critical', 0)}",
        f"- **High**: {summary.get('high', 0)}",
        f"- **Medium**: {summary.get('medium', 0)}",
        f"- **Low**: {summary.get('low', 0)}",
        "",
        "## Detailed Findings & Suggested Actions",
        ""
    ]

    for f in report["findings"]:
        sev_badge = f"**[{f['severity'].upper()}]**"
        action = f["suggested_action"]
        lines.extend([
            f"### {f['id']}: {f['title']} {sev_badge}",
            f"- **Evidence**: {f['evidence']}",
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

    return "\n".join(lines)
