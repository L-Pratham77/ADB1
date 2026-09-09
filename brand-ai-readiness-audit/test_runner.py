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

    def test_robots_txt_group_isolation_and_case_insensitivity(self):
        """Verifies RFC 9309 group boundaries and case-insensitive user-agent matching."""
        mock_robots = """
User-agent: *
Disallow: /admin/

User-agent: chatgpt-user
Disallow: /

User-agent: PerplexityBot
Disallow: /
"""
        findings = run_crawl_audit("https://testbrand.com", raw_html="<html><body><h1>Test</h1></body></html>", raw_robots=mock_robots)
        blocked_findings = [f for f in findings if "AI search and citation bots explicitly blocked" in f["title"]]
        self.assertEqual(len(blocked_findings), 1)
        # Verify that only the explicitly blocked bots are listed, and other bots (like Claude-Web) are NOT blocked
        evidence = blocked_findings[0]["evidence"]
        self.assertIn("ChatGPT-User", evidence)
        self.assertIn("PerplexityBot", evidence)
        self.assertNotIn("Claude-Web", evidence)

    def test_nested_tags_in_headings_and_buttons(self):
        """Verifies that nested tags (span, b, i) inside h1 and buttons preserve complete text and classes."""
        mock_html = """
<!DOCTYPE html>
<html>
<head><title>Modern Styled App</title></head>
<body>
  <nav><a href="/">Home</a></nav>
  <h1 class="hero">Transform Your <span>Intelligent Enterprise</span></h1>
  <a class="btn btn-primary" href="/signup"><span>Get Started Free</span></a>
</body>
</html>
"""
        engagement_findings = run_engagement_audit("https://testbrand.com", raw_html=mock_html)
        # Should NOT flag missing H1 or missing CTA
        missing_h1 = [f for f in engagement_findings if "<h1>" in f["title"]]
        missing_cta = [f for f in engagement_findings if "Call-to-Action" in f["title"]]
        self.assertEqual(len(missing_h1), 0, f"Unexpected H1 finding: {missing_h1}")
        self.assertEqual(len(missing_cta), 0, f"Unexpected CTA finding: {missing_cta}")

        # Crawl audit should also capture H1 with child span
        crawl_findings = run_crawl_audit("https://testbrand.com", raw_html=mock_html, raw_robots="User-agent: *\nAllow: /")
        missing_crawl_h1 = [f for f in crawl_findings if "Missing semantic <h1>" in f["title"]]
        self.assertEqual(len(missing_crawl_h1), 0)

    def test_international_currency_pricing_detection(self):
        """Verifies detection of commercial pricing signals using international currency symbols (€, £, ¥, ₹)."""
        mock_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Global SaaS</title>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "Organization", "name": "Global SaaS", "sameAs": ["https://www.wikidata.org/wiki/Q1"]}
  </script>
</head>
<body>
  <h1>Global Solutions</h1>
  <p>Our European tier is €49/mo and UK tier is £39/mo.</p>
</body>
</html>
"""
        findings = run_schema_audit("https://testbrand.com", raw_html=mock_html)
        pricing_findings = [f for f in findings if "Commercial or pricing content present" in f["title"]]
        self.assertEqual(len(pricing_findings), 1)

    def test_cross_skill_h1_harmonization(self):
        """Verifies entrypoint harmonizes overlapping missing-H1 findings from crawl and engagement skills."""
        mock_html = """
<!DOCTYPE html>
<html>
<head><title>No H1 Site</title></head>
<body>
  <nav><a href="/">Home</a></nav>
  <p>Welcome to our page without any headline.</p>
  <button class="btn">Click to Explore</button>
</body>
</html>
"""
        report = run_full_audit("https://testbrand.com", raw_html=mock_html, raw_robots="User-agent: *\nAllow: /")
        h1_findings = [f for f in report["findings"] if "Missing <h1> headline" in f["title"]]
        self.assertEqual(len(h1_findings), 1, "Expected exactly 1 harmonized H1 finding")
        self.assertIn("critical for both AI topic extraction and visitor orientation", h1_findings[0]["title"])


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

        # Check AI readiness score and sub-scores
        summary = report["summary"]
        self.assertIn("ai_readiness_score", summary)
        self.assertTrue(0 <= summary["ai_readiness_score"] <= 100)
        self.assertIn("scores", summary)
        self.assertIn("discoverability", summary["scores"])
        self.assertIn("engagement", summary["scores"])
        self.assertTrue(0 <= summary["scores"]["discoverability"] <= 100)
        self.assertTrue(0 <= summary["scores"]["engagement"] <= 100)

        # Check that all findings have copy-pasteable remediation_details
        for f in report["findings"]:
            action = f["suggested_action"]
            self.assertIn("remediation_details", action, f"Finding {f['id']} lacks remediation_details")
            self.assertTrue(len(action["remediation_details"].strip()) > 0)

    def test_opengraph_citation_card_audit(self):
        """Verifies detection of missing OpenGraph tags needed for AI search citation cards."""
        html_without_og = """
<!DOCTYPE html>
<html>
<head><title>No OG Tags</title></head>
<body><h1>Hello World</h1></body>
</html>
"""
        findings = run_quotability_audit("https://example.com", raw_html=html_without_og)
        og_findings = [f for f in findings if "OpenGraph" in f["title"]]
        self.assertEqual(len(og_findings), 1)
        self.assertIn("remediation_details", og_findings[0]["suggested_action"])
        self.assertIn("og:title", og_findings[0]["suggested_action"]["remediation_details"])
        self.assertIn("og:description", og_findings[0]["suggested_action"]["remediation_details"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
