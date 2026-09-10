# Brand AI-Readiness Audit Marketplace
> **Adobe University Hackathon 2026 — Round 3**  
> An automated, multi-skill evaluation engine for assessing and remediating website **AI Discoverability** and **On-Site Engagement**.

[![Tests](https://img.shields.io/badge/tests-17%20passed-brightgreen)](#automated-test-suite)
[![Platform](https://img.shields.io/badge/agentskills.io-compliant-blue)](#marketplace-architecture)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](#prerequisites)
[![Dependencies](https://img.shields.io/badge/dependencies-zero%20(stdlib)-brightgreen)](#prerequisites)
[![Archive Size](https://img.shields.io/badge/submission%20zip-60%20KB%20(%3C%2050%20MB)-success)](#submission-packaging)

---

## Quick Start (1-Command Run)

Run an end-to-end audit on any website with a single command:

```bash
# Basic audit (emits compliant JSON report)
python run_audit.py https://example.com

# Save report to a file
python run_audit.py https://example.com --output audit_report.json

# Display executive Markdown summary
python run_audit.py https://example.com --format markdown
```

---

## Running Automated Tests

Run the full 17-test regression and compliance suite:

```bash
python brand-ai-readiness-audit/test_runner.py
```

---

## Submission Package

The complete `agentskills.io` marketplace is located in [`brand-ai-readiness-audit/`](brand-ai-readiness-audit/):
* Manifest: [`marketplace.json`](brand-ai-readiness-audit/marketplace.json) (designates `audit-orchestrator` as entrypoint)
* Full Documentation: [`brand-ai-readiness-audit/README.md`](brand-ai-readiness-audit/README.md)
* Step-by-Step Running Guide: [`HOW_TO_RUN.txt`](HOW_TO_RUN.txt)
* Submission Zip: [`brand-ai-readiness-audit.zip`](brand-ai-readiness-audit.zip) (ready for upload to the hackathon portal)

---

## Architecture Overview

```
brand-ai-readiness-audit/
├── marketplace.json                         # Marketplace registry manifest (entrypoint designated)
├── README.md                                # Root documentation & composition guide
├── HOW_TO_RUN.txt                           # Running instructions & quick-start guide
├── run_audit.py                             # Single 1-command execution launcher
├── _runner.py                           # Automated  suite (13 unit & integration s)
├── package_submission.py                    # Submission packaging and verification utility
└── skills/
    ├── audit-orchestrator/                  # [ENTRYPOINT] Coordinates all skills & emits final report
    │   ├── SKILL.md                         # agentskills.io declaration & execution workflow
    │   ├── scripts/orchestrate.py           # Main CLI executor & sub-skill orchestrator
    │   ├── scripts/report_formatter.py      # Schema validator & Markdown formatter
    │   └── references/                      # Schema and scoring references
    │
    ├── crawl-render-audit/                  # [SKILL 1] Technical Crawlability & JS-Render Gaps
    │   ├── SKILL.md                         # robots.txt, WAFs, CSR hydration checks
    │   └── scripts/crawler.py
    │
    ├── structured-data-entity-audit/        # [SKILL 2] Schema.org, Knowledge Graphs & Entity Authority
    │   ├── SKILL.md                         # JSON-LD, entity disambiguation, multi-currency
    │   └── scripts/schema_inspector.py
    │
    ├── content-quotability-audit/           # [SKILL 3] AI RAG Retrieval, Quotability & OpenGraph Cards
    │   ├── SKILL.md                         # Fact density, OpenGraph, /llms.txt
    │   └── scripts/quotability_analyzer.py
    │
    └── on-site-engagement-audit/            # [SKILL 4] User Orientation, Information Architecture & CTAs
        ├── SKILL.md                         # 3-second value prop, CTA clarity, heading hierarchy
        └── scripts/engagement_evaluator.py
```

See [`brand-ai-readiness-audit/README.md`](brand-ai-readiness-audit/README.md) for the complete architecture and skill breakdown.
