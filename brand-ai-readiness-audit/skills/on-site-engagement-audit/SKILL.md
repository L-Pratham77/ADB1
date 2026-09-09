---
name: on-site-engagement-audit
description: Audit on-site visitor orientation, 3-second value proposition clarity, heading hierarchy, Call-to-Action (CTA) effectiveness, cognitive load, and navigation aids. Use when diagnosing why visitors arriving from AI search citations bounce or fail to engage.
license: Apache-2.0
allowed-tools: [python, bash]
metadata:
  version: "1.0.0"
  category: "on-site-engagement"
  framework: "agentskills.io"
---

# On-Site Engagement & Visitor Retention Audit

Audits the post-click visitor experience to ensure visitors arriving from AI assistant citations immediately grasp the page topic, experience minimal cognitive friction, and encounter clear conversion paths.

## When to use
- When AI search traffic shows high bounce rates or low dwell time.
- When evaluating landing page clarity, hero headline effectiveness, and CTA hierarchy.
- When checking document scannability, reading patterns, and heading continuity.

## Inputs
- `target_url` (string, required): Target landing page URL.
- `html_content` (string, optional): Raw HTML string for offline evaluation.

## Procedure
1. **Value Proposition & H1 Heading Analysis**:
   - Verify presence and singularity of the primary `<h1>` element.
   - Evaluate whether the headline clearly states the product category, core benefit, and target user within 3–15 words.
2. **Heading Progression & Hierarchy**:
   - Check sequential order of headings (`H1` -> `H2` -> `H3`).
   - Detect skipped heading levels that confuse assistive readers and diminish scannability.
3. **Call-to-Action (CTA) Hierarchy**:
   - Detect primary action buttons (`button`, `a.btn`, `a.cta`).
   - Check for outcome-oriented action verbs vs vague phrases ("Click here", "Learn more").
4. **Scannability & Cognitive Load**:
   - Detect dense paragraphs (> 95 words) that violate scannable reading patterns.
5. **Navigation & Breadcrumb Structure**:
   - Verify presence of semantic `<nav>` elements and breadcrumb structures for cross-page context retention.

## Output
Emits finding dictionaries adhering to the marketplace schema:
```json
[
  {
    "title": "Missing above-the-fold <h1> headline for immediate visitor orientation",
    "severity": "high",
    "evidence": "0 <h1> elements found. AI-referred visitors cannot quickly confirm topic match.",
    "suggested_action": {
      "summary": "Add a prominent <h1> headline clearly stating what the product does and for whom.",
      "priority": "high"
    }
  }
]
```

## References & Scripts
- Engagement Heuristics: [`references/engagement_heuristics.md`](references/engagement_heuristics.md)
- Friction Audit Checklist: [`references/friction_audit_checklist.md`](references/friction_audit_checklist.md)
- Executable Evaluator: [`scripts/engagement_evaluator.py`](scripts/engagement_evaluator.py)
