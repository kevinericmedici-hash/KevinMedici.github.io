#!/usr/bin/env python3
"""Check local asset links (src/href) in HTML files for missing files or
case mismatches. GitHub Pages serves from a case-sensitive filesystem, so a
reference that only works on case-insensitive Windows/macOS will 404 live.

Usage: python scripts/check_links.py
Exits non-zero if any problem is found.
"""
import glob
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSET_EXT = r"\.(?:png|jpg|jpeg|gif|svg|webp|ico|pdf|css|js)"
LINK_RE = re.compile(r'(?:src|href)="([^"]+' + ASSET_EXT + r')"', re.IGNORECASE)


def build_file_index(root):
    index = {}
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for name in filenames:
            rel = os.path.normpath(os.path.relpath(os.path.join(dirpath, name), root))
            index[rel.lower()] = rel
    return index


def main():
    html_files = glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(
        os.path.join(ROOT, "**", "*.html"), recursive=True
    )
    html_files = sorted(set(html_files))
    file_index = build_file_index(ROOT)

    problems = []
    for hf in html_files:
        rel_hf = os.path.relpath(hf, ROOT)
        content = open(hf, encoding="utf-8", errors="ignore").read()
        base_dir = os.path.dirname(hf)
        for m in LINK_RE.finditer(content):
            link = urllib.parse.unquote(m.group(1))
            if link.startswith("http") or link.startswith("//") or link.startswith("#"):
                continue
            path = os.path.normpath(os.path.join(base_dir, link))
            rel_path = os.path.relpath(path, ROOT)
            key = rel_path.lower()
            if key not in file_index:
                problems.append((rel_hf, link, "NOT FOUND"))
            elif file_index[key] != rel_path:
                problems.append(
                    (rel_hf, link, f"CASE MISMATCH -> actual file is {file_index[key]}")
                )

    if problems:
        print("Broken or case-mismatched asset links found:\n")
        for hf, link, reason in problems:
            print(f"  {hf}: \"{link}\" -- {reason}")
        print(f"\n{len(problems)} problem(s). These will 404 on GitHub Pages "
              "even if they work locally on Windows/macOS.")
        return 1

    print(f"Checked {len(html_files)} HTML file(s) - all local asset links OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
