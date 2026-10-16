"""
security.py
PIN protection for the command-line app.

The PIN itself is never stored. We keep only a random salt and a
PBKDF2 hash of the PIN, so even someone who opens finance.db cannot
read it back. Wrong guesses are slowed down and capped.
"""

import hashlib
import hmac
import os
import re
import time
from getpass import getpass

from database import get_connection

ITERATIONS = 200_000
MAX_FAILS = 5


def _get(key):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def _set(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def _hash(pin, salt):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, ITERATIONS)


def has_pin():
    return _get("pin_hash") is not None


def set_pin(pin):
    if not re.fullmatch(r"\d{4,6}", pin):
        raise ValueError("PIN must be 4 to 6 digits.")
    salt = os.urandom(16)
    _set("pin_salt", salt.hex())
    _set("pin_hash", _hash(pin, salt).hex())


def remove_pin():
    conn = get_connection()
    conn.execute("DELETE FROM settings WHERE key IN ('pin_salt', 'pin_hash')")
    conn.commit()
    conn.close()


def verify_pin(pin):
    salt, stored = _get("pin_salt"), _get("pin_hash")
    if not salt or not stored:
        return True
    # compare_digest avoids leaking information through timing
    return hmac.compare_digest(_hash(pin, bytes.fromhex(salt)), bytes.fromhex(stored))


def login():
    """Ask for the PIN (hidden as you type). Returns True if access is allowed."""
    if not has_pin():
        return True
    for attempt in range(1, MAX_FAILS + 1):
        if verify_pin(getpass("Enter PIN: ")):
            return True
        print(f"Wrong PIN ({attempt}/{MAX_FAILS}).")
        time.sleep(attempt)  # each wrong guess waits longer
    print("Too many wrong attempts. Exiting.")
    return False
