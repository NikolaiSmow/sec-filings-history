# Plan: SEC Filings Git History Pipeline

## Context
Build a Python pipeline that pulls 10-K filings from SEC EDGAR for 5 companies and stores them as git commits backdated to the actual filing date. Each filing populates per-section markdown files (Item 1A, Item 3, etc.), so `git log`, `git diff`, and `git blame` work as a time machine for corporate disclosures.

**Chosen companies:** NVDA, META, TSLA, AAPL, AMZN
**History range:** 2010–present (~14 years, ~70 commits total across all companies)

| Ticker | Story |
|--------|-------|
| NVDA | "AI" first enters risk factors ~2017, explodes post-2022 |
| META | Cambridge Analytica, GDPR, FTC all appear as legal proceedings commits |
| TSLA | Going concern language appears/disappears, Elon comp drama |
| AAPL | Conservative baseline, China risk evolution |
| AMZN | AWS emergence in business desc, antitrust in legal proceedings |

---

## Architecture

```
pipeline/
  fetch.py          # Pulls filings from EDGAR via edgartools
  extract.py        # Parses markdown → per-section .md files
  commit.py         # Creates backdated git commits
  run.py            # Orchestrator

output-repo/        # The actual git repo that IS the product
  NVDA/
    item-1a-risk-factors.md
    item-1c-cybersecurity.md      # Only available from 2023+
    item-3-legal-proceedings.md
    item-13-related-parties.md
  META/
    ...
  TSLA/ AAPL/ AMZN/
  README.md         # Demo commands, viral examples
```

---

## Implementation Steps

### 1. Setup
```bash
mkdir sec-filings-history && cd sec-filings-history
python -m venv venv && source venv/bin/activate
pip install edgartools gitpython
git init output-repo
```

### 2. fetch.py — Pull filings from EDGAR
```python
from edgar import Company

def get_10k_filings(ticker: str):
    company = Company(ticker)
    filings = company.get_filings(form="10-K")
    return filings  # edgartools handles rate limiting + CIK lookup
```

### 3. extract.py — Parse sections from each filing
Use `filing.markdown()` from edgartools, then extract sections by regex-matching `Item N` headers in the markdown output.

Sections to extract:
- `item-1a-risk-factors.md`
- `item-1c-cybersecurity.md` (skip gracefully if not present, i.e. pre-2023)
- `item-3-legal-proceedings.md`
- `item-13-related-parties.md`

Fallback for older filings: parse raw HTML via BeautifulSoup with fuzzy Item header matching.

### 4. commit.py — Backdated git commits
Use `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` env vars to stamp each commit with the actual SEC filing date.

```python
import subprocess, os

def make_commit(repo_path, ticker, filing_date, form_type, period):
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = filing_date.isoformat()
    env["GIT_COMMITTER_DATE"] = filing_date.isoformat()

    subprocess.run(["git", "add", ticker + "/"], cwd=repo_path)
    subprocess.run([
        "git", "commit", "-m",
        f"{ticker} {form_type} filed {filing_date} (FY{period})"
    ], cwd=repo_path, env=env)
```

### 5. run.py — Orchestrator
For each ticker → fetch all 10-Ks → sort by filing date → extract sections → commit chronologically

### 6. README.md — The viral demo content
Include copy-pasteable commands that show the magic:
```bash
# When did NVDA first mention "artificial intelligence" in risk factors?
git log --all --oneline -- NVDA/item-1a-risk-factors.md | tail -5

# What changed in Meta's legal proceedings after Cambridge Analytica?
git diff HEAD~3 HEAD -- META/item-3-legal-proceedings.md

# Show full history of Tesla going concern language
git log -p -- TSLA/item-1a-risk-factors.md | grep -A5 "going concern"

# Every company that added "tariff" to risk factors in 2025
git log --after="2025-01-01" --before="2025-12-31" -p -- */item-1a-risk-factors.md | grep "^+" | grep -i tariff
```

---

## Key Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Language | Python | edgartools is Python-native, no JS equivalent |
| EDGAR access | edgartools library | Handles CIK lookup, rate limiting, HTML parsing |
| HTML→MD | `filing.markdown()` | Built-in, handles SEC-specific HTML quirks |
| Section extraction | Regex on markdown output | Simpler than raw HTML parsing for modern filings |
| Git commits | subprocess + GIT_AUTHOR_DATE | Backdated commits preserve historical timeline |
| Scope | 10-K only (not 10-Q) for v1 | Simpler, one commit per year per company |

---

## Gotchas
- **Pre-2009 filings**: unstructured HTML, section headers are inconsistent. Start from 2005 or 2010 and note the cutoff.
- **Item 1C** (Cybersecurity): only required from FY2023 onwards — skip gracefully.
- **Section boundary detection**: Item headers in markdown may be `##`, `###`, `**Item 1A**`, or plain text — need fuzzy matching.
- **Rate limit**: EDGAR caps at 10 req/sec. edgartools handles this but add a `time.sleep(0.1)` between filings to be safe.
- **User-Agent header**: SEC requires a descriptive User-Agent (name + email). Set via `edgar.set_identity("Your Name your@email.com")`.

---

## Verification
1. Run pipeline for NVDA only first
2. `cd output-repo && git log --oneline -- NVDA/item-1a-risk-factors.md` — should show ~20 commits spanning years
3. `git diff HEAD~1 HEAD -- NVDA/item-1a-risk-factors.md` — verify diff is readable and meaningful
4. Check commit dates match actual SEC filing dates on EDGAR
5. Confirm Item 1C only appears from 2023 commits onward
