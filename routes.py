"""
routes.py — All TrelawnyTown API endpoints.

POST /api/trelawny/join_waitlist   → register, save to DB, email password
POST /api/trelawny/login           → verify email + password
POST /api/trelawny/change_password → update password
"""

import secrets
import string
import bcrypt

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from db import get_conn
from email_sender import send_welcome_email

router = APIRouter()


# ── Request models ──────────────────────────────────────────────────────────

class JoinRequest(BaseModel):
    name: str
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str


# ── Helpers ─────────────────────────────────────────────────────────────────

def generate_password(length: int = 10) -> str:
    """Generate a readable random password (no ambiguous chars)."""
    alphabet = string.ascii_letters + string.digits
    # Remove visually ambiguous characters
    alphabet = alphabet.translate(str.maketrans("", "", "0OIl1"))
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/join_waitlist")
def join_waitlist(payload: JoinRequest):
    name  = payload.name.strip()
    email = payload.email.strip().lower()

    if not name:
        return {"status": "error", "message": "Please enter your name."}

    conn = get_conn()
    cur  = conn.cursor()

    # Check for existing member
    cur.execute("SELECT id FROM society_members WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close(); conn.close()
        return {"status": "error", "message": "This email is already registered."}

    # Generate and hash password
    plain_password = generate_password()
    hashed         = hash_password(plain_password)

    # Save to DB
    cur.execute(
        "INSERT INTO society_members (name, email, password) VALUES (%s, %s, %s)",
        (name, email, hashed)
    )
    conn.commit()
    cur.close(); conn.close()

    # Send welcome email with password
    sent = send_welcome_email(name, email, plain_password)

    if sent:
        return {
            "status": "ok",
            "message": f"Welcome, {name}! Check your email for your login password."
        }
    else:
        return {
            "status": "ok",
            "message": "Registered! However, the confirmation email could not be sent. "
                       "Please contact us at contact@trelawnytown.com."
        }


@router.post("/login")
def login(payload: LoginRequest):
    email    = payload.email.strip().lower()
    password = payload.password.strip()

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id, name, password FROM society_members WHERE email = %s",
        (email,)
    )
    member = cur.fetchone()
    cur.close(); conn.close()

    if not member:
        return {"status": "error", "message": "Email not found."}

    if not verify_password(password, member["password"]):
        return {"status": "error", "message": "Incorrect password."}

    return {
        "status": "ok",
        "message": "Login successful.",
        "name": member["name"],
        "member_id": member["id"]
    }


@router.post("/change_password")
def change_password(payload: ChangePasswordRequest):
    email            = payload.email.strip().lower()
    current_password = payload.current_password.strip()
    new_password     = payload.new_password.strip()

    if len(new_password) < 6:
        return {"status": "error", "message": "New password must be at least 6 characters."}

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "SELECT id, password FROM society_members WHERE email = %s",
        (email,)
    )
    member = cur.fetchone()

    if not member:
        cur.close(); conn.close()
        return {"status": "error", "message": "Email not found."}

    if not verify_password(current_password, member["password"]):
        cur.close(); conn.close()
        return {"status": "error", "message": "Current password is incorrect."}

    new_hash = hash_password(new_password)
    cur.execute(
        "UPDATE society_members SET password = %s WHERE email = %s",
        (new_hash, email)
    )
    conn.commit()
    cur.close(); conn.close()

    return {"status": "ok", "message": "Password updated successfully."}
