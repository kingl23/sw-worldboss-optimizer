# io_utils.py
import json
import glob
import os


def load_latest_json(keyword):
    # Find JSON files containing keyword
    candidates = (glob.glob(f"attached_assets/*{keyword}*.json") +
                  glob.glob(f"*{keyword}*.json"))

    if not candidates:
        raise FileNotFoundError(f"No JSON file containing '{keyword}' found")

    path = sorted(candidates)[-1]
    print("Using file:", path)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
