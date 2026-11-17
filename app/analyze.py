from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pymongo import MongoClient

from .config import DEFAULT_OUTPUT_DIR, MONGO_COLLECTION, MONGO_DATABASE, MONGO_URI


def _run_analyses(collection) -> dict:
    totals = list(collection.aggregate([
        {"$group": {
            "_id": None,
            "events": {"$sum": 1},
            "unique_actors": {"$addToSet": "$actor_login"},
            "unique_repositories": {"$addToSet": "$repo_name"},
        }},
        {"$project": {
            "_id": 0,
            "events": 1,
            "unique_actors": {"$size": "$unique_actors"},
            "unique_repositories": {"$size": "$unique_repositories"},
        }},
    ]))
    by_type = list(collection.aggregate([
        {"$group": {"_id": "$event_type", "events": {"$sum": 1}}},
        {"$sort": {"events": -1}},
        {"$limit": 15},
    ]))
    by_hour = list(collection.aggregate([
        {"$project": {"hour": {"$toInt": {"$substr": ["$created_at", 11, 2]}}}},
        {"$group": {"_id": "$hour", "events": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]))
    by_repo = list(collection.aggregate([
        {"$group": {"_id": "$repo_name", "events": {"$sum": 1}}},
        {"$sort": {"events": -1}},
        {"$limit": 10},
    ]))
    return {
        "descriptive_statistics": totals[0] if totals else {},
        "most_common_event_types": [{"event_type": r["_id"], "events": r["events"]} for r in by_type],
        "events_by_hour_utc": [{"hour": r["_id"], "events": r["events"]} for r in by_hour],
        "most_active_repositories": [{"repository": r["_id"], "events": r["events"]} for r in by_repo],
    }


def _save_figures(results: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    types = results["most_common_event_types"]
    plt.figure(figsize=(10, 6))
    plt.barh([r["event_type"] for r in reversed(types)], [r["events"] for r in reversed(types)])
    plt.title("15 najczęstszych typów zdarzeń GitHub")
    plt.xlabel("Liczba zdarzeń")
    plt.tight_layout()
    plt.savefig(directory / "event_types.png", dpi=150)
    plt.close()

    hours = results["events_by_hour_utc"]
    plt.figure(figsize=(10, 5))
    plt.bar([r["hour"] for r in hours], [r["events"] for r in hours])
    plt.title("Zdarzenia według godziny UTC")
    plt.xlabel("Godzina UTC")
    plt.ylabel("Liczba zdarzeń")
    plt.xticks(range(24))
    plt.tight_layout()
    plt.savefig(directory / "events_by_hour.png", dpi=150)
    plt.close()

    repositories = results["most_active_repositories"]
    plt.figure(figsize=(10, 6))
    plt.barh(
        [r["repository"] for r in reversed(repositories)],
        [r["events"] for r in reversed(repositories)],
    )
    plt.title("10 najaktywniejszych repozytoriów")
    plt.xlabel("Liczba zdarzeń")
    plt.tight_layout()
    plt.savefig(directory / "most_active_repositories.png", dpi=150)
    plt.close()


def _save_summary(results: dict, output_dir: Path) -> None:
    statistics = results["descriptive_statistics"]
    lines = [
        "PODSUMOWANIE ANALIZY GITHUB ARCHIVE",
        "",
        "1. Statystyki zbioru",
        f"Liczba zdarzeń: {statistics.get('events', 0)}",
        f"Liczba unikalnych autorów: {statistics.get('unique_actors', 0)}",
        f"Liczba unikalnych repozytoriów: {statistics.get('unique_repositories', 0)}",
        "",
        "2. Ranking typów zdarzeń: output/figures/event_types.png",
        "3. Aktywność według godziny UTC: output/figures/events_by_hour.png",
        "4. Ranking repozytoriów: output/figures/most_active_repositories.png",
    ]
    (output_dir / "summary.txt").write_text("\n".join(lines), encoding="utf-8")


def analyze(output_dir: Path) -> dict:
    client = MongoClient(MONGO_URI)
    try:
        results = _run_analyses(client[MONGO_DATABASE][MONGO_COLLECTION])
    finally:
        client.close()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _save_figures(results, output_dir / "figures")
    _save_summary(results, output_dir)
    return results


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)


def main(args: argparse.Namespace) -> None:
    print(json.dumps(analyze(args.output_dir), ensure_ascii=False, indent=2))
