import { useEffect, useRef, useState } from "react";
import { api, session } from "./api";
import type { Comment, Exercise, LeaderRow, Progress, Result, Stats } from "./api";

function useHash(): [string, (h: string) => void] {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const on = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return [hash, (h) => { window.location.hash = h; }];
}

function MatrixBg() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current!;
    const ctx = cv.getContext("2d")!;
    let w = (cv.width = window.innerWidth);
    let h = (cv.height = window.innerHeight);
    const cols = Math.floor(w / 18);
    const drops = Array.from({ length: cols }, () => Math.random() * h / 18);
    const chars = "01{}[]<>/=+;$#review";
    const id = setInterval(() => {
      ctx.fillStyle = "rgba(0,0,0,0.08)";
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = "#00ff41";
      ctx.font = "14px monospace";
      drops.forEach((y, i) => {
        ctx.fillText(chars[Math.floor(Math.random() * chars.length)], i * 18, y * 18);
        drops[i] = y * 18 > h && Math.random() > 0.975 ? 0 : y + 1;
      });
    }, 70);
    const onResize = () => { w = cv.width = window.innerWidth; h = cv.height = window.innerHeight; };
    window.addEventListener("resize", onResize);
    return () => { clearInterval(id); window.removeEventListener("resize", onResize); };
  }, []);
  return <canvas ref={ref} className="matrix" />;
}

const BOOT = [
  "[ OK ] mounting /dev/dojo ...",
  "[ OK ] loading flaw database ... 18 vulnerabilities armed",
  "[ OK ] starting scoring engine ...",
  "[ OK ] connecting to vultr-node ... secure",
  "> WELCOME, HACKER. RUN CODE REVIEW. EARN XP. LEVEL UP.",
];

function Boot({ onDone }: { onDone: () => void }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (n >= BOOT.length) { const t = setTimeout(onDone, 500); return () => clearTimeout(t); }
    const t = setTimeout(() => setN(n + 1), 420);
    return () => clearTimeout(t);
  }, [n, onDone]);
  return (
    <div className="boot" onClick={onDone}>
      <pre>{BOOT.slice(0, n).join("\n")}<span className="cursor">█</span></pre>
      <small>click to skip</small>
    </div>
  );
}

function Typewriter({ lines }: { lines: string[] }) {
  const [i, setI] = useState(0);
  const [txt, setTxt] = useState("");
  const [del, setDel] = useState(false);
  useEffect(() => {
    const full = lines[i % lines.length];
    const t = setTimeout(() => {
      if (!del) { setTxt(full.slice(0, txt.length + 1)); if (txt.length + 1 === full.length) setTimeout(() => setDel(true), 1200); }
      else { setTxt(full.slice(0, txt.length - 1)); if (txt.length - 1 === 0) { setDel(false); setI(i + 1); } }
    }, del ? 25 : 55);
    return () => clearTimeout(t);
  }, [txt, del, i, lines]);
  return <p className="typer">{"> "}{txt}<span className="cursor">█</span></p>;
}

