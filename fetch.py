"""
fetch.py — Pull 10-K filings from SEC EDGAR via edgartools.
"""

import time
from edgar import Company, set_identity

# SEC requires a descriptive User-Agent header.
# Replace with your own name and email before running.
set_identity("Your Name your@email.com")

TICKERS = ["NVDA", "META", "TSLA", "AAPL", "AMZN"]
START_YEAR = 2010


def get_filings(ticker: str) -> list[dict]:
    """
    Returns a list of 10-K filing metadata for a ticker, sorted by filing date.
    Each entry has: ticker, filing_date, period_of_report, accession_number, filing object.
    """
    print(f"[fetch] Fetching 10-K filings for {ticker}...")
    company = Company(ticker)
    filings = company.get_filings(form="10-K")

    results = []
    for filing in filings:
        # Filter to filings from START_YEAR onwards
        if filing.filing_date.year < START_YEAR:
            continue
        results.append({
            "ticker": ticker,
            "filing_date": filing.filing_date,
            "period": filing.period_of_report,
            "accession": filing.accession_no,
            "filing": filing,
        })
        time.sleep(0.1)  # Be polite to EDGAR's rate limit (max 10 req/sec)

    results.sort(key=lambda x: x["filing_date"])
    print(f"[fetch] Found {len(results)} filings for {ticker} since {START_YEAR}")
    return results


if __name__ == "__main__":
    for ticker in TICKERS:
        filings = get_filings(ticker)
        for f in filings:
            print(f"  {f['ticker']} | {f['filing_date']} | period: {f['period']}")
