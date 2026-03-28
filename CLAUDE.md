# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SEC Filing History Tracker — a Python pipeline that fetches 10-K annual reports from SEC EDGAR, extracts key disclosure sections, and stores them in a git repository (`output-repo/`) with backdated commits matching actual filing dates. This creates a queryable historical archive (2010–present) for tech companies (NVDA, META, TSLA, AAPL, AMZN).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run for all tickers
python run.py

# Run for specific tickers
python run.py NVDA META

# Query the generated archive
cd output-repo
git log --oneline -- NVDA/item-1a-risk-factors.md
git diff HEAD~1 -- NVDA/item-1a-risk-factors.md
git blame NVDA/item-1a-risk-factors.md
```

## Architecture

Three-stage pipeline: **Fetch → Extract → Commit**

- **`run.py`** — Orchestrator. Configures SEC identity, parses CLI args for ticker selection, chains the three stages.
- **`fetch.py`** — Uses `edgartools` to query SEC EDGAR for 10-K filings. Respects SEC rate limit (0.1s between requests). Returns filing metadata sorted by date.
- **`extract.py`** — Converts filings to markdown via `filing.markdown()`, then uses regex to extract specific sections (Item 1A: Risk Factors, Item 1C: Cybersecurity, Item 3: Legal Proceedings, Item 13: Related Party Transactions). Writes per-section `.md` files under `output-repo/{TICKER}/`.
- **`commit.py`** — Creates backdated git commits using `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` environment variables so commit timestamps match SEC filing dates.

## Key Details

- SEC EDGAR requires a User-Agent identity — configured via `SEC_IDENTITY` in `run.py` and `set_identity()`.
- `output-repo/` is a generated git repository, not the source repo. It is the pipeline's output artifact.
- Each disclosure section is a separate file to enable granular `git diff`/`git blame`/`git log` queries.
- Item 1C (Cybersecurity) only exists in filings from FY2023 onward.
- The pipeline is deterministic — reruns produce identical output.