function XpBar({ p, big }: { p: Progress; big?: boolean }) {
  const pct = Math.min(100, Math.round((100 * p.xp_in_level) / p.xp_needed));
  return (
    <div className={big ? "xpbar big" : "xpbar"}>
      <div className="xp-top"><b>LVL {p.level}</b><span>{p.title}</span><span className="dim">{p.xp_in_level}/{p.xp_needed} XP</span></div>
      <div className="xp-track"><i style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

function Header({ nav, hash, user, onLogout, prog }: { nav: (h: string) => void; hash: string; user: string | null; onLogout: () => void; prog: Progress | null }) {
  const link = (h: string, label: string) => (
    <a href={h} className={hash === h ? "active" : ""} onClick={(e) => { e.preventDefault(); nav(h); }}>{label}</a>
  );
  return (
    <header className="top">
      <a href="#/" className="logo" onClick={(e) => { e.preventDefault(); nav("#/"); }}>
        <span>&gt;_</span> REVIEW_DOJO
      </a>
      {user && prog && <div className="hud"><XpBar p={prog} /></div>}
      <nav>
        {link("#/", "dojo")}
        {link("#/leaderboard", "leaderboard")}
        {user && link("#/profile", "profile")}
        {user ? <button className="ghost" onClick={onLogout}>logout [{user}]</button> : link("#/login", "login")}
      </nav>
    </header>
  );
}

function Home({ nav, prog, user }: { nav: (h: string) => void; prog: Progress | null; user: string | null }) {
  const [list, setList] = useState<Exercise[] | null>(null);
  const [lang, setLang] = useState("All");
  const [err, setErr] = useState("");
  useEffect(() => { api.exercises().then(setList).catch((e) => setErr(e.message)); }, []);
  const langs = ["All", ...Array.from(new Set((list ?? []).map((e) => e.language)))];
  const shown = (list ?? []).filter((e) => lang === "All" || e.language === lang);
  return (
    <>
      <section className="hero">
        <h1 className="glitch">Find the bug before it ships.</h1>
        <Typewriter lines={["scanning pull request...", "bug detected in line 9", "security hole found", "review complete. +120 XP. LEVEL UP!"]} />
        <p>Review realistic pull requests with planted flaws. Comment on the lines you distrust, get scored, earn XP and level up.</p>
        <div className="steps">
          <span>1 pick a PR</span><span>2 click a line to comment</span><span>3 submit &amp; get scored</span>
        </div>
      </section>
      {user && prog ? (
        <div className="player"><div className="avatar">{prog.level}</div><div style={{ flex: 1 }}><XpBar p={prog} big /></div></div>
      ) : (
        <div className="player guest"><span>👾 Guest mode: you start at LVL 1. <a href="#/login">Register</a> to earn XP, unlock harder missions and join the leaderboard.</span></div>
      )}
      <div className="filters">
        {langs.map((l) => (<button key={l} className={l === lang ? "chip on" : "chip"} onClick={() => setLang(l)}>{l}</button>))}
      </div>
      {err && <p className="error">Cannot reach API: {err}</p>}
      {!list && !err && <p className="dim">loading exercises...</p>}
      <div className="grid">
        {shown.map((e) => (
          <article key={e.id} className={e.locked ? "card locked" : "card"} onClick={() => !e.locked && nav(`#/exercise/${e.id}`)}>
            {e.locked && <div className="lock">🔒 REQUIRES LVL {e.level_required}</div>}
            <div className="row"><span className="lang">{e.language}</span><span className={`diff ${e.difficulty.toLowerCase()}`}>{e.difficulty}</span></div>
            <h3>{e.title}</h3>
            <p className="dim">{e.description}</p>
            <div className="row"><span className="dim">{e.flaw_count} hidden flaws</span>
              <span>{e.best !== null ? `best ${e.best}/100` : "not attempted"}</span></div>
          </article>
        ))}
      </div>
    </>
  );
}

function ExercisePage({ id, onProgress }: { id: string; onProgress: () => void }) {
  const [ex, setEx] = useState<Exercise | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [open, setOpen] = useState<{ file: string; line: number } | null>(null);
  const [draft, setDraft] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    setEx(null); setResult(null); setComments([]);
    api.exercise(id).then(setEx).catch((e) => setErr(e.message));
  }, [id]);

  if (!ex && err) return <p className="error">{err}</p>;
  if (!ex) return <p className="dim">loading pull request...</p>;
  if (ex.locked) return <p className="error">🔒 Locked. Reach level {ex.level_required} to open this pull request. <a href="#/">Back to the dojo</a></p>;

  const mark = new Map<string, "caught" | "missed">();
  result?.caught.forEach((f) => { for (let n = f.line_start; n <= f.line_end; n++) mark.set(`${f.file}:${n}`, "caught"); });
  result?.missed.forEach((f) => { for (let n = f.line_start; n <= f.line_end; n++) mark.set(`${f.file}:${n}`, "missed"); });

  const addComment = () => {
    if (!open || !draft.trim()) return;
    setComments([...comments, { file: open.file, line: open.line, text: draft.trim() }]);
    setDraft(""); setOpen(null);
  };
  const submit = async () => {
    setBusy(true); setErr("");
    try { const r = await api.submit(ex.id, comments); setResult(r); onProgress(); window.scrollTo({ top: 0, behavior: "smooth" }); }
    catch (e) { setErr((e as Error).message); }
    setBusy(false);
  };
  const reset = () => { setResult(null); setComments([]); setOpen(null); };

  return (
    <>
      <div className="pr-head">
        <div className="row"><span className="lang">{ex.language}</span><span className={`diff ${ex.difficulty.toLowerCase()}`}>{ex.difficulty}</span></div>
        <h2>{ex.title} <span className="dim">#{ex.id}</span></h2>
        <p className="dim">opened by <b>{ex.author}</b> · {ex.flaw_count} hidden flaws</p>
        <p>{ex.description}</p>
      </div>

      {result && <ResultPanel r={result} onRetry={reset} />}

      {ex.files.map((f) => (
        <div key={f.path} className="file">
          <div className="file-name">{f.path}</div>
          <table className="code"><tbody>
            {f.lines.map((l, i) => {
              const key = `${f.path}:${l.n}`;
              const m = l.n !== null ? mark.get(key) : undefined;
              const lineComments = comments.filter((c) => c.file === f.path && c.line === l.n);
              const isOpen = open && open.file === f.path && open.line === l.n;
              return (
                <FragmentRows key={i}>
                  <tr className={`${l.t} ${m ?? ""}`}>
                    <td className="gutter">
                      {l.n !== null && !result && (
                        <button className="plus" title="Add comment" onClick={() => { setOpen({ file: f.path, line: l.n! }); setDraft(""); }}>+</button>
                      )}
                    </td>
                    <td className="ln">{l.n ?? ""}</td>
                    <td className="sign">{l.t === "add" ? "+" : l.t === "del" ? "-" : ""}</td>
                    <td className="src"><pre>{l.c}</pre></td>
                  </tr>
                  {lineComments.map((c, j) => (
                    <tr key={`c${j}`} className="cmt"><td colSpan={4}>
                      <div className="bubble">💬 {c.text}
                        {!result && <button className="ghost" onClick={() => setComments(comments.filter((x) => x !== c))}>delete</button>}
                      </div></td></tr>
                  ))}
                  {isOpen && (
                    <tr className="cmt"><td colSpan={4}>
                      <div className="editor">
                        <textarea autoFocus value={draft} onChange={(e) => setDraft(e.target.value)}
                          placeholder={`Comment on line ${l.n}: what is wrong, and why does it matter?`} />
                        <div className="row"><button onClick={addComment}>add comment</button>
                          <button className="ghost" onClick={() => setOpen(null)}>cancel</button></div>
                      </div></td></tr>
                  )}
                </FragmentRows>
              );
            })}
          </tbody></table>
        </div>
      ))}

      {err && <p className="error">{err}</p>}
      {!result && (
        <div className="submit-bar">
          <span>{comments.length} comment{comments.length === 1 ? "" : "s"}</span>
          <button disabled={busy || comments.length === 0} onClick={submit}>{busy ? "scoring..." : "submit review"}</button>
        </div>
      )}
    </>
  );
}

