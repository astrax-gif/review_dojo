"""Seed exercises. Lines start with '+ ' (added), '- ' (removed) or '  ' (context).
A trailing '@@F1' tag marks a planted flaw; the tag is stripped and the line number recorded."""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Exercise

TAG = re.compile(r"\s*@@(F\d+)$")


def build(files_spec, flaw_spec):
    files, pos = [], {}
    for path, text in files_spec:
        n, lines = 0, []
        for raw in text.strip("\n").split("\n"):
            tag = None
            m = TAG.search(raw)
            if m:
                tag, raw = m.group(1), raw[: m.start()]
            kind = {"+": "add", "-": "del", " ": "ctx"}[raw[0]] if raw else "ctx"
            code = raw[2:] if len(raw) > 1 else ""
            if kind == "del":
                lines.append({"n": None, "t": kind, "c": code})
                continue
            n += 1
            lines.append({"n": n, "t": kind, "c": code})
            if tag:
                pos.setdefault((path, tag), []).append(n)
        files.append({"path": path, "lines": lines})
    flaws = []
    for f in flaw_spec:
        ns = pos[(f["file"], f["id"])]
        flaws.append({**f, "line_start": min(ns), "line_end": max(ns)})
    return files, flaws


EXERCISES = []


def add(id, title, language, difficulty, description, files, flaws):
    f, fl = build(files, flaws)
    EXERCISES.append(dict(id=id, title=title, language=language, difficulty=difficulty, author="mira-dev",
                          description=description, files=f, flaws=fl))


add("py-login-endpoint", "Add email/password login endpoint", "Python", "Beginner",
    "Adds a /login route so users can sign in with email and password. Tested manually with two accounts.",
    [("app/auth.py", '''
  import hashlib
  from flask import request, jsonify
  from .db import get_conn

+ @app.route("/login", methods=["POST"])
+ def login():
+     data = request.get_json()
+     conn = get_conn()
+     query = f"SELECT id, password FROM users WHERE email = '{data['email']}'"   @@F1
+     row = conn.execute(query).fetchone()
+     if row is None:
+         return jsonify({"error": "No account with that email"}), 404   @@F3
+     if row["password"] == data["password"]:   @@F2
+         return jsonify({"token": make_token(row["id"])})
+     return jsonify({"error": "Wrong password"}), 401
''')],
    [dict(id="F1", file="app/auth.py", title="SQL injection in login query", category="security", severity="critical",
          keywords=["sql", "injection", "parameter", "prepared", "sanitiz", "f-string", "escape", "inject"],
          explanation="User input is pasted straight into the SQL string. An email like ' OR '1'='1 logs an attacker in. Use parameterised queries: conn.execute('... WHERE email = ?', (email,))."),
     dict(id="F2", file="app/auth.py", title="Passwords stored and compared in plain text", category="security", severity="high",
          keywords=["plain", "hash", "bcrypt", "argon", "salt", "password", "scrypt"],
          explanation="Comparing the raw password means passwords are stored unhashed. A database leak exposes every user. Store a salted hash (argon2, bcrypt) and compare with a constant-time check."),
     dict(id="F3", file="app/auth.py", title="Error message reveals which emails exist", category="security", severity="low",
          keywords=["enumerat", "reveal", "exist", "generic", "same error", "leak", "different"],
          explanation="Returning 404 for unknown emails and 401 for wrong passwords lets attackers discover registered accounts. Return one generic 'Invalid email or password' for both cases.")])

add("js-comments-widget", "Comments widget for blog posts", "JavaScript", "Beginner",
    "Loads comments for a post and renders them under the article. Uses our analytics API key for tracking.",
    [("src/comments.js", '''
+ const API_KEY = "sk_live_51Hx9aKJ2eZvKYlo2C0q"   @@F3
+
+ async function loadComments(postId) {
+   const ids = await fetch(`/api/posts/${postId}/comment-ids`).then(r => r.json());
+   const out = [];
+   for (const id of ids) {
+     const c = await fetch(`/api/comments/${id}`).then(r => r.json());   @@F2
+     out.push(c);
+   }
+   return out;
+ }
+
+ function render(comments) {
+   const list = document.getElementById("comments");
+   comments.forEach(c => {
+     list.innerHTML += `<li><b>${c.author}</b>: ${c.body}</li>`;   @@F1
+   });
+ }
''')],
    [dict(id="F1", file="src/comments.js", title="Cross-site scripting (XSS) via innerHTML", category="security", severity="high",
          keywords=["xss", "innerhtml", "script", "sanitiz", "escape", "textcontent", "inject"],
          explanation="Comment author and body are user-controlled and inserted as HTML. A comment containing <img onerror=...> runs code in every reader's browser. Build elements with textContent or sanitise the HTML."),
     dict(id="F2", file="src/comments.js", title="Sequential requests (N+1 fetch) slow the page", category="performance", severity="medium",
          keywords=["n+1", "sequential", "promise.all", "parallel", "batch", "loop", "slow", "await"],
          explanation="Each comment is fetched one after another inside the loop, so 100 comments means 100 waits in a row. Use one batch endpoint or Promise.all to fetch in parallel."),
     dict(id="F3", file="src/comments.js", title="Secret API key hard-coded in source", category="security", severity="critical",
          keywords=["secret", "key", "hard", "env", "commit", "leak", "expose", "credential", "token"],
          explanation="A live secret key in front-end code is visible to everyone and ends up in git history. Rotate it, move it to a server-side environment variable, and proxy calls through your backend.")])

