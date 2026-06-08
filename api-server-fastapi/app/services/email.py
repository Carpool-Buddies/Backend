"""
Transactional email via Resend.
All functions are fire-and-forget — they log on error but never raise,
so a broken email config can't break the main request flow.
Key is read lazily so tests that don't set RESEND_API_KEY just skip silently.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _send(*, to: str, subject: str, html: str) -> None:
    try:
        from app.core.config import get_settings
        settings = get_settings()
        if not settings.RESEND_API_KEY:
            logger.debug("RESEND_API_KEY not configured — skipping email to %s", to)
            return
        import resend  # type: ignore[import]
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": f"CarpoolBuddies <{settings.EMAIL_FROM}>",
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info("Email sent to %s: %s", to, subject)
    except Exception as exc:
        logger.warning("Failed to send email to %s (%s): %s", to, subject, exc)


# ── Templates ────────────────────────────────────────────────────────────────

def _base(content: str) -> str:
    return f"""
    <div dir="rtl" style="font-family:Arial,Helvetica,sans-serif;max-width:520px;
         margin:auto;background:#0F172A;color:#e2e8f0;padding:32px;border-radius:16px">
      <h2 style="color:#14B8A6;margin-top:0">🚗 CarpoolBuddies</h2>
      {content}
      <hr style="border:none;border-top:1px solid #334155;margin:24px 0"/>
      <p style="color:#64748b;font-size:12px">
        קיבלת מייל זה כי אתה/את רשום/ה ל-CarpoolBuddies.
      </p>
    </div>
    """


def send_request_received(
    driver_email: str, driver_name: str, passenger_name: str, destination: str
) -> None:
    _send(
        to=driver_email,
        subject=f"בקשת הצטרפות חדשה — {destination}",
        html=_base(f"""
          <p>שלום {driver_name},</p>
          <p>
            <strong style="color:#f8fafc">{passenger_name}</strong>
            ביקש/ה להצטרף לנסיעה שלך ל<strong style="color:#14B8A6">{destination}</strong>.
          </p>
          <p>היכנס/י לאפליקציה כדי לאשר או לדחות את הבקשה.</p>
        """),
    )


def send_request_accepted(
    passenger_email: str, passenger_name: str, destination: str, driver_name: str
) -> None:
    _send(
        to=passenger_email,
        subject=f"הבקשה אושרה! 🎉 — {destination}",
        html=_base(f"""
          <p>שלום {passenger_name},</p>
          <p>
            <strong style="color:#f8fafc">{driver_name}</strong>
            אישר/ה את הצטרפותך לנסיעה ל<strong style="color:#14B8A6">{destination}</strong>.
          </p>
          <p style="font-size:24px">נסיעה טובה! 🙌</p>
        """),
    )


def send_request_rejected(
    passenger_email: str, passenger_name: str, destination: str
) -> None:
    _send(
        to=passenger_email,
        subject=f"עדכון על בקשתך — {destination}",
        html=_base(f"""
          <p>שלום {passenger_name},</p>
          <p>
            לצערנו, בקשתך להצטרף לנסיעה
            ל<strong style="color:#14B8A6">{destination}</strong> לא אושרה.
          </p>
          <p>אל תתייאש/י — יש עוד נסיעות זמינות! 🚕</p>
        """),
    )


def send_ride_cancelled(
    passenger_email: str, passenger_name: str, destination: str, driver_name: str
) -> None:
    _send(
        to=passenger_email,
        subject=f"הנסיעה בוטלה — {destination}",
        html=_base(f"""
          <p>שלום {passenger_name},</p>
          <p>
            הנסיעה עם <strong style="color:#f8fafc">{driver_name}</strong>
            ל<strong style="color:#14B8A6">{destination}</strong> בוטלה.
          </p>
          <p>חפש/י נסיעה חלופית באפליקציה.</p>
        """),
    )


def send_ride_completed(
    passenger_email: str, passenger_name: str, destination: str
) -> None:
    _send(
        to=passenger_email,
        subject=f"הנסיעה הושלמה — דרגו את הנהג! ⭐",
        html=_base(f"""
          <p>שלום {passenger_name},</p>
          <p>
            הנסיעה ל<strong style="color:#14B8A6">{destination}</strong>
            הושלמה בהצלחה!
          </p>
          <p>קח/י רגע לדרג את הנהג — זה עוזר לכולם לדעת עם מי לנסוע. ⭐</p>
        """),
    )


def send_ride_updated(
    passenger_email: str, passenger_name: str, destination: str
) -> None:
    _send(
        to=passenger_email,
        subject=f"עדכון בפרטי הנסיעה — {destination}",
        html=_base(f"""
          <p>שלום {passenger_name},</p>
          <p>
            הנהג עדכן פרטים בנסיעה
            ל<strong style="color:#14B8A6">{destination}</strong>.
          </p>
          <p>היכנס/י לאפליקציה לצפייה בפרטים העדכניים.</p>
        """),
    )


def send_passenger_left(
    driver_email: str, driver_name: str, passenger_name: str, destination: str
) -> None:
    _send(
        to=driver_email,
        subject=f"נוסע ביטל — {destination}",
        html=_base(f"""
          <p>שלום {driver_name},</p>
          <p>
            <strong style="color:#f8fafc">{passenger_name}</strong>
            ביטל/ה את ההשתתפות בנסיעה
            ל<strong style="color:#14B8A6">{destination}</strong>.
          </p>
          <p>מקום פנוי זמין כעת — אחרים יוכלו להצטרף.</p>
        """),
    )