function FragmentRows({ children }: { children: React.ReactNode }) { return <>{children}</>; }

function ResultPanel({ r, onRetry }: { r: Result; onRetry: () => void }) {
  return (
    <section className="result">
      {r.score >= 90 && <div className="hacked">ACCESS GRANTED</div>}
      {r.level_up && <div className="levelup">⚡ LEVEL UP! You are now LVL {r.progress.level}: {r.progress.title}</div>}
      <div className="score-row">
        <div className="ring" style={{ "--p": r.score } as React.CSSProperties}><b>{r.score}</b><small>/100</small></div>
        <div>
          <h2>{r.rank}</h2>
          <p>{r.mentor}</p>
          {!r.saved && <p className="dim">Log in to save this score to your profile and the leaderboard.</p>}
        </div>
      </div>
      {r.saved ? (
        <div className="xpgain"><b>+{r.xp_gain} XP</b>{r.xp_gain === 0 && <span className="dim"> (beat your best on this PR to earn more)</span>}<XpBar p={r.progress} /></div>
      ) : null}
      {r.new_achievements.map((a) => (<div key={a.id} className="ach-pop">{a.icon} Achievement unlocked: <b>{a.name}</b> <span className="dim">{a.desc}</span></div>))}
      {r.ai_coach && <div className="ai"><b>AI sensei:</b> {r.ai_coach}</div>}
      {r.caught.length > 0 && <h3 className="good">✔ Caught ({r.caught.length})</h3>}
      {r.caught.map((f) => (
        <div key={f.id} className="flaw good">
          <b>{f.title}</b> <span className={`sev ${f.severity}`}>{f.severity}</span> <span className="dim">{f.category} · line {f.line_start}</span>
          <p>{f.explanation}</p>
        </div>
      ))}
      {r.missed.length > 0 && <h3 className="bad">✘ Missed ({r.missed.length})</h3>}
      {r.missed.map((f) => (
        <div key={f.id} className="flaw bad">
          <b>{f.title}</b> <span className={`sev ${f.severity}`}>{f.severity}</span> <span className="dim">{f.category} · line {f.line_start}</span>
          <p>{f.explanation}</p>
        </div>
      ))}
      {r.false_alarms.length > 0 && <h3 className="warn">⚠ Comments on fine lines ({r.false_alarms.length})</h3>}
      {r.false_alarms.map((c, i) => (<div key={i} className="flaw warn">line {c.line}: {c.text}</div>))}
      {r.tips.length > 0 && <><h3>Feedback tips</h3><ul>{r.tips.map((t, i) => <li key={i}>{t}</li>)}</ul></>}
      <button onClick={onRetry}>try again</button>
    </section>
  );
}