add("java-account-transfer", "Implement money transfer between accounts", "Java", "Intermediate",
    "Adds AccountService.transfer and an audit helper. Unit tests pass for the happy path.",
    [("src/main/java/bank/AccountService.java", '''
+ public class AccountService {
+     private final Map<String, Account> accounts = new HashMap<>();
+
+     public void transfer(String fromId, String toId, double amount) {   @@F2
+         Account from = accounts.get(fromId);
+         Account to = accounts.get(toId);
+         if (from.getBalance() >= amount) {   @@F1
+             from.setBalance(from.getBalance() - amount);   @@F1
+             to.setBalance(to.getBalance() + amount);   @@F1
+         }
+     }
+
+     public void audit(String id) {
+         try {
+             log.write(accounts.get(id).toString());
+         } catch (Exception e) {   @@F3
+         }
+     }
+ }
''')],
    [dict(id="F1", file="src/main/java/bank/AccountService.java", title="Race condition: balance check and update are not atomic", category="bug", severity="high",
          keywords=["race", "thread", "synchron", "atomic", "concurren", "lock", "transaction", "double spend"],
          explanation="Two simultaneous transfers can both pass the balance check and overdraw the account. Make the check-and-update atomic with synchronized, locks, or a database transaction."),
     dict(id="F2", file="src/main/java/bank/AccountService.java", title="No amount validation and double used for money", category="bug", severity="high",
          keywords=["negative", "validat", "bigdecimal", "double", "precision", "amount", "float", "zero"],
          explanation="A negative amount moves money the wrong way, and double causes rounding errors. Reject amounts <= 0, check both accounts exist, and use BigDecimal (or integer cents) for money."),
     dict(id="F3", file="src/main/java/bank/AccountService.java", title="Exception swallowed silently", category="design", severity="medium",
          keywords=["swallow", "empty", "catch", "exception", "log", "ignore", "silent", "handle"],
          explanation="An empty catch hides failures, so audits can fail with no trace. Log the error with context, catch specific exceptions, and rethrow when the caller must know.")])

add("sql-revenue-report", "Monthly revenue report and order archive", "SQL", "Intermediate",
    "Adds the revenue query for finance and archives old orders. Query returns the right numbers on staging.",
    [("reports/monthly_revenue.sql", '''
+ -- Monthly revenue report
+ SELECT *   @@F1
+ FROM orders o
+ JOIN customers c ON c.id = o.customer_id
+ WHERE YEAR(o.created_at) = 2026   @@F2
+   AND o.status = 'paid';
+
+ -- Archive finished orders
+ UPDATE orders SET status = 'archived';   @@F3
''')],
    [dict(id="F1", file="reports/monthly_revenue.sql", title="SELECT * on a join returns ambiguous, unneeded columns", category="design", severity="low",
          keywords=["select *", "star", "columns", "ambiguous", "explicit", "needed", "wildcard", "id"],
          explanation="SELECT * pulls every column from both tables (including duplicate 'id' columns and personal data the report does not need). List the columns you need."),
     dict(id="F2", file="reports/monthly_revenue.sql", title="YEAR() on the column prevents index use", category="performance", severity="medium",
          keywords=["index", "sargable", "function", "range", "full scan", "scan", "between", "year"],
          explanation="Wrapping created_at in YEAR() forces a full table scan. Use a range: created_at >= '2026-01-01' AND created_at < '2027-01-01' so an index can be used."),
     dict(id="F3", file="reports/monthly_revenue.sql", title="UPDATE without WHERE changes every order", category="bug", severity="critical",
          keywords=["where", "every", "all rows", "all orders", "filter", "condition", "dangerous", "whole table"],
          explanation="With no WHERE clause this archives every order, including open and unpaid ones. Add a condition (for example status = 'delivered' AND created_at < ...) and test it in a transaction first.")])

