"""
emailer.py
Sends your VIT Aurum summary to your Gmail account through Gmail's SMTP server.

Gmail does not accept your normal password here. You need an *App Password*:
  1. Turn on 2-Step Verification: https://myaccount.google.com/security
  2. Create an app password:      https://myaccount.google.com/apppasswords
  3. Provide it as the GMAIL_APP_PASSWORD environment variable, or type it
     when asked. It is used for this one send and is never saved to disk.
"""

import os
import re
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from getpass import getpass

from database import get_connection

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class EmailError(Exception):
    """A problem sending the email, with a message that is safe to show the user."""


def valid_email(address: str) -> bool:
    return bool(EMAIL_RE.match(address))


def get_email():
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = 'email_address'").fetchone()
    conn.close()
    return row["value"] if row else None


def set_email(address: str):
    if not valid_email(address):
        raise ValueError("That does not look like an email address.")
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES ('email_address', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (address,))
    conn.commit()
    conn.close()


def summary_text(fm) -> str:
    s = fm.monthly_summary()
    _, projected = fm.projected_month_spend()
    lines = [
        f"VIT Aurum summary - {datetime.now():%B %Y}",
        f"Balance: ₹{fm.get_balance():,.2f}",
        f"Income: ₹{s['income']:,.2f}",
        f"Spent: ₹{s['expense']:,.2f}",
        f"Net: ₹{s['net']:,.2f}",
        f"Projected month-end spend: ₹{projected:,.2f}",
    ]
    for category, total in list(s["by_category"].items())[:5]:
        lines.append(f"  {category}: ₹{total:,.2f}")
    over = [f"{c}: ₹{b['spent']:,.2f} of ₹{b['limit']:,.2f}"
            for c, b in fm.check_budget_status().items() if b["over_budget"]]
    lines.append("Over budget: " + "; ".join(over) if over else "All budgets on track.")
    return "\n".join(lines)


def send_email(address: str, subject: str, body: str, password: str = None):
    """Send `body` from your Gmail account to itself. Raises EmailError on failure."""
    if not valid_email(address):
        raise EmailError("That does not look like an email address.")
    password = password or os.environ.get("GMAIL_APP_PASSWORD") or getpass(
        "Gmail App Password (not your normal password; not saved): ")
    password = password.replace(" ", "")  # Google shows app passwords in groups of four
    if not password:
        raise EmailError("No app password given.")

    msg = EmailMessage()
    msg["From"] = address
    msg["To"] = address
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(),
                              timeout=20) as server:
            server.login(address, password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        raise EmailError("Gmail rejected the login. Use an App Password (this needs "
                         "2-Step Verification), not your normal password.")
    except (OSError, smtplib.SMTPException) as e:
        raise EmailError(f"Could not reach Gmail: {e}")
