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


# ── Manifestations & Encouragements ──────────────────────────────────────────

class ManifestationRequest(BaseModel):
    email: str
    date: str
    gratitude_1: str = None
    gratitude_2: str = None
    gratitude_3: str = None
    gratitude_done: bool = None
    morning_vis: str = None
    vis_done: bool = None
    inspired_action: str = None
    action_taken: bool = None
    evening_vis: str = None
    evening_done: bool = None
    encouragement_received: bool = None

@router.get("/manifest/get")
def get_manifest(email: str, date: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM daily_manifestations WHERE email = %s AND date = %s", (email, date))
        row = cur.fetchone()
        if row:
            return {"status": "ok", "data": dict(row)}
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "message": "Database error"}
    finally:
        cur.close()
        conn.close()

@router.post("/manifest/save")
def save_manifest(payload: ManifestationRequest):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Dictionary of fields to update
        data = payload.dict(exclude_unset=True)
        email = data.pop("email")
        date = data.pop("date")

        cur.execute("SELECT email FROM daily_manifestations WHERE email = %s AND date = %s", (email, date))
        exists = cur.fetchone()

        if not exists:
            cur.execute("INSERT INTO daily_manifestations (email, date) VALUES (%s, %s)", (email, date))

        if data:
            set_clause = ", ".join(f"{k} = %s" for k in data.keys())
            values = list(data.values())
            values.extend([email, date])
            cur.execute(f"UPDATE daily_manifestations SET {set_clause} WHERE email = %s AND date = %s", values)

        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": "Failed to save data"}
    finally:
        cur.close()
        conn.close()

@router.get("/encouragement/daily")
def get_daily_encouragement(date: str):
    word = "Every step you take is a step toward your manifestation."
    try:
        import hashlib
        words = [
            "Your focus creates your reality. Stay focused on 1604.",
            "Every step you take is a step toward your manifestation.",
            "The universe is conspiring in your favor today.",
            "You are the master of your fate and the captain of your soul.",
            "Manifestation is the art of believing it into existence.",
            "Your gratitude is the magnet for all your desires.",
            "Rest in the knowing that it is already done.",
            "Success is a state of mind. Adopt the mind of a winner.",
            "You are worthy of all the abundance flowing to you.",
            "Today is a perfect day to align with your highest self.",
            "Confidence is the cornerstone of your success.",
            "Believe in the power of your vision.",
            "Your dreams are valid and achievable.",
            "Abundance is your birthright.",
            "Stay true to your path and the results will follow.",
            "Persistence is the key to manifesting your goals.",
            "Your thoughts are the seeds of your future.",
            "Embrace the journey with an open heart.",
            "You have everything you need within you.",
            "Consistency in your practice leads to mastery.",
            "The light within you shines brightly today.",
            "Affirm your goals with conviction.",
            "Your energy attracts your experiences.",
            "Be intentional in everything you do.",
            "Your potential is limitless.",
            "Find joy in the present moment.",
            "Trust the process of life.",
            "You are powerful beyond measure.",
            "Radiate positivity and watch the world respond.",
            "Your vision is becoming clearer every day.",
            "Stay patient and stay focused.",
            "Great things take time and dedication.",
            "Celebrate every victory, no matter how small.",
            "You are a magnet for miracles.",
            "Harmonize with the rhythm of the universe.",
            "Peace and prosperity are yours today.",
            "Your dedication is inspiring.",
            "Keep moving forward with grace.",
        ]
        idx = int(hashlib.md5(date.encode()).hexdigest(), 16) % len(words)
        word = words[idx]
    except Exception:
        pass
    
    return {"status": "ok", "word": word}
