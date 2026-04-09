from fastapi import APIRouter, Depends
from datetime import date, datetime
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, Session
import json
from auth_router import get_current_user, User, get_db
import os

router = APIRouter(prefix="/api")

DB_PATH = "user.db"

# -------------------------
# DB
# -------------------------

Base = declarative_base()

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    date = Column(String)
    poem_id = Column(Integer)
    line_id = Column(Integer)
    subline_index = Column(Integer)

# -------------------------
# 데이터 preload (서버 시작 시 실행된다고 가정)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
DATA_DIR = os.path.join(BASE_DIR, "data")

with open(os.path.join(DATA_DIR, "poems_final.json"), encoding="utf-8") as f:
    POEMS_DATA = json.load(f)

with open("data/poems_final.json", encoding="utf-8") as f:
    POEMS_DATA = json.load(f)
    POEMS = POEMS_DATA["poems"]
    BINS = POEMS_DATA["bins"]

with open("data/lines.json", encoding="utf-8") as f:
    LINES = json.load(f)

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
    poem = bin0[seed % len(bin0)]
    return poem["poem_id"]

# -------------------------
# core logic
# -------------------------

def get_today_line(user: User, db: Session):

    today = date.today().isoformat()

    # 1. 오늘 기록
    existing = db.query(UserProgress).filter(
        UserProgress.user_id == user.id,
        UserProgress.date == today
    ).first()

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
        d0 = date.fromisoformat(user.cycle_start_date)
        week_index = (date.today() - d0).days // 7

        # 3. poem 선택
        poem_id = pick_poem(user.id, week_index)
        sorted_lines = lines_by_poem[poem_id]

        # 4. 이전 progress
        prev = db.query(UserProgress).filter(
            UserProgress.user_id == user.id
        ).order_by(UserProgress.date.desc()).first()

        if not prev:
            current = sorted_lines[0]

        else:
            key = (prev.poem_id, prev.line_id, prev.subline_index)
            idx = index_map.get(key, 0)

            next_sub = None
            for l in sorted_lines:
                if l["line_id"] == prev.line_id and l["subline_index"] == prev.subline_index + 1:
                    next_sub = l
                    break

            if next_sub:
                current = next_sub
            else:
                if idx + 1 < len(sorted_lines):
                    current = sorted_lines[idx + 1]
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
    
    all_progress = db.query(UserProgress).filter(
        UserProgress.user_id == user.id
    ).order_by(UserProgress.date.asc()).all()

    history = []

    for p in all_progress:
        poem_id = p.poem_id
        sorted_lines = lines_by_poem[poem_id]

        current = next(
            l for l in sorted_lines
            if l["line_id"] == p.line_id and l["subline_index"] == p.subline_index
        )

        lines = [current]

        if len(current["lemmas"]) == 1:
            next_line = next(
                (l for l in sorted_lines if l["line_id"] == current["line_id"] + 1),
                None
            )
            if next_line:
                lines.append(next_line)

        history.append({
            "date": p.date,
            "lines": lines
        })

    return {
        "poem": poem_map[poem_id],
        "history": history
    }

# -------------------------
# API
# -------------------------

@router.get("/today")
def today(current_user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):

    return get_today_line(current_user, db)