# Avenqor Technologies — Website

A premium marketing website for Avenqor Technologies — **plain HTML, CSS,
and JavaScript** on the frontend (no build tools, no npm needed to view
it), with a Python (FastAPI) + MySQL backend for the contact form.

## Project structure

```
avenqor-html/
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## How it works

The Python backend serves the frontend folder directly AND answers the
contact form's API calls — one process, one command, no separate frontend
server and no build step:

```
uvicorn main:app  →  http://localhost:8000
                       ├── /              → frontend/index.html
                       ├── /css/style.css → frontend/css/style.css
                       ├── /js/main.js    → frontend/js/main.js
                       └── /api/contact   → FastAPI + MySQL
```

## 1. Set up MySQL

You need a MySQL server running (MySQL Workbench, XAMPP, or MySQL
Community Server all work — whatever you already have).

The backend auto-creates the `avenqor` database and its `inquiries` table
on first run, as long as the MySQL user has permission to create
databases. If you'd rather create it yourself first:

```sql
CREATE DATABASE avenqor CHARACTER SET utf8mb4;
```

## 2. Configure the backend

```bash
cd backend
pip install -r requirements.txt      # add --break-system-packages on some systems
copy .env.example .env               # Windows — use `cp` on Mac/Linux
```

Open `.env` and fill in your real MySQL credentials:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password-here
MYSQL_DATABASE=avenqor
```

(If your MySQL root user has no password, as is common on a fresh local
install, just leave `MYSQL_PASSWORD=` empty.)

## 3. Run everything

```bash
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** — that's the entire website. Submit the
contact form to confirm it reaches MySQL: check with

```sql
USE avenqor;
SELECT * FROM inquiries ORDER BY id DESC;
```

...in MySQL Workbench, phpMyAdmin, or the `mysql` CLI.

## Editing the site

Because there's no build step, changes are instant:

- Edit `frontend/index.html`, `frontend/css/style.css`, or
  `frontend/js/main.js`.
- Refresh `http://localhost:8000` in your browser (hard refresh —
  Ctrl+Shift+R / Cmd+Shift+R — if you don't see the change, in case the
  browser cached the old CSS/JS file).
- The backend does **not** need to be restarted for frontend edits — only
  restart it if you change `backend/main.py` itself (or just leave
  `--reload` on, which restarts it automatically).

## Optional: email notifications

Leave `SMTP_HOST` etc. blank in `.env` and submissions are still saved to
MySQL — you just won't get an email alert. To enable it, fill in:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=you@yourdomain.com
SMTP_PASS=your-smtp-password
NOTIFY_EMAIL=you@yourdomain.com
```

## Optional: viewing submissions via the API

Set `ADMIN_TOKEN` in `.env` to any value, restart the backend, then call:

```
GET http://localhost:8000/api/inquiries
Header: X-Admin-Token: <your token>
```

(Needs a tool like Postman or `curl` — a plain browser address bar can't
send custom headers.)

## Before going live

- **Contact details** — `frontend/index.html`'s Contact section has
  placeholder email, location, and LinkedIn URL in square brackets.
  Search for `[add-your-email` and replace them.
- **Company facts** — no founding year, employee count, client list, or
  certifications are claimed anywhere. Add these once you have real
  information to back them up.
- **Deploy** — the `frontend/` folder is plain static files (deployable
  anywhere), and `backend/` is a standard FastAPI app (deployable to
  Render, Railway, a VPS, etc.). You'll need a reachable MySQL server in
  production too — a managed option (PlanetScale, AWS RDS, Railway's
  MySQL add-on) is usually easiest.

## Notes on the Infrastructure AI content

All infrastructure-inspection figures (issue counts, section IDs, dates)
shown on the site are illustrative sample data, not real inspection
results. The copy is written to position Avenqor Infra as an AI-assisted
decision-support tool — not a replacement for professional engineering
judgment or a certification of structural safety. Keep that framing if
you extend this content.
