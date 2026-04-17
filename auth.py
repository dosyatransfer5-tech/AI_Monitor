"""
Authentication helpers for tire press chatbot.
Password hashing: PBKDF2-HMAC-SHA256 (stdlib only, no extra dependencies).
"""

import hashlib
import json
import os

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_PATH    = os.path.join(_BASE, "data", "users.json")
MACHINES_PATH = os.path.join(_BASE, "data", "machines.json")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    ).hex()


def check_credentials(username: str, password: str) -> dict | None:
    """Return the user dict if credentials are valid, otherwise None."""
    try:
        with open(USERS_PATH, encoding="utf-8") as f:
            users = json.load(f).get("users", [])
        for u in users:
            if u.get("username") == username:
                if _hash_password(password, u["salt"]) == u["password_hash"]:
                    return u
    except Exception:
        pass
    return None


def load_machines() -> list[dict]:
    """Return all active machines from machines.json."""
    try:
        with open(MACHINES_PATH, encoding="utf-8") as f:
            return [m for m in json.load(f).get("machines", []) if m.get("active", True)]
    except Exception:
        return []
