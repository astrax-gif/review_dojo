"""Game layer: XP, levels, locks, streaks and achievements."""
from datetime import date, datetime, timedelta, timezone

from .scoring import WEIGHT

TITLES = {1: "Script Kiddie", 2: "Packet Sniffer", 3: "Bug Hunter", 4: "Code Auditor",
          5: "Exploit Analyst", 6: "Red Teamer", 7: "Zero-Day Hunter", 8: "Shadow Admin"}
REQUIRED_LEVEL = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}

ACHIEVEMENTS = [
    ("first_blood", "First Blood", "🩸", "Submit your first review"),
    ("sniper", "Sniper", "🎯", "Catch 2+ flaws with zero false alarms"),
    ("sec5", "Security Specialist", "🛡️", "Catch 5 security flaws"),
    ("poly", "Polyglot", "🌍", "Review code in all 4 languages"),
    ("streak3", "On Fire", "🔥", "Review on 3 days in a row"),
    ("sensei", "Sensei Rank", "🥋", "Score 90+ on a pull request"),
    ("perfect", "Perfect Sweep", "💯", "Score 100 on a pull request"),
    ("level5", "Exploit Analyst", "⚡", "Reach level 5"),
]


def level_for(xp: int) -> int:
    return int((max(xp, 0) / 40) ** 0.5) + 1


def level_floor(level: int) -> int:
    return 40 * (level - 1) ** 2


def progress(xp: int) -> dict:
    lvl = level_for(xp)
    lo, hi = level_floor(lvl), level_floor(lvl + 1)
    return {"level": lvl, "title": TITLES.get(lvl, "Root"), "xp": xp,
            "xp_in_level": xp - lo, "xp_needed": hi - lo}


def required_level(difficulty: str) -> int:
    return REQUIRED_LEVEL.get(difficulty, 1)


def raw_xp(result: dict) -> int:
    """XP a review is worth: score + 5 per severity point caught + bonus for 90+."""
    bonus = sum(WEIGHT[c["severity"]] * 5 for c in result["caught"])
    return result["score"] + bonus + (25 if result["score"] >= 90 else 0)


def streaks(days: set[date]) -> tuple[int, int]:
    if not days:
        return 0, 0
    ordered = sorted(days)
    longest = run = 1
    for a, b in zip(ordered, ordered[1:]):
        run = run + 1 if (b - a).days == 1 else 1
        longest = max(longest, run)
    today = datetime.now(timezone.utc).date()
    d = today if today in days else today - timedelta(days=1)
    cur = 0
    while d in days:
        cur += 1
        d -= timedelta(days=1)
    return cur, longest


def unlocked(reviews: list, lang_by_ex: dict, level: int) -> set[str]:
    got: set[str] = set()
    if reviews:
        got.add("first_blood")
    sec = 0
    langs: set[str] = set()
    days: set[date] = set()
    for r in reviews:
        res = r.result
        langs.add(lang_by_ex.get(r.exercise_id, ""))
        days.add(r.created_at.date())
        sec += sum(1 for c in res.get("caught", []) if c["category"] == "security")
        if len(res.get("caught", [])) >= 2 and not res.get("false_alarms"):
            got.add("sniper")
        if r.score >= 90:
            got.add("sensei")
        if r.score >= 100:
            got.add("perfect")
    if sec >= 5:
        got.add("sec5")
    if {"Python", "JavaScript", "Java", "SQL"} <= langs:
        got.add("poly")
    if streaks(days)[1] >= 3:
        got.add("streak3")
    if level >= 5:
        got.add("level5")
    return got


def achievement_list(got: set[str]) -> list[dict]:
    return [{"id": i, "name": n, "icon": ic, "desc": d, "unlocked": i in got} for i, n, ic, d in ACHIEVEMENTS]
