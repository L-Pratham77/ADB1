# Conversion Friction & Bounce Risk Audit Checklist

This reference outlines high-friction patterns that repel visitors arriving at a website, leading to elevated bounce rates and lost engagement.

---

## 1. High-Friction Anti-Patterns

### 1. The Immediate Modal / Popup Wall
- **The Defect**: Firing newsletter sign-up overlays, full-screen discount popups, or intrusive surveys within 5 seconds of page load.
- **The Impact**: Visitors seeking rapid confirmation of a fact from an AI search result are interrupted; cognitive friction spikes, resulting in immediate page abandonment.
- **Remediation**: Defer non-critical modals to exit-intent triggers or scroll depth >= 60%.

### 2. Ambiguous or Hidden Value Proposition
- **The Defect**: Using clever, poetic, or hyper-abstract slogans in the hero banner (e.g. *"Empowering Tomorrow's Possibilities Today"*).
- **The Impact**: A visitor arriving from an AI query like *"best automated data lineage tool"* cannot tell whether this site solves their problem.
- **Remediation**: Use concrete, outcome-based hero headlines with explicit category names.

### 3. Missing or Vague Primary Action (CTA)
- **The Defect**: No clear button above the fold, or buttons that only say *"Learn More"*.
- **The Impact**: Visitors lack a defined next step in their customer journey.
- **Remediation**: Provide high-contrast primary buttons stating the exact action and cost/commitment (e.g. *"Start Free Trial — No Credit Card Required"*).

### 4. Broken or Skipped Heading Hierarchy
- **The Defect**: Skipping heading levels (e.g. `<h1>` followed directly by `<h3>` or `<h4>`), or using multiple competing `<h1>` tags on a single page.
- **The Impact**: Degrades accessibility screen-reader navigation and confuses crawler document models.
- **Remediation**: Enforce strict sequential heading hierarchy (`H1` -> `H2` -> `H3`).

---

## 2. On-Site Engagement Scoring Matrix

| Signal | Ideal State | Warning Threshold | Critical Failure |
|---|---|---|---|
| **Above-the-fold H1** | 1 descriptive H1 (4–15 words) | Multiple H1s or H1 > 25 words | Missing H1 |
| **Primary CTA** | Explicit, outcome-focused action | Vague ("Click here") | Missing CTA above the fold |
| **Paragraph Length** | 20–60 words per paragraph | 60–90 words | Wall of text (> 100 words) |
| **Navigation Aids** | Breadcrumbs + clear `<nav>` | Missing breadcrumbs on subpages | No navigation container |
