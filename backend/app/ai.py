"""Optional AI mentor. Works only if ANTHROPIC_API_KEY is set; otherwise the app uses the built-in mentor text."""
import os

import httpx


def coach(exercise_title: str, language: str, result: dict) -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    caught = "; ".join(f"{c['title']} (comment: {c['comment']['text']})" for c in result["caught"]) or "none"
    missed = "; ".join(m["title"] for m in result["missed"]) or "none"
    fa = "; ".join(f"line {c['line']}: {c['text']}" for c in result["false_alarms"]) or "none"
    prompt = (
        f"You are a friendly senior engineer mentoring a student who just reviewed a {language} pull request "
        f"called '{exercise_title}'.\nFlaws they caught: {caught}\nFlaws they missed: {missed}\n"
        f"Comments on fine lines: {fa}\nScore: {result['score']}/100.\n"
        "Write 3 short sentences: one praising something specific, one explaining the most important miss "
        "and how to spot it next time, one concrete habit to practise. Plain text, no markdown."
    )
    try:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": os.getenv("AI_MODEL", "claude-sonnet-4-6"),
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=25,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    except Exception:
        return None
