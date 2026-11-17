from __future__ import annotations

import argparse
import gzip
import json
import logging
from pathlib import Path

from pymongo import MongoClient

from .config import MONGO_COLLECTION, MONGO_DATABASE, MONGO_URI, RAW_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)


def clean_event(event: dict) -> dict | None:
    event_type = event.get("type")
    actor = event.get("actor") or {}
    repo = event.get("repo") or {}
    created_at = event.get("created_at")
    if not all(isinstance(value, str) and value for value in (event_type, created_at)):
        return None
    if not isinstance(actor.get("login"), str) or not isinstance(repo.get("name"), str):
        return None
    if event_type.endswith("Event") is False:
        return None
    return {
        "event_id": event.get("id"),
        "event_type": event_type,
        "created_at": created_at,
        "actor_login": actor["login"],
        "repo_name": repo["name"],
        "public": bool(event.get("public", False)),
    }


def import_directory(input_dir: Path, batch_size: int) -> tuple[int, int]:
    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DATABASE][MONGO_COLLECTION]
    collection.drop()
    collection.create_index("created_at")
    collection.create_index("event_type")
    collection.create_index("repo_name")
    inserted = rejected = 0
    try:
        for path in sorted(input_dir.glob("*.json.gz")):
            LOGGER.info("Importowanie %s", path.name)
            batch: list[dict] = []
            with gzip.open(path, "rt", encoding="utf-8") as file:
                for line in file:
                    try:
                        cleaned = clean_event(json.loads(line))
                    except (json.JSONDecodeError, TypeError):
                        cleaned = None
                    if cleaned is None:
                        rejected += 1
                    else:
                        batch.append(cleaned)
                    if len(batch) >= batch_size:
                        collection.insert_many(batch, ordered=False)
                        inserted += len(batch)
                        batch.clear()
            if batch:
                collection.insert_many(batch, ordered=False)
                inserted += len(batch)
        LOGGER.info("Zaimportowano: %s, odrzucono: %s", inserted, rejected)
        return inserted, rejected
    finally:
        client.close()


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--batch-size", type=int, default=5000)


def main(args: argparse.Namespace) -> None:
    if args.batch_size <= 0:
        raise ValueError("--batch-size musi być dodatni")
    import_directory(args.input_dir, args.batch_size)
