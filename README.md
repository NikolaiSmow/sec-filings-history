# sec-filings-history

A Python pipeline that turns SEC 10-K filings into a git repository with backdated commits. Each commit is stamped with the actual SEC filing date, so `git log`, `git diff`, and `git blame` work as a time machine for corporate disclosures.

**Companies:** NVDA, META, TSLA, AAPL, AMZN
**Coverage:** 2010 -- present
**Source:** [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar)

## What's interesting

| Ticker | What you can find |
|--------|-------------------|
| NVDA | "AI" first enters risk factors ~2017, explodes post-2022 |
| META | Cambridge Analytica, GDPR, FTC appear as legal proceedings |
| TSLA | Going concern language appears and disappears, Elon comp drama |
| AAPL | Conservative baseline, China risk evolution over a decade |
| AMZN | AWS emergence in business description, antitrust in legal proceedings |

## Sections extracted

Each company gets four files, extracted from the 10-K annual report:

```
NVDA/
  item-1a-risk-factors.md          Risk Factors (Item 1A)
  item-1c-cybersecurity.md         Cybersecurity (Item 1C, FY2023+ only)
  item-3-legal-proceedings.md      Legal Proceedings (Item 3)
  item-13-related-parties.md       Related Party Transactions (Item 13)
```

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Before running, edit `run.py` and set your SEC identity (required by EDGAR):

```python
SEC_IDENTITY = "Your Name your@email.com"
```

## Usage

```bash
python run.py                # All 5 companies
python run.py NVDA           # Single company
python run.py NVDA META      # Specific companies
```

The pipeline writes to `output-repo/`, a git repository where each commit is one annual filing.

## Querying the output

```bash
cd output-repo

# Full filing history for NVDA risk factors
git log --oneline -- NVDA/item-1a-risk-factors.md

# What changed in the last filing?
git diff HEAD~1 HEAD -- NVDA/item-1a-risk-factors.md

# When did NVIDIA first mention "artificial intelligence"?
git log -p -- NVDA/item-1a-risk-factors.md \
  | grep -B5 -i "artificial intelligence" | head -30

# Meta's legal proceedings after Cambridge Analytica (2018)
git log --after="2018-01-01" --before="2020-01-01" -p \
  -- META/item-3-legal-proceedings.md

# Which companies first disclosed cybersecurity risk? (Item 1C added 2023)
git log --oneline -- '*/item-1c-cybersecurity.md'

# Every company that added "tariff" to risk factors in 2025
git log --after="2025-01-01" --before="2026-01-01" -p \
  -- '*/item-1a-risk-factors.md' | grep "^+" | grep -i tariff

# When was each line in NVDA's current risk factors first introduced?
git blame NVDA/item-1a-risk-factors.md
```

## How it works

Three-stage pipeline: **Fetch -> Extract -> Commit**

1. **fetch.py** -- Queries SEC EDGAR for 10-K filings using [edgartools](https://github.com/dgunning/edgartools). Respects the 10 req/sec rate limit.
2. **extract.py** -- Converts each filing to markdown, then uses regex to extract specific Item sections into separate `.md` files.
3. **commit.py** -- Stages the extracted files and creates a git commit with `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` set to the actual SEC filing date.
4. **run.py** -- Orchestrates the pipeline, processing filings chronologically per company.

## Notes

- The SEC requires a User-Agent header with your name and email on all EDGAR requests.
- Item 1C (Cybersecurity) was only mandated starting FY2023 -- earlier filings won't have it.
- `output-repo/` is gitignored from this repository since it's a generated artifact.
- All section text is extracted verbatim from filed documents.
