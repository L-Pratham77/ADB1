#!/usr/bin/env python3
"""
Single One-Run Launcher for Brand AI-Readiness Audit
Delegates directly to the designated entrypoint skill (audit-orchestrator).
"""
import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRYPOINT = os.path.join(BASE_DIR, "skills", "audit-orchestrator", "scripts", "orchestrate.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_audit.py <URL> [options]")
        print("Example: python run_audit.py https://example.com")
        sys.exit(1)

    cmd = [sys.executable, ENTRYPOINT] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
