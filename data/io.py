import json
from pathlib import Path


def load_latest_json(keyword):
    """Load the most recent JSON file matching the keyword."""
    repo_root = Path(__file__).resolve().parents[1]
    candidates = list(repo_root.glob(f"attached_assets/*{keyword}*.json"))
    candidates.extend(repo_root.glob(f"*{keyword}*.json"))

    if not candidates:
        raise FileNotFoundError(f"No JSON file containing '{keyword}' found")

    path = sorted(candidates)[-1]
    print("Using file:", path)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