function Leaderboard() {
  const [rows, setRows] = useState<LeaderRow[] | null>(null);
  useEffect(() => { api.leaderboard().then(setRows).catch(() => setRows([])); }, []);
  return (
    <>
      <h2>// leaderboard</h2>
      {!rows && <p className="dim">loading...</p>}
      {rows && rows.length === 0 && <p className="dim">No ranked reviewers yet. Log in and be the first.</p>}
      <table className="board"><tbody>
        {rows?.map((r, i) => (<tr key={r.username}><td>#{i + 1}</td><td>{r.username}</td><td>LVL {r.level} <span className="dim">{r.title}</span></td><td>{r.reviews} reviews</td><td><b>{r.xp}</b> XP</td></tr>))}
      </tbody></table>
    </>
  );
}

function Profile() {
  const [s, setS] = useState<Stats | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.stats().then(setS).catch((e) => setErr(e.message)); }, []);
  if (err) return <p className="error">{err}</p>;
  if (!s) return <p className="dim">loading...</p>;
  return (
    <>
      <h2>// {s.username}</h2>
      <div className="player"><div className="avatar">{s.progress.level}</div><div style={{ flex: 1 }}><XpBar p={s.progress} big /></div></div>
      <div className="stats">
        <div><b>{s.rank}</b><small>belt</small></div>
        <div><b>{s.reviews}</b><small>reviews</small></div>
        <div><b>{s.average}</b><small>avg score</small></div>
        <div><b>{s.progress.xp}</b><small>total XP</small></div>
        <div><b>🔥 {s.streak}</b><small>day streak (best {s.best_streak})</small></div>
      </div>
      <h3>Achievements ({s.achievements.filter((a) => a.unlocked).length}/{s.achievements.length})</h3>
      <div className="ach-grid">
        {s.achievements.map((a) => (
          <div key={a.id} className={a.unlocked ? "ach on" : "ach"} title={a.desc}>
            <span>{a.unlocked ? a.icon : "🔒"}</span><b>{a.name}</b><small>{a.desc}</small>
          </div>
        ))}
      </div>
      <h3>Review skill by category</h3>
      {Object.keys(s.skills).length === 0 && <p className="dim">Submit a review to see your strengths and weak spots.</p>}
      {Object.entries(s.skills).map(([k, v]) => {
        const pct = Math.round((100 * v.caught) / v.total);
        return (<div key={k} className="bar"><span>{k}</span><div><i style={{ width: `${pct}%` }} /></div><span>{pct}%</span></div>);
      })}
      <h3>Recent missions</h3>
      <table className="board"><tbody>
        {s.history.map((h, i) => (<tr key={i}><td>{h.exercise}</td><td><b>{h.score}</b>/100</td><td>+{h.xp} XP</td><td className="dim">{new Date(h.at).toLocaleString()}</td></tr>))}
      </tbody></table>
    </>
  );
}

function Login({ onAuth }: { onAuth: (u: string) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");
  const go = async () => {
    setErr("");
    try {
      const r = await (mode === "login" ? api.login(u, p) : api.register(u, p));
      session.set(r.token, r.username); onAuth(r.username);
    } catch (e) { setErr((e as Error).message); }
  };
  return (
    <div className="auth">
      <h2>// {mode}</h2>
      <input placeholder="username" value={u} onChange={(e) => setU(e.target.value)} />
      <input placeholder="password (6+ chars)" type="password" value={p} onChange={(e) => setP(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && go()} />
      {err && <p className="error">{err}</p>}
      <button onClick={go}>{mode}</button>
      <button className="ghost" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "need an account? register" : "have an account? login"}
      </button>
    </div>
  );
}

export default function App() {
  const [hash, nav] = useHash();
  const [user, setUser] = useState<string | null>(session.user());
  const [prog, setProg] = useState<Progress | null>(null);
  const [booted, setBooted] = useState(sessionStorage.getItem("rd_boot") === "1");
  const refresh = () => { if (session.token()) api.stats().then((s) => setProg(s.progress)).catch(() => {}); };
  useEffect(() => { if (user) refresh(); else setProg(null); }, [user]);
  const logout = () => { session.clear(); setUser(null); nav("#/"); };
  const done = () => { sessionStorage.setItem("rd_boot", "1"); setBooted(true); };
  if (!booted) return <Boot onDone={done} />;
  let page: React.ReactNode;
  if (hash.startsWith("#/exercise/")) page = <ExercisePage id={hash.slice("#/exercise/".length)} onProgress={refresh} />;
  else if (hash === "#/leaderboard") page = <Leaderboard />;
  else if (hash === "#/profile") page = user ? <Profile /> : <Login onAuth={(u) => { setUser(u); nav("#/profile"); }} />;
  else if (hash === "#/login") page = <Login onAuth={(u) => { setUser(u); nav("#/"); }} />;
  else page = <Home nav={nav} prog={prog} user={user} />;
  return (
    <>
      <MatrixBg />
      <div className="crt" />
      <Header nav={nav} hash={hash} user={user} onLogout={logout} prog={prog} />
      <main>{page}</main>
      <footer>Review Dojo · HackGlobal 2026 · powered by Vultr</footer>
    </>
  );
}
