"""Scoring engine: compares a learner's inline comments with the planted flaws."""

WEIGHT = {"low": 1, "medium": 2, "high": 3, "critical": 4}
WINDOW = 2  # a comment within 2 lines of a flaw still counts as locating it
REASON_WORDS = ("because", "could", "should", "instead", "which", "use ", "attacker", "unsafe", "risk")


def _clarity_ok(text: str) -> bool:
    t = text.lower()
    return len(text.strip()) >= 25 and any(w in t for w in REASON_WORDS)


def _distance(flaw: dict, line: int) -> int:
    if flaw["line_start"] <= line <= flaw["line_end"]:
        return 0
    return min(abs(line - flaw["line_start"]), abs(line - flaw["line_end"]))


def rank_for(score: int) -> str:
    if score >= 90:
        return "Sensei"
    if score >= 75:
        return "Black Belt"
    if score >= 55:
        return "Brown Belt"
    if score >= 30:
        return "Green Belt"
    return "White Belt"


def public_flaw(f: dict) -> dict:
    return {k: f[k] for k in ("id", "file", "line_start", "line_end", "title", "category", "severity", "explanation")}


def evaluate(flaws: list[dict], comments: list[dict]) -> dict:
    caught: dict[str, dict] = {}
    false_alarms: list[dict] = []
    tips: list[str] = []

    for c in comments:
        text = c["text"].strip()
        target, best = None, 99
        for f in flaws:
            if f["file"] != c["file"]:
                continue
            d = _distance(f, c["line"])
            if d <= WINDOW and d < best:
                target, best = f, d
        if len(text) < 15:
            tips.append(f"Line {c['line']}: '{text}' is too short. Say what is wrong and why it matters.")
        if target is None:
            false_alarms.append(c)
            continue
        hits = [k for k in target["keywords"] if k in text.lower()]
        prev = caught.get(target["id"])
        if prev is None or len(hits) > len(prev["hits"]):
            caught[target["id"]] = {"flaw": target, "comment": c, "hits": hits}

    max_points = sum(WEIGHT[f["severity"]] for f in flaws)
    earned = 0.0
    caught_out = []
    for item in caught.values():
        f, c, hits = item["flaw"], item["comment"], item["hits"]
        quality = 0.6 + (0.3 if hits else 0.0) + (0.1 if _clarity_ok(c["text"]) else 0.0)
        earned += WEIGHT[f["severity"]] * quality
        if not hits:
            tips.append(f"Line {c['line']}: you found the right spot, but name the actual problem (what is it called?).")
        caught_out.append({**public_flaw(f), "comment": c, "quality": round(quality, 2)})

    penalty = min(len(false_alarms) * 1.0, max_points * 0.25)
    score = max(0, min(100, round(100 * (earned - penalty) / max_points))) if max_points else 0
    missed = [public_flaw(f) for f in flaws if f["id"] not in caught]

    n_found, n_total = len(caught), len(flaws)
    if n_found == n_total and not false_alarms:
        mentor = "Perfect sweep. You found every planted flaw with no false alarms."
    elif n_found == 0:
        mentor = "Nothing found this time. Read the code slowly: ask what happens with bad input, bad users and bad timing."
    else:
        worst = max(missed, key=lambda m: WEIGHT[m["severity"]], default=None)
        mentor = f"You found {n_found} of {n_total} flaws."
        if worst:
            mentor += f" The most serious one you missed was a {worst['severity']} {worst['category']} issue: {worst['title']}."
        if false_alarms:
            mentor += f" You also raised {len(false_alarms)} comment(s) on lines that were fine; be sure a comment points at a real risk."

    return {
        "score": score,
        "rank": rank_for(score),
        "earned": round(earned, 2),
        "max_points": max_points,
        "caught": caught_out,
        "missed": missed,
        "false_alarms": false_alarms,
        "tips": tips,
        "mentor": mentor,
    }
