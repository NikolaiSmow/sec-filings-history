"""
run.py — Orchestrator. Runs the full pipeline for all tickers.

Usage:
  python run.py              # Run all tickers
  python run.py NVDA         # Run a single ticker (for testing)
  python run.py NVDA META    # Run specific tickers

Output: output-repo/ — a git repository with backdated commits.
"""

import sys
from pathlib import Path
from edgar import set_identity

from fetch import get_filings, TICKERS
from extract import extract_sections
from commit import init_repo, stage_and_commit

# ── Config ────────────────────────────────────────────────────────────────────
# Replace with your name and email before running.
# The SEC requires a descriptive User-Agent header on all EDGAR API requests.
SEC_IDENTITY = "Your Name your@email.com"

OUTPUT_REPO = Path(__file__).parent / "output-repo"
# ──────────────────────────────────────────────────────────────────────────────


def run(tickers: list[str]) -> None:
    set_identity(SEC_IDENTITY)
    init_repo(OUTPUT_REPO)

    for ticker in tickers:
        print(f"\n{'='*60}")
        print(f"Processing {ticker}")
        print(f"{'='*60}")

        filings = get_filings(ticker)
        if not filings:
            print(f"[run] No filings found for {ticker}, skipping")
            continue

        for entry in filings:
            print(f"\n[run] {ticker} | {entry['filing_date']} | period {entry['period']}")

            # Extract sections into output-repo/TICKER/
            ticker_dir = OUTPUT_REPO / ticker
            extract_sections(entry["filing"], ticker, ticker_dir)

            # Commit with the real filing date
            stage_and_commit(
                repo_path=OUTPUT_REPO,
                ticker=ticker,
                filing_date=entry["filing_date"],
                period=entry["period"],
            )

    print(f"\n{'='*60}")
    print("Done! Your git history is ready.")
    print(f"\nTry these commands in {OUTPUT_REPO}:")
    print()
    print("  # Full history for NVDA risk factors")
    print("  git log --oneline -- NVDA/item-1a-risk-factors.md")
    print()
    print("  # What changed in NVDA's risk factors last year?")
    print("  git diff HEAD~1 HEAD -- NVDA/item-1a-risk-factors.md")
    print()
    print("  # When did NVDA first mention 'artificial intelligence'?")
    print("  git log -p -- NVDA/item-1a-risk-factors.md | grep -B3 'artificial intelligence' | head -20")
    print()
    print("  # Every company that mentioned 'tariff' in 2025 filings")
    print("  git log --after='2025-01-01' --before='2026-01-01' -p -- '*/item-1a-risk-factors.md' | grep '^+' | grep -i tariff")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Allow overriding tickers from command line: python run.py NVDA META
    tickers = sys.argv[1:] if len(sys.argv) > 1 else TICKERS
    run(tickers)
