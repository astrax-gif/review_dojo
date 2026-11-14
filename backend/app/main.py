import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import ai, auth, game, models, schemas, scoring
from .db import Base, SessionLocal, engine, get_db
from .seed import seed_exercises


def init_db():
    for _ in range(30):  # wait for Postgres to come up in Docker
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            time.sleep(2)
    with SessionLocal() as db:
        seed_exercises(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Review Dojo API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def exercise_public(ex: models.Exercise, best: int | None = None, level: int = 1) -> dict:
    need = game.required_level(ex.difficulty)
    return {
        "level_required": need, "locked": level < need,
        "id": ex.id, "title": ex.title, "language": ex.language, "difficulty": ex.difficulty,
        "author": ex.author, "description": ex.description, "files": ex.files,
        "flaw_count": len(ex.flaws), "best": best,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=schemas.TokenOut)
def register(body: schemas.Credentials, db: Session = Depends(get_db)):
    if db.scalar(select(models.User).where(models.User.username == body.username)):
        raise HTTPException(409, "Username already taken")
    user = models.User(username=body.username, password_hash=auth.hash_password(body.password))
    db.add(user)
    db.commit()
    return {"token": auth.make_token(user.id), "username": user.username}


@app.post("/api/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.username == body.username))
    if not user or not auth.verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    return {"token": auth.make_token(user.id), "username": user.username}


def user_xp(db: Session, user_id: int | None) -> int:
    if user_id is None:
        return 0
    return sum(x for (x,) in db.execute(select(models.Review.xp_gain).where(models.Review.user_id == user_id)))


def lang_map(db: Session) -> dict:
    return {e.id: e.language for e in db.scalars(select(models.Exercise))}


def best_scores(db: Session, user_id: int | None) -> dict:
    if user_id is None:
        return {}
    best: dict[str, int] = {}
    for r in db.scalars(select(models.Review).where(models.Review.user_id == user_id)):
        best[r.exercise_id] = max(best.get(r.exercise_id, 0), r.score)
    return best


@app.get("/api/exercises")
def list_exercises(db: Session = Depends(get_db), user: models.User | None = Depends(auth.optional_user)):
    uid = user.id if user else None
    best = best_scores(db, uid)
    level = game.level_for(user_xp(db, uid))
    rows = db.scalars(select(models.Exercise)).all()
    rows.sort(key=lambda e: (game.required_level(e.difficulty), e.id))
    return [exercise_public(e, best.get(e.id), level) for e in rows]


@app.get("/api/exercises/{exercise_id}")
def get_exercise(exercise_id: str, db: Session = Depends(get_db),
                 user: models.User | None = Depends(auth.optional_user)):
    ex = db.get(models.Exercise, exercise_id)
    if not ex:
        raise HTTPException(404, "Exercise not found")
    return exercise_public(ex, None, game.level_for(user_xp(db, user.id if user else None)))


@app.post("/api/exercises/{exercise_id}/submit")
def submit(exercise_id: str, body: schemas.SubmitIn, db: Session = Depends(get_db),
           user: models.User | None = Depends(auth.optional_user)):
    ex = db.get(models.Exercise, exercise_id)
    if not ex:
        raise HTTPException(404, "Exercise not found")
    uid = user.id if user else None
    old_xp = user_xp(db, uid)
    need = game.required_level(ex.difficulty)
    if game.level_for(old_xp) < need:
        raise HTTPException(403, f"Locked: reach level {need} to attempt this pull request")
    old_ach: set[str] = set()
    if user:
        old_ach = game.unlocked(db.scalars(select(models.Review).where(models.Review.user_id == uid)).all(),
                                lang_map(db), game.level_for(old_xp))
    comments = [c.model_dump() for c in body.comments]
    result = scoring.evaluate(ex.flaws, comments)
    result["ai_coach"] = ai.coach(ex.title, ex.language, result) if body.use_ai else None
    raw = game.raw_xp(result)
    result["xp_raw"] = raw
    gain = 0
    if user:
        prev = [r.result.get("xp_raw", 0) for r in db.scalars(
            select(models.Review).where(models.Review.user_id == uid, models.Review.exercise_id == ex.id))]
        gain = max(0, raw - max(prev, default=0))
    review = models.Review(user_id=uid, exercise_id=ex.id, comments=comments,
                           score=result["score"], result=result, xp_gain=gain)
    db.add(review)
    db.commit()
    new_xp = old_xp + gain
    new_ach: list[dict] = []
    if user:
        now_ach = game.unlocked(db.scalars(select(models.Review).where(models.Review.user_id == uid)).all(),
                                lang_map(db), game.level_for(new_xp))
        new_ach = [a for a in game.achievement_list(now_ach) if a["unlocked"] and a["id"] not in old_ach]
    return {**result, "review_id": review.id, "saved": user is not None, "xp_gain": gain, "xp_raw": raw,
            "level_up": game.level_for(new_xp) > game.level_for(old_xp),
            "progress": game.progress(new_xp), "new_achievements": new_ach}


@app.get("/api/me/stats")
def my_stats(db: Session = Depends(get_db), user: models.User = Depends(auth.required_user)):
    reviews = db.scalars(select(models.Review).where(models.Review.user_id == user.id)
                         .order_by(models.Review.created_at.desc())).all()
    skills: dict[str, dict] = {}
    for r in reviews:
        for item in r.result.get("caught", []):
            s_ = skills.setdefault(item["category"], {"caught": 0, "total": 0})
            s_["caught"] += 1
            s_["total"] += 1
        for item in r.result.get("missed", []):
            s_ = skills.setdefault(item["category"], {"caught": 0, "total": 0})
            s_["total"] += 1
    titles = {e.id: e.title for e in db.scalars(select(models.Exercise))}
    xp = sum(r.xp_gain for r in reviews)
    prog = game.progress(xp)
    avg = round(sum(r.score for r in reviews) / len(reviews)) if reviews else 0
    cur, longest = game.streaks({r.created_at.date() for r in reviews})
    got = game.unlocked(reviews, lang_map(db), prog["level"])
    return {
        "username": user.username, "reviews": len(reviews), "average": avg,
        "rank": scoring.rank_for(avg) if reviews else "White Belt",
        "progress": prog, "streak": cur, "best_streak": longest,
        "achievements": game.achievement_list(got), "skills": skills,
        "history": [{"exercise": titles.get(r.exercise_id, r.exercise_id), "score": r.score,
                     "xp": r.xp_gain, "at": r.created_at.isoformat()} for r in reviews[:12]],
    }


@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    users = {u.id: u.username for u in db.scalars(select(models.User))}
    xp: dict[int, int] = {}
    count: dict[int, int] = {}
    for r in db.scalars(select(models.Review).where(models.Review.user_id.is_not(None))):
        xp[r.user_id] = xp.get(r.user_id, 0) + r.xp_gain
        count[r.user_id] = count.get(r.user_id, 0) + 1
    rows = [{"username": users[u], "xp": x, "level": game.level_for(x), "title": game.progress(x)["title"],
             "reviews": count[u]} for u, x in xp.items()]
    rows.sort(key=lambda r: (-r["xp"], r["username"]))
    return rows[:20]
