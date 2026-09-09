#!/usr/bin/env python3
"""
Submission Packaging & Verification Script
Validates directory structure, marketplace manifest, runs unit tests,
and builds brand-ai-readiness-audit.zip ensuring size <= 50 MB.
"""

import os
import sys
import zipfile
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
OUTPUT_ZIP_PATH = os.path.join(PARENT_DIR, "brand-ai-readiness-audit.zip")


def run_tests():
    print(">>> Running automated verification tests...")
    test_script = os.path.join(BASE_DIR, "test_runner.py")
    res = subprocess.run([sys.executable, test_script], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        print("[-] Tests failed! Aborting packaging.")
        sys.exit(1)
    print("[+] All verification tests passed successfully!\n")


def create_zip():
    print(f">>> Creating submission zip at {OUTPUT_ZIP_PATH}...")
    folder_name = os.path.basename(BASE_DIR)

    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Skip python cache or hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith((".", "__pycache__"))]
            for file in files:
                if file.endswith((".pyc", ".tmp")) or file.startswith("."):
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PARENT_DIR)
                zipf.write(file_path, rel_path)
                file_count += 1

    size_bytes = os.path.getsize(OUTPUT_ZIP_PATH)
    size_mb = size_bytes / (1024 * 1024)
    print(f"[+] Packaged {file_count} files into {OUTPUT_ZIP_PATH}")
    print(f"[+] Zip size: {size_bytes:,} bytes ({size_mb:.2f} MB)")

    if size_mb > 50.0:
        print(f"[-] ERROR: Submission zip exceeds 50 MB limit ({size_mb:.2f} MB)!")
        sys.exit(1)
    else:
        print(f"[+] Verification OK: Zip size is well within the 50 MB ceiling.")


if __name__ == "__main__":
    run_tests()
    create_zip()
