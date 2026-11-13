<div align="center">

![banner](https://capsule-render.vercel.app/api?type=rect&color=0:000000,100:0a2e0a&height=200&section=header&text=REVIEW_DOJO&fontSize=70&fontColor=00ff41&animation=twinkling&fontAlignY=45&desc=%3E%20train%20your%20code%20review%20skills&descAlignY=68&descSize=20&descColor=00ff41)

[![typing](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=00FF41&background=000000&center=true&vCenter=true&width=700&lines=%3E+scanning+pull+request...;%3E+bug+detected+in+line+9;%3E+security+hole+found;%3E+review+complete.+score%3A+95%25)](https://git.io/typing-svg)

![status](https://img.shields.io/badge/status-live-00ff41?style=for-the-badge&labelColor=000000)
![frontend](https://img.shields.io/badge/frontend-TypeScript%20%2B%20React-00ff41?style=for-the-badge&logo=react&logoColor=00ff41&labelColor=000000)
![backend](https://img.shields.io/badge/backend-FastAPI-00ff41?style=for-the-badge&logo=python&logoColor=00ff41&labelColor=000000)
![db](https://img.shields.io/badge/database-PostgreSQL-00ff41?style=for-the-badge&logo=postgresql&logoColor=00ff41&labelColor=000000)
![host](https://img.shields.io/badge/hosted%20on-Vultr-00ff41?style=for-the-badge&labelColor=000000)

**HackGlobal 2026 entry · Polaris School of Technology × Vultr**

</div>

---

## What is Review Dojo?
A *dojo* is a training hall. **Review Dojo** is a training hall for one of the most important and least taught skills in software: **code review**. You read realistic pull requests with **planted flaws** (bugs, security holes, slow code, messy design), comment on the lines you distrust, and get **scored** against an answer key with a clear explanation of every flaw.

## The problem
- Universities teach writing code, not reading it. Juniors are asked to review code from day one.
- Weak reviews let bugs and vulnerabilities reach production.
- There is no safe, scored place to practise. Existing AI tools review code *for* you; they do not train *you*.

## Features
- 6 realistic pull request exercises: **Python, JavaScript, Java, SQL** (beginner to advanced)
- GitHub-style diff viewer with **inline comments** (hover a line, click `+`)
- **Scoring engine**: severity-weighted, rewards naming the problem, penalises false alarms
- Belt ranks: White, Green, Brown, Black, **Sensei**
- **AI sensei** feedback (optional, Claude API) plus a built-in mentor that works with no key
- Accounts (JWT), **profile with skill bars per category**, global **leaderboard**
- Guests can play without signing up; log in to save scores
- Dockerised, deployable on a Vultr VM in minutes

## Tech stack
| Layer | Technology |
|---|---|
| Frontend | TypeScript, React, Vite |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| Deploy | Docker Compose, nginx, Vultr Cloud Compute |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system design diagram and scoring rules.

## Project structure
```
review_dojo/
├── backend/            # FastAPI app: API, scoring engine, seed exercises
├── frontend/           # React + TypeScript UI
├── docs/               # Architecture, Vultr deploy guide, submission checklist
├── docker-compose.yml  # db + backend + frontend
└── .env.example
```

## Run locally
**Backend** (SQLite is used automatically if no DATABASE_URL is set):
```bash
cd backend
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
**Frontend** (new terminal):
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

## Run everything with Docker
```bash
cp .env.example .env     # edit the passwords
docker compose up -d --build
# open http://localhost
```

## Deploy on Vultr
Step-by-step guide: [docs/DEPLOY_VULTR.md](docs/DEPLOY_VULTR.md)

## Roadmap
Teacher dashboards to assign exercises to a class · more languages · community-submitted pull requests · GitHub import.

## License
All Rights Reserved. Public for viewing and hackathon judging only. See [LICENSE](LICENSE).

## Author
Built by a software engineering student at the University of Europe for Applied Sciences.

![footer](https://capsule-render.vercel.app/api?type=rect&color=0:0a2e0a,100:000000&height=100&section=footer)
