"""
extract.py — Extract specific Items from a 10-K filing and write them as markdown files.

Sections extracted:
  item-1a-risk-factors.md
  item-1c-cybersecurity.md      (only exists from FY2023 onwards)
  item-3-legal-proceedings.md
  item-13-related-parties.md
"""

import re
import os
from pathlib import Path

# Maps section slug → list of header patterns to match (case-insensitive)
SECTIONS = {
    "item-1a-risk-factors": [
        r"item\s+1a[\.\s]",
        r"risk\s+factors",
    ],
    "item-1c-cybersecurity": [
        r"item\s+1c[\.\s]",
        r"cybersecurity",
    ],
    "item-3-legal-proceedings": [
        r"item\s+3[\.\s]",
        r"legal\s+proceedings",
    ],
    "item-13-related-parties": [
        r"item\s+13[\.\s]",
        r"related\s+party\s+transactions",
        r"certain\s+relationships",
    ],
}

# Regex to detect any "Item N" header line — used as a section boundary
ITEM_HEADER_RE = re.compile(
    r"^#{1,4}\s+item\s+\d+[a-z]?[\.\s]", re.IGNORECASE | re.MULTILINE
)


def _matches_section(line: str, patterns: list[str]) -> bool:
    """Return True if the line matches any of the section's header patterns."""
    line_lower = line.lower()
    return any(re.search(p, line_lower) for p in patterns)


def _is_any_item_header(line: str) -> bool:
    """Return True if this line looks like any Item header."""
    return bool(ITEM_HEADER_RE.match(line))


def extract_sections(filing, ticker: str, output_dir: Path) -> dict[str, bool]:
    """
    Given an edgartools Filing object, extract target sections and write them
    as individual .md files under output_dir/ticker/.

    Returns a dict of {section_slug: was_found}.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[extract] Converting {ticker} filing to markdown...")
    try:
        md_text = filing.markdown()
    except Exception as e:
        print(f"[extract] WARNING: Could not get markdown for {ticker}: {e}")
        return {}

    lines = md_text.splitlines()
    found = {slug: False for slug in SECTIONS}

    for slug, patterns in SECTIONS.items():
        section_lines = []
        in_section = False

        for i, line in enumerate(lines):
            if not in_section:
                # Look for the section header
                if _matches_section(line, patterns):
                    in_section = True
                    section_lines.append(line)
            else:
                # We're inside the section — stop at the next Item header
                # (but not the very first line, which is the section itself)
                if i > 0 and _is_any_item_header(line):
                    # Make sure it's a *different* item than the one we're in
                    if not _matches_section(line, patterns):
                        break
                section_lines.append(line)

        if section_lines:
            found[slug] = True
            content = "\n".join(section_lines).strip()
            out_path = output_dir / f"{slug}.md"
            out_path.write_text(content, encoding="utf-8")
            print(f"[extract]   Wrote {out_path.name} ({len(content):,} chars)")
        else:
            # Section not found — this is normal for item-1c before FY2023
            print(f"[extract]   Section '{slug}' not found in this filing (skipped)")

    return found


if __name__ == "__main__":
    # Quick smoke test on a single NVDA filing
    from edgar import Company, set_identity
    set_identity("Your Name your@email.com")

    company = Company("NVDA")
    filings = company.get_filings(form="10-K")
    latest = filings[0]  # Most recent

    out = Path("output-repo") / "NVDA"
    result = extract_sections(latest, "NVDA", out)
    print("\nResults:", result)
