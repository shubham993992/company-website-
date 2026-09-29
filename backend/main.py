"""
Avenqor Technologies — backend.

Serves the plain HTML/CSS/JS website in ../frontend AND the contact-form
API from a single process — just run:

    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

then open http://localhost:8000 — that's the whole site, no separate
frontend server or build step needed.
"""

import os
import smtplib
from contextlib import contextmanager
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

# --- MySQL connection settings -----------------------------------------
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "avenqor")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")  # set this to protect GET /api/inquiries

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")  # where inquiry notifications are sent

app = FastAPI(title="Avenqor Technologies — API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _connect(with_database: bool = True):
    kwargs = dict(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
    if with_database:
        kwargs["database"] = DB_NAME
    return mysql.connector.connect(**kwargs)


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the database (if missing) and the inquiries table."""
    conn = _connect(with_database=False)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4")
    cursor.close()
    conn.close()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inquiries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_at VARCHAR(64) NOT NULL,
                name VARCHAR(200) NOT NULL,
                organization VARCHAR(200),
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(40),
                interest VARCHAR(100) NOT NULL,
                need VARCHAR(300),
                message TEXT NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.close()


init_db()


class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    organization: str | None = Field(default=None, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    interest: str = Field(min_length=1, max_length=100)
    need: str | None = Field(default=None, max_length=300)
    message: str = Field(min_length=1, max_length=5000)


class ContactOut(BaseModel):
    id: int
    created_at: str


def send_email_notification(entry: dict) -> None:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and NOTIFY_EMAIL):
        return  # email notifications not configured — skip silently

    body = (
        f"New inquiry from the Avenqor Technologies website\n\n"
        f"Name: {entry['name']}\n"
        f"Organization: {entry.get('organization') or '-'}\n"
        f"Email: {entry['email']}\n"
        f"Phone: {entry.get('phone') or '-'}\n"
        f"Interested in: {entry['interest']}\n"
        f"Needs help with: {entry.get('need') or '-'}\n\n"
        f"Message:\n{entry['message']}\n"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"New Avenqor inquiry from {entry['name']}"
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/contact", response_model=ContactOut)
def submit_contact(payload: ContactIn):
    created_at = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO inquiries
                (created_at, name, organization, email, phone, interest, need, message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                created_at,
                payload.name,
                payload.organization,
                payload.email,
                payload.phone,
                payload.interest,
                payload.need,
                payload.message,
            ),
        )
        new_id = cursor.lastrowid
        cursor.close()

    try:
        send_email_notification(payload.model_dump())
    except Exception:
        # Don't fail the request if email sending fails — the submission
        # is already safely stored in the database.
        pass

    return ContactOut(id=new_id, created_at=created_at)


@app.get("/api/inquiries")
def list_inquiries(x_admin_token: str | None = Header(default=None)):
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin access not configured (set ADMIN_TOKEN).")
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token.")

    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inquiries ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        return rows


# ---------------------------------------------------------------------------
# Serve the plain HTML/CSS/JS frontend from ../frontend.
#
# Mounted last (after all /api/* routes above) so it never shadows them.
# html=True makes it serve frontend/index.html at "/" automatically.
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
