from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT_DIR = ROOT / "output"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "github_archive")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "events")
GH_ARCHIVE_URL = "https://data.gharchive.org"
