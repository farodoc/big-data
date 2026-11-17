from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import requests

from .config import GH_ARCHIVE_URL, RAW_DATA_DIR


def download_files(
    years: list[int],
    destination: Path,
    max_gb: float | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if start_date is None:
        start_date = date(min(years), 1, 1)
    if end_date is None:
        end_date = date(max(years), 12, 31)
    if start_date > end_date:
        raise ValueError("--start-date musi być wcześniejsza lub równa --end-date")
    limit = max_gb * 1024**3 if max_gb is not None else None
    downloaded = sum(path.stat().st_size for path in destination.glob("*.json.gz"))
    current = start_date
    while current <= end_date:
        for hour in range(24):
            filename = f"{current:%Y-%m-%d}-{hour}.json.gz"
            target = destination / filename
            if target.exists() and target.stat().st_size > 0:
                continue
            if limit is not None and downloaded >= limit:
                print(f"[limit] Osiągnięto około {max_gb:.2f} GB.")
                return
            url = f"{GH_ARCHIVE_URL}/{filename}"
            print(f"[download] {url}")
            response = requests.get(url, stream=True, timeout=(30, 300))
            response.raise_for_status()
            temporary = target.with_suffix(".part")
            try:
                with temporary.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            file.write(chunk)
                temporary.replace(target)
                downloaded += target.stat().st_size
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        current += timedelta(days=1)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument("--max-gb", type=float, help="Stop after approximately this many GB")
    parser.add_argument("--start-date", type=date.fromisoformat, help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=date.fromisoformat, help="End date YYYY-MM-DD")
    parser.add_argument("--destination", type=Path, default=RAW_DATA_DIR)


def main(args: argparse.Namespace) -> None:
    if any(year < 2011 or year > 2100 for year in args.years):
        raise ValueError("--years musi zawierać lata od 2011 wzwyż")
    if args.max_gb is not None and args.max_gb <= 0:
        raise ValueError("--max-gb musi być dodatnie")
    download_files(args.years, args.destination, args.max_gb, args.start_date, args.end_date)