add("py-pagination-cache", "Paginate results with a small cache", "Python", "Advanced",
    "Adds get_page for the list endpoints and caches pages to reduce load. Metrics are best-effort.",
    [("app/pagination.py", '''
+ _cache = {}
+
+ def get_page(items, page, size=10, seen=[]):   @@F1
+     key = (id(items), page)
+     if key in _cache:
+         return _cache[key]
+     start = page * size + 1   @@F3
+     result = items[start:start + size]
+     _cache[key] = result   @@F2
+     seen.append(page)
+     try:
+         save_metrics(page)
+     except:   @@F4
+         pass   @@F4
+     return result
''')],
    [dict(id="F1", file="app/pagination.py", title="Mutable default argument shared between calls", category="bug", severity="medium",
          keywords=["mutable", "default", "shared", "list", "none", "argument", "persist"],
          explanation="seen=[] is created once and shared by every call, so it grows forever and leaks state between requests. Use seen=None and create a new list inside the function."),
     dict(id="F2", file="app/pagination.py", title="Unbounded cache keyed by id() grows and goes stale", category="performance", severity="medium",
          keywords=["unbounded", "memory", "leak", "evict", "lru", "grow", "stale", "id(", "invalidat", "cache"],
          explanation="The cache never evicts, so memory grows without limit, and id(items) can be reused by a different list (wrong data) or be stale when items change. Use functools.lru_cache or a bounded cache with a real key."),
     dict(id="F3", file="app/pagination.py", title="Off-by-one: first item of every page is skipped", category="bug", severity="high",
          keywords=["off-by-one", "off by one", "+ 1", "+1", "skip", "start", "index", "first item", "zero"],
          explanation="With 0-based pages the start index is page * size. The extra +1 skips the first item of every page, so one item per page is never shown."),
     dict(id="F4", file="app/pagination.py", title="Bare except hides every error", category="design", severity="low",
          keywords=["bare", "except", "swallow", "pass", "log", "silent", "specific", "ignore"],
          explanation="A bare except with pass hides real bugs (and even KeyboardInterrupt). Catch the specific exception you expect and log it.")])

add("js-auth-middleware", "Auth middleware and password reset token", "JavaScript", "Advanced",
    "Adds Express auth middleware, a reset-token helper and API-key check for internal services.",
    [("server/auth.js", '''
+ const jwt = require("jsonwebtoken");
+ const crypto = require("crypto");
+
+ function authenticate(req, res, next) {
+   const token = req.headers.authorization.split(" ")[1];
+   req.user = jwt.decode(token);   @@F1
+   next();
+ }
+
+ function createResetToken() {
+   return Math.random().toString(36).slice(2);   @@F2
+ }
+
+ function checkApiKey(provided) {
+   return provided === process.env.API_KEY;   @@F3
+ }
''')],
    [dict(id="F1", file="server/auth.js", title="jwt.decode does not verify the signature", category="security", severity="critical",
          keywords=["verify", "signature", "decode", "forge", "trust", "secret", "unsigned", "fake"],
          explanation="jwt.decode only reads the token; anyone can forge one with any user id. Use jwt.verify(token, secret) and handle errors (also guard against a missing Authorization header)."),
     dict(id="F2", file="server/auth.js", title="Predictable reset token from Math.random", category="security", severity="high",
          keywords=["random", "predict", "crypto", "randombytes", "secure", "guess", "entropy", "math.random"],
          explanation="Math.random is not cryptographically secure, so reset tokens can be guessed, which allows account takeover. Use crypto.randomBytes(32).toString('hex')."),
     dict(id="F3", file="server/auth.js", title="API key compared with === (timing attack)", category="security", severity="medium",
          keywords=["timing", "constant", "timingsafeequal", "compare", "side channel", "===", "equal"],
          explanation="A normal string comparison stops at the first differing character, which can leak the key through response timing. Use crypto.timingSafeEqual on equal-length buffers.")])


def seed_exercises(db: Session) -> None:
    existing = {e for (e,) in db.execute(select(Exercise.id))}
    for ex in EXERCISES:
        if ex["id"] not in existing:
            db.add(Exercise(**ex))
    db.commit()
