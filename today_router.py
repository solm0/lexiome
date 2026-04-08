from fastapi import APIRouter, Depends
from datetime import date, datetime
import sqlite3
import json
import random

router = APIRouter()

DB_PATH = "users.db"

# -------------------------
# DB
# -------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# 데이터 preload (서버 시작 시 실행된다고 가정)
# -------------------------

with open("data/lines.json", encoding="utf-8") as f:
    LINES = json.load(f)

with open("data/poems.json", encoding="utf-8") as f:
    POEMS_DATA = json.load(f)
    POEMS = POEMS_DATA["poems"]
    BINS = POEMS_DATA["bins"]

# poem_id → poem
poem_map = {p["poem_id"]: p for p in POEMS}

# poem_id → sorted lines
lines_by_poem = {}
index_map = {}  # (poem_id, line_id, subline_index) → idx

for line in LINES:
    pid = line["poem_id"]
    lines_by_poem.setdefault(pid, []).append(line)

for pid, lines in lines_by_poem.items():
    sorted_lines = sorted(
        lines,
        key=lambda x: (x["complexity"], x["line_id"])
    )
    lines_by_poem[pid] = sorted_lines

    for idx, l in enumerate(sorted_lines):
        key = (pid, l["line_id"], l["subline_index"])
        index_map[key] = idx

# -------------------------
# helper
# -------------------------

def get_today():
    return date.today().isoformat()

def get_week_index(cycle_start_date: str):
    d0 = datetime.fromisoformat(cycle_start_date).date()
    return (date.today() - d0).days // 7

def pick_poem(user_id: int, week_index: int):
    seed = hash(f"{user_id}_{week_index}")
    bin0 = BINS[0]
    return bin0[seed % len(bin0)]

# -------------------------
# core logic
# -------------------------

def get_today_line(user_id: int, db: sqlite3.Connection):
    today = get_today()

    # 1. 오늘 기록 있으면 그대로 반환
    row = db.execute(
        "SELECT * FROM user_progress WHERE user_id=? AND date=?",
        (user_id, today)
    ).fetchone()

    if row:
        return dict(row)

    # 2. user 조회
    user = db.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    cycle_start_date = user["cycle_start_date"]
    week_index = get_week_index(cycle_start_date)

    # 3. poem 선택
    poem_id = pick_poem(user_id, week_index)
    sorted_lines = lines_by_poem[poem_id]

    # 4. 이전 progress
    prev = db.execute(
        "SELECT * FROM user_progress WHERE user_id=? ORDER BY date DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    if not prev:
        current = sorted_lines[0]

    else:
        key = (
            prev["poem_id"],
            prev["line_id"],
            prev["subline_index"]
        )

        idx = index_map.get(key, 0)
        prev_line = prev["line_id"]
        prev_sub = prev["subline_index"]

        # 같은 line에서 subline+1
        next_sub = None
        for l in sorted_lines:
            if l["line_id"] == prev_line and l["subline_index"] == prev_sub + 1:
                next_sub = l
                break

        if next_sub:
            current = next_sub
        else:
            # 다음 complexity
            if idx + 1 < len(sorted_lines):
                current = sorted_lines[idx + 1]
            else:
                # poem 끝 → 다음 주로 넘김
                week_index += 1

                db.execute(
                    "UPDATE users SET cycle_start_date=? WHERE user_id=?",
                    (today, user_id)
                )
                db.commit()

                poem_id = pick_poem(user_id, week_index)
                sorted_lines = lines_by_poem[poem_id]
                current = sorted_lines[0]


    # 5. lemma 1개면 하나 더
    result_lines = [current]

    if len(current["lemmas"]) == 1:
        next_line = None
        for l in LINES:
            if (
                l["poem_id"] == poem_id and
                l["line_id"] == current["line_id"] + 1
            ):
                next_line = l
                break

        if next_line:
            result_lines.append(next_line)

    # 6. 저장 (대표로 첫 줄만 저장)
    db.execute(
        """
        INSERT INTO user_progress (user_id, date, poem_id, line_id, subline_index)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            today,
            poem_id,
            current["line_id"],
            current["subline_index"]
        )
    )
    db.commit()

    return {
        "poem": poem_map[poem_id],
        "lines": result_lines
    }

# -------------------------
# API
# -------------------------

@router.get("/today")
def today(current_user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):

    return get_today_line(current_user.id, db)