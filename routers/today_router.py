from fastapi import APIRouter, Depends, HTTPException
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import Session
import json
from routers.auth_router import get_current_user, User, get_db, Base, engine
import os
from collections import defaultdict
import hashlib
from pydantic import BaseModel

router = APIRouter(prefix="/api")

# -------------------------
# DB
# -------------------------

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    date = Column(String)
    poem_id = Column(Integer)
    line_id = Column(Integer)
    subline_index = Column(Integer)

    __table_args__ = (
        UniqueConstraint("user_id", "date"),
    )

Base.metadata.create_all(bind=engine)

# -------------------------
# schemas
# -------------------------

class SelectPoemRequest(BaseModel):
    poem_id: int

# -------------------------
# DATA LOAD
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../../data/corpus")

with open(os.path.join(DATA_DIR, "poems_final.json"), encoding="utf-8") as f:
    POEMS_DATA = json.load(f)
    POEMS = POEMS_DATA["poems"]
    BINS = POEMS_DATA["bins"]

with open(os.path.join(DATA_DIR, "lines.json"), encoding="utf-8") as f:
    LINES = json.load(f)

poem_map = {p["poem_id"]: p for p in POEMS}

lines_by_poem = {}
index_map = {}

for line in LINES:
    pid = line["poem_id"]
    lines_by_poem.setdefault(pid, []).append(line)

for pid, lines in lines_by_poem.items():
    # Keep poem order deterministic: line first, then subline.
    sorted_lines = sorted(lines, key=lambda x: (x["line_id"], x["subline_index"]))
    lines_by_poem[pid] = sorted_lines

    for idx, l in enumerate(sorted_lines):
        index_map[(pid, l["line_id"], l["subline_index"])] = idx


# -------------------------
# helpers
# -------------------------

def get_today():
    return date.today().isoformat()


def get_week_index(cycle_start_date: str):
    d0 = datetime.fromisoformat(cycle_start_date).date()
    return (date.today() - d0).days // 7


def pick_poem(user_id: int, week_index: int):
    # Deterministic across process restarts (Python hash is salted).
    digest = hashlib.sha256(f"{user_id}_{week_index}".encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big")
    bin0 = BINS[0]
    poem = bin0[seed % len(bin0)]
    return poem["poem_id"]


def build_history(db: Session, user_id: int):
    all_progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id)
        .order_by(UserProgress.date.asc())
        .all()
    )

    history = []

    for p in all_progress:
        sorted_lines = lines_by_poem[p.poem_id]

        current = next(
            l for l in sorted_lines
            if l["line_id"] == p.line_id and l["subline_index"] == p.subline_index
        )

        lines = [current]

        if len(current.get("lemmas", [])) == 1:
            next_line = next(
                (l for l in sorted_lines if l["line_id"] == current["line_id"] + 1),
                None
            )
            if next_line:
                lines.append(next_line)

        history.append({
            "date": p.date,
            "poem_id": p.poem_id,
            "lines": lines
        })

    return history

def build_history_grouped(db: Session, user_id: int):
    all_progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id)
        .order_by(UserProgress.date.asc())
        .all()
    )

    today = get_today()
    current = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == user_id,
            UserProgress.date == today
        )
        .first()
    )
    current_poem_id = current.poem_id if current else None

    grouped = defaultdict(list)

    for p in all_progress:
        grouped[p.poem_id].append(p)

    result = []

    for poem_id, progresses in grouped.items():
        poem = poem_map[poem_id]
        sorted_lines = lines_by_poem.get(poem_id, [])

        lines = []
        for p in progresses:
            lines.append({
                "date": p.date,
                "line_id": p.line_id,
                "subline_index": p.subline_index
            })
        last_progress = progresses[-1] if progresses else None
        last_line = None
        if last_progress:
            last_line = next(
                (
                    l for l in sorted_lines
                    if l["line_id"] == last_progress.line_id
                    and l["subline_index"] == last_progress.subline_index
                ),
                None
            )
        total_lines = len(sorted_lines)
        seen = {(p.line_id, p.subline_index) for p in progresses}
        progress_percent = round((len(seen) / total_lines) * 100, 2) if total_lines else 0.0
        is_current = poem_id == current_poem_id

        result.append({
            "poem_id": poem_id,
            "title": poem["title"],
            "author": poem["author"],
            "lines": lines,
            "progress_percent": progress_percent,
            "isCurrent": is_current,
            "last_line": last_line
        })

    return result

# -------------------------
# core logic
# -------------------------

def get_today_line(user: User, db: Session):
    today = date.today().isoformat()

    # 1. 오늘 기록
    existing = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == user.id,
            UserProgress.date == today
        )
        .first()
    )

    if existing:
        poem_id = existing.poem_id
        sorted_lines = lines_by_poem[poem_id]

        # current 찾기
        current = next(
            l for l in sorted_lines
            if l["line_id"] == existing.line_id and l["subline_index"] == existing.subline_index
        )

    else:
        # 2. week 계산
        week_index = get_week_index(user.cycle_start_date)

        # 3. poem 선택
        poem_id = pick_poem(user.id, week_index)
        sorted_lines = lines_by_poem[poem_id]

        # 4. 이전 progress (same poem)
        prev = (
            db.query(UserProgress)
            .filter(
                UserProgress.user_id == user.id,
                UserProgress.poem_id == poem_id
            )
            .order_by(UserProgress.date.desc())
            .first()
        )

        if not prev:
            current = sorted_lines[0]

        else:
            next_line = next(
                (l for l in sorted_lines if l["line_id"] == prev.line_id + 1),
                None
            )

            if next_line:
                current = next_line
            else:
                # cycle reset
                user.cycle_start_date = today
                db.commit()

                poem_id = pick_poem(user.id, 0)
                sorted_lines = lines_by_poem[poem_id]
                current = sorted_lines[0]
        # 5. 저장
        progress = UserProgress(
            user_id=user.id,
            date=today,
            poem_id=poem_id,
            line_id=current["line_id"],
            subline_index=current["subline_index"]
        )

        db.add(progress)
        db.commit()

    return {
        "poem": poem_map[poem_id],
        "current": current,
        "history": build_history(db, user.id)
    }


# -------------------------
# APIs
# -------------------------

@router.get("/today")
def today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_today_line(current_user, db)

@router.get("/history")
def history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "history": build_history_grouped(db, current_user.id)
    }

@router.post("/today/select")
def select_today_poem(
    payload: SelectPoemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    poem_id = payload.poem_id
    if poem_id not in poem_map:
        raise HTTPException(status_code=404, detail="poem not found")

    sorted_lines = lines_by_poem.get(poem_id, [])
    if not sorted_lines:
        raise HTTPException(status_code=400, detail="poem has no lines")

    today = get_today()
    current_user.cycle_start_date = today

    progress = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == current_user.id,
            UserProgress.date == today
        )
        .first()
    )

    first_line = sorted_lines[0]
    if progress:
        progress.poem_id = poem_id
        progress.line_id = first_line["line_id"]
        progress.subline_index = first_line["subline_index"]
    else:
        progress = UserProgress(
            user_id=current_user.id,
            date=today,
            poem_id=poem_id,
            line_id=first_line["line_id"],
            subline_index=first_line["subline_index"]
        )
        db.add(progress)

    db.commit()

    return get_today_line(current_user, db)
