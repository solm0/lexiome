import os
import json

CACHE_DIR = "cache"


def get_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def exists(key: str) -> bool:
    return os.path.exists(get_path(key))


def load(key: str) -> dict:
    with open(get_path(key), "r", encoding="utf-8") as f:
        return json.load(f)


def save(key: str, data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)

    with open(get_path(key), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)