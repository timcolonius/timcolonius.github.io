#!/usr/bin/env python3
"""
Parse saved HTML pages from colonius.caltech.edu and write alumni_positions.csv.

Before running:
  1. Save https://colonius.caltech.edu/people/former-graduate-students
     to ~/Desktop as "Former Graduate Students*.html"
  2. Save https://colonius.caltech.edu/people/former-postdocs
     to ~/Desktop as "Former Postdocs*.html"

Run:  python3 harvest_alumni.py
Output: alumni_positions.csv
"""

import re, csv
from pathlib import Path

DESKTOP = Path.home() / "Desktop"

# ── Find saved files ───────────────────────────────────────────────────────────

def find_file(keywords):
    for f in DESKTOP.glob("*.html"):
        if all(k.lower() in f.name.lower() for k in keywords):
            return f
    return None

FILES = {
    "GRA Advisee":     find_file(["graduate"]),
    "Postdoc Advisee": find_file(["postdoc"]),
}

# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_file(path, role):
    """
    Each entry is a <li> inside a .rich-text block with the form:
      Name (Year[s]). Present: Position, Institution
    with an optional <a href="..."> wrapping the position text.
    """
    html = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r'<div class="rich-text">(.*?)</div>', html, re.DOTALL)

    rows = []
    for block in blocks:
        items = re.findall(r'<li[^>]*>(.*?)</li>', block, re.DOTALL)
        for item in items:
            text = re.sub(r'<[^>]+>', '', item).strip()
            if not text:
                continue

            # Extract website URL (first external href)
            href_m = re.search(r'href="(https?://[^"]+)"', item)
            website = href_m.group(1) if href_m else ""

            # Parse "Firstname Lastname (Year). Present: Position"
            # Name is everything before the first "("
            name_m = re.match(r'^(.+?)\s*\(', text)
            name = name_m.group(1).strip() if name_m else text

            # Position is everything after "Present:" (strip trailing whitespace/dots)
            pos_m = re.search(r'[Pp]resent:\s*(.+)', text)
            position = pos_m.group(1).strip().rstrip('.') if pos_m else ""

            rows.append({"role": role, "name": name,
                         "position": position, "website": website})
    return rows

# ── Run ────────────────────────────────────────────────────────────────────────

all_rows = []
for role, path in FILES.items():
    if path:
        rows = parse_file(path, role)
        print(f"  {role}: {len(rows)} entries  ← {path.name}")
        all_rows.extend(rows)
    else:
        keywords = "graduate" if "GRA" in role else "postdoc"
        print(f"  {role}: NOT FOUND — save the {keywords} page to Desktop first")

out = Path("alumni_positions.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["role", "name", "position", "website"])
    w.writeheader()
    w.writerows(all_rows)

print(f"\nWrote {len(all_rows)} rows → {out.resolve()}")
print("Columns: role | name | position | website")
