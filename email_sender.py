"""
email_sender.py — Resend email delivery for TrelawnyTown.
Sends from noreply@trelawnytown.com once the domain is verified in Resend.
"""

import os
import resend

resend.api_key = os.environ.get("RESEND_API_KEY", "")

FROM_ADDRESS = "TrelawnyTown Society <noreply@trelawnytown.com>"


def send_welcome_email(name: str, email: str, password: str) -> bool:
    """
    Sends a welcome email to a new society member with their login credentials.
    """
    try:
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "reply_to": "dcfarquharson@gmail.com",
            "to": [email],
            "subject": "Welcome to the Trelawny Town Society",
            "html": f"""
            <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto;
                        background: #1a2e1d; color: #e8dfc0; padding: 2.5rem; border-radius: 8px;">

                <div style="text-align:center; margin-bottom:1.5rem;">
                    <h1 style="color:#d4af37; font-size:1.6rem; letter-spacing:2px;
                               text-transform:uppercase; margin:0;">
                        The Trelawny Town Society
                    </h1>
                    <hr style="border:none; border-top:1px solid rgba(212,175,55,0.4); margin:1rem 0;">
                </div>

                <p style="font-size:1.1rem;">Dear <strong style="color:#d4af37;">{name}</strong>,</p>

                <p style="line-height:1.8;">
                    Thank you for joining the Trelawny Town Society. You are now part of a growing
                    community dedicated to preserving and sharing the untold story of the Trelawny Town Maroons.
                </p>

                <p style="line-height:1.8;">Your login credentials are below:</p>

                <div style="background:rgba(0,0,0,0.3); border-left:4px solid #d4af37;
                            padding:1rem 1.5rem; margin:1.5rem 0; border-radius:0 4px 4px 0;">
                    <p style="margin:0.3rem 0;"><strong>Email:</strong> {email}</p>
                    <p style="margin:0.3rem 0;"><strong>Password:</strong>
                        <span style="font-family:monospace; font-size:1.1rem;
                                     color:#d4af37;">{password}</span>
                    </p>
                </div>

                <p style="line-height:1.8; font-size:0.9rem; color:#aaa;">
                    You can change your password at any time from your member profile.
                    Please keep these credentials safe.
                </p>

                <hr style="border:none; border-top:1px solid rgba(212,175,55,0.2); margin:2rem 0;">
                <p style="text-align:center; font-size:0.8rem; color:#777;">
                    &copy; 2026 TrelawnyTown.com &mdash; Dedicated to the Ancestors.
                </p>
            </div>
            """,
        })
        return True
    except Exception as e:
        print(f"[Resend Error] {e}")
        return False
