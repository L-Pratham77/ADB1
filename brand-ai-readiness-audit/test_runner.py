#!/usr/bin/env python3
"""
Automated Test Suite for Brand AI-Readiness Audit Marketplace
Validates agentskills.io compliance, marketplace manifest, individual skill logic,
and full end-to-end orchestration against mock web fixtures.
"""

import os
import sys
import json
import re
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

# Add script paths
sys.path.insert(0, os.path.join(SKILLS_DIR, "audit-orchestrator", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "crawl-render-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "structured-data-entity-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "content-quotability-audit", "scripts"))
sys.path.insert(0, os.path.join(SKILLS_DIR, "on-site-engagement-audit", "scripts"))

from orchestrate import run_full_audit
from report_formatter import validate_report_schema
from crawler import run_crawl_audit
from schema_inspector import run_schema_audit
from quotability_analyzer import run_quotability_audit
from engagement_evaluator import run_engagement_audit


class TestMarketplaceCompliance(unittest.TestCase):
    """Verifies that the marketplace manifest and skill folders strictly conform to the spec."""

    def test_marketplace_manifest_validity(self):
        manifest_path = os.path.join(BASE_DIR, "marketplace.json")
        self.assertTrue(os.path.exists(manifest_path), "marketplace.json does not exist at root.")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertIn("name", manifest)
        self.assertIn("version", manifest)
        self.assertIn("skills", manifest)
        self.assertIsInstance(manifest["skills"], list)
        self.assertGreater(len(manifest["skills"]), 1, "Marketplace must contain multiple skills.")

        # Exactly one entrypoint skill
        entrypoints = [s for s in manifest["skills"] if s.get("entrypoint") is True]
        self.assertEqual(len(entrypoints), 1, f"Expected exactly 1 entrypoint, found {len(entrypoints)}.")
        self.assertEqual(entrypoints[0]["id"], "audit-orchestrator")

        # Every declared skill path exists and has SKILL.md
        for skill_entry in manifest["skills"]:
            skill_path = os.path.join(BASE_DIR, skill_entry["path"])
            self.assertTrue(os.path.isdir(skill_path), f"Skill folder '{skill_path}' does not exist.")
            skill_md = os.path.join(skill_path, "SKILL.md")
            self.assertTrue(os.path.exists(skill_md), f"SKILL.md missing in '{skill_path}'.")

    def test_agentskills_io_format(self):
        """Validates that each skill's SKILL.md satisfies agentskills.io frontmatter & sections."""
        manifest_path = os.path.join(BASE_DIR, "marketplace.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for skill_entry in manifest["skills"]:
            skill_path = os.path.join(BASE_DIR, skill_entry["path"])
            skill_md_path = os.path.join(skill_path, "SKILL.md")
            with open(skill_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify YAML frontmatter exists
            self.assertTrue(content.startswith("---"), f"{skill_entry['id']} SKILL.md missing frontmatter.")
            parts = content.split("---", 2)
            self.assertGreaterEqual(len(parts), 3, f"{skill_entry['id']} SKILL.md frontmatter unclosed.")
            frontmatter = parts[1]

            # Verify required metadata fields in frontmatter
            self.assertIn("name:", frontmatter, f"{skill_entry['id']} missing 'name:' in frontmatter.")
            self.assertIn("description:", frontmatter, f"{skill_entry['id']} missing 'description:' in frontmatter.")

            # Verify required markdown sections in body
            body = parts[2]
            self.assertIn("## When to use", body, f"{skill_entry['id']} missing '## When to use'.")
            self.assertIn("## Inputs", body, f"{skill_entry['id']} missing '## Inputs'.")
            self.assertIn("## Procedure", body, f"{skill_entry['id']} missing '## Procedure'.")
            self.assertIn("## Output", body, f"{skill_entry['id']} missing '## Output'.")


class TestDomainSkillDetectionAccuracy(unittest.TestCase):
    """Tests each skill's detection logic against synthetic fixtures representing Round 2 failure modes."""

    def test_blocked_ai_bots_in_robots(self):
        mock_robots = """
User-agent: *
Disallow: /admin/

User-agent: ChatGPT-User
Disallow: /

User-agent: PerplexityBot
Disallow: /
"""
        findings = run_crawl_audit("https://testbrand.com", raw_html="<html><body><h1>Test</h1></body></html>", raw_robots=mock_robots)
        blocked_findings = [f for f in findings if "AI search and citation bots explicitly blocked" in f["title"]]
        self.assertEqual(len(blocked_findings), 1)
        self.assertEqual(blocked_findings[0]["severity"], "critical")
        self.assertIn("ChatGPT-User", blocked_findings[0]["evidence"])

    def test_client_side_rendering_hydration_gap(self):
        mock_csr_html = """
<!DOCTYPE html>
<html>
<head><title>SPA App</title></head>
<body>
  <div id="root"></div>
  <noscript>You need JavaScript to view this application.</noscript>
</body>
</html>
"""
        findings = run_crawl_audit("https://testbrand.com", raw_html=mock_csr_html, raw_robots="")
        csr_findings = [f for f in findings if "Client-Side JavaScript Hydration Gap" in f["title"]]
        self.assertEqual(len(csr_findings), 1)
        self.assertEqual(csr_findings[0]["severity"], "critical")

    def test_missing_structured_data_and_sameas(self):
        mock_html_no_schema = """
<!DOCTYPE html>
<html>
<head><title>No Schema Brand</title></head>
<body>
  <h1>Welcome to Brand</h1>
  <p>Our monthly subscription is $49/mo.</p>
</body>
</html>
"""
        findings = run_schema_audit("https://testbrand.com", raw_html=mock_html_no_schema)
        schema_findings = [f for f in findings if "No Schema.org structured data" in f["title"]]
        self.assertEqual(len(schema_findings), 1)
        self.assertEqual(schema_findings[0]["severity"], "high")

    def test_locked_facts_in_images_and_jargon(self):
        mock_html = """
<!DOCTYPE html>
<html>
<head><title>Product</title></head>
<body>
  <h1>Revolutionary Platform</h1>
  <p>We deliver next-gen disruptive paradigm shifting synergy for cutting-edge holistic enterprises.</p>
  <img src="/images/pricing_matrix_table.png" />
</body>
</html>
"""
        findings = run_quotability_audit("https://testbrand.com", raw_html=mock_html)
        locked_findings = [f for f in findings if "locked in raster images" in f["title"]]
        self.assertEqual(len(locked_findings), 1)
        self.assertEqual(locked_findings[0]["severity"], "high")

    def test_engagement_friction(self):
        mock_html = """
<!DOCTYPE html>
<html>
<head><title>Friction Brand</title></head>
<body>
  <h3>Skipped Heading</h3>
  <p>Wall of text paragraph that continues without pause for a very long stretch of text containing more than one hundred words to deliberately trigger the dense reading friction detection heuristic designed to prevent cognitive fatigue for visitors arriving from fast-paced AI assistant search summaries. It goes on and on without any bullet lists, bold spans, or section breaks until the reader loses interest completely and hits back to return to ChatGPT.</p>
</body>
</html>
"""
        findings = run_engagement_audit("https://testbrand.com", raw_html=mock_html)
        h1_missing = [f for f in findings if "Missing above-the-fold <h1> headline" in f["title"]]
        cta_missing = [f for f in findings if "No primary Call-to-Action" in f["title"]]
        self.assertEqual(len(h1_missing), 1)
        self.assertEqual(len(cta_missing), 1)


class TestEndToEndOrchestrationAndReportSchema(unittest.TestCase):
    """Tests the full orchestration pipeline and validates the generated report against the required schema."""

    def test_end_to_end_audit_and_schema_validation(self):
        mock_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Acme Cloud Services</title>
</head>
<body>
  <nav><a href="/">Home</a> | <a href="/pricing">Pricing</a></nav>
  <h1>Acme Cloud AI Data Pipelines</h1>
  <p>Acme is a cloud data platform that provides real-time telemetry and automated dbt orchestration.</p>
  <p>Plans start at $49/mo.</p>
  <button class="btn">Start Free 14-Day Trial</button>
</body>
</html>
"""
        mock_robots = """
User-agent: *
Allow: /
Sitemap: https://acme.com/sitemap.xml
"""
        report = run_full_audit("https://acme.com", raw_html=mock_html, raw_robots=mock_robots)

        # Validate against schema
        is_valid, errors = validate_report_schema(report)
        self.assertTrue(is_valid, f"Report failed schema validation: {errors}")

        # Check required fields
        self.assertEqual(report["site"], "acme.com")
        self.assertIn("audited_at", report)
        self.assertIn("summary", report)
        self.assertIn("findings", report)
        self.assertIn("total_findings", report["summary"])
        self.assertIn("critical", report["summary"])
        self.assertIn("high", report["summary"])
        self.assertIn("medium", report["summary"])

        # Check finding structure
        for f in report["findings"]:
            self.assertTrue(f["id"].startswith("F-"))
            self.assertIn("title", f)
            self.assertIn("severity", f)
            self.assertIn("evidence", f)
            self.assertIn("suggested_action", f)
            self.assertIn("summary", f["suggested_action"])
            self.assertIn("priority", f["suggested_action"])

        # Check proactive recommendations exist
        self.assertIn("proactive_recommendations", report)
        self.assertGreater(len(report["proactive_recommendations"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
