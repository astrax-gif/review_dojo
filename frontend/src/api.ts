export type Line = { n: number | null; t: "add" | "del" | "ctx"; c: string };
export type FileDiff = { path: string; lines: Line[] };
export type Exercise = {
  id: string; title: string; language: string; difficulty: string; author: string;
  description: string; flaw_count: number; files: FileDiff[]; best: number | null;
  level_required: number; locked: boolean;
};
export type Comment = { file: string; line: number; text: string };
export type Flaw = {
  id: string; file: string; line_start: number; line_end: number; title: string;
  category: string; severity: string; explanation: string;
};
export type Caught = Flaw & { comment: Comment; quality: number };
export type Result = {
  score: number; rank: string; earned: number; max_points: number;
  caught: Caught[]; missed: Flaw[]; false_alarms: Comment[]; tips: string[];
  mentor: string; ai_coach: string | null; saved: boolean;
  xp_gain: number; xp_raw: number; level_up: boolean; progress: Progress; new_achievements: Achievement[];
};
export type Progress = { level: number; title: string; xp: number; xp_in_level: number; xp_needed: number };
export type Achievement = { id: string; name: string; icon: string; desc: string; unlocked: boolean };
export type Stats = {
  username: string; reviews: number; average: number; rank: string;
  progress: Progress; streak: number; best_streak: number; achievements: Achievement[];
  skills: Record<string, { caught: number; total: number }>;
  history: { exercise: string; score: number; xp: number; at: string }[];
};
export type LeaderRow = { username: string; xp: number; level: number; title: string; reviews: number };

const BASE: string = import.meta.env.VITE_API_URL ?? "/api";

export const session = {
  token: () => localStorage.getItem("rd_token"),
  user: () => localStorage.getItem("rd_user"),
  set: (t: string, u: string) => { localStorage.setItem("rd_token", t); localStorage.setItem("rd_user", u); },
  clear: () => { localStorage.removeItem("rd_token"); localStorage.removeItem("rd_user"); },
};

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const t = session.token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(BASE + path, { ...init, headers });
  if (!res.ok) {
    let msg = res.statusText;
    try { const j = await res.json(); msg = typeof j.detail === "string" ? j.detail : "Request failed"; } catch { /* ignore */ }
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  exercises: () => req<Exercise[]>("/exercises"),
  exercise: (id: string) => req<Exercise>(`/exercises/${id}`),
  submit: (id: string, comments: Comment[]) =>
    req<Result>(`/exercises/${id}/submit`, { method: "POST", body: JSON.stringify({ comments, use_ai: true }) }),
  login: (username: string, password: string) =>
    req<{ token: string; username: string }>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  register: (username: string, password: string) =>
    req<{ token: string; username: string }>("/auth/register", { method: "POST", body: JSON.stringify({ username, password }) }),
  stats: () => req<Stats>("/me/stats"),
  leaderboard: () => req<LeaderRow[]>("/leaderboard"),
};
