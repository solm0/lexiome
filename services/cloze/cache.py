import json, os

CACHE_DIR = "../data/cache/cloze"

def _path(key):
    return f"{CACHE_DIR}/{key}.json"

def load_cache(key):
    path = _path(key)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["items"]

def save_cache(key, items):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_path(key), "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)