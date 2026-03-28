"""
commit.py — Create backdated git commits in the output repo.

Each commit represents one 10-K filing, stamped with the actual SEC filing date.
This gives the repo a real historical timeline — git log shows real corporate history.
"""

import os
import subprocess
from datetime import date
from pathlib import Path


def init_repo(repo_path: Path) -> None:
    """Initialize the output git repo if it doesn't exist yet."""
    if not (repo_path / ".git").exists():
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        print(f"[commit] Initialized git repo at {repo_path}")


def stage_and_commit(
    repo_path: Path,
    ticker: str,
    filing_date: date,
    period: date | str,
    form_type: str = "10-K",
) -> None:
    """
    Stage all changes under ticker/ and create a backdated commit.

    The commit date is set to the actual SEC filing date, so git log
    shows the real timeline of corporate disclosures.
    """
    ticker_dir = repo_path / ticker
    if not ticker_dir.exists():
        print(f"[commit] WARNING: No files found for {ticker}, skipping commit")
        return

    # Check if there's anything to commit
    status = subprocess.run(
        ["git", "status", "--porcelain", str(ticker)],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        print(f"[commit] No changes for {ticker} on {filing_date}, skipping")
        return

    # Format the filing date as ISO 8601 for git
    date_str = filing_date.isoformat() + "T00:00:00"

    # Period can be a date object or a string like "2023-12-31"
    period_str = str(period)[:4] if period else "unknown"

    commit_message = f"{ticker} {form_type} filed {filing_date} (FY{period_str})"

    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    subprocess.run(["git", "add", ticker], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=repo_path,
        env=env,
        check=True,
    )

    print(f"[commit] Committed: {commit_message}")
