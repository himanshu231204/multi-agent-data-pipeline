import hashlib
import logging
import os
import sqlite3

from src.auth.github_api import has_followed, has_forked, has_starred
from src.cost_config import FREE_RUNS, LIFETIME_ACCESS_RUNS, STAR_BONUS_RUNS

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline_runs.db")

FREE_ANON_RUNS = 2


def _conn():
    return sqlite3.connect(DB_PATH)


# ── IP FINGERPRINT ────────────────────────────────────────────────────────────


def make_fingerprint(ip: str, user_agent: str) -> str:
    """SHA-256 of IP + User-Agent, truncated to 20 chars."""
    raw = f"{ip}|{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _init_anon_table():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS anon_visitors (
                fingerprint TEXT PRIMARY KEY,
                runs_used   INTEGER DEFAULT 0,
                first_seen  TEXT,
                last_seen   TEXT
            )
        """)


def get_anon_runs(fingerprint: str) -> int:
    _init_anon_table()
    from datetime import datetime

    now = datetime.utcnow().isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT runs_used FROM anon_visitors WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
        if not row:
            c.execute(
                "INSERT INTO anon_visitors VALUES (?,0,?,?)", (fingerprint, now, now)
            )
            return 0
        c.execute(
            "UPDATE anon_visitors SET last_seen=? WHERE fingerprint=?",
            (now, fingerprint),
        )
        return row[0]


def record_anon_run(fingerprint: str):
    _init_anon_table()
    with _conn() as c:
        c.execute(
            "UPDATE anon_visitors SET runs_used = runs_used + 1 WHERE fingerprint=?",
            (fingerprint,),
        )


def _init_users_table():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                github_username TEXT PRIMARY KEY,
                runs_used INTEGER DEFAULT 0,
                has_forked INTEGER DEFAULT 0,
                has_starred INTEGER DEFAULT 0,
                has_followed INTEGER DEFAULT 0,
                using_byok INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT
            )
        """)
        try:
            c.execute("ALTER TABLE users ADD COLUMN has_followed INTEGER DEFAULT 0")
        except Exception:
            pass


def get_or_create_user(username: str) -> dict:
    _init_users_table()
    from datetime import datetime

    now = datetime.utcnow().isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE github_username=?", (username,)
        ).fetchone()
        if not row:
            c.execute(
                "INSERT INTO users VALUES (?,0,0,0,0,0,?,?)", (username, now, now)
            )
            row = c.execute(
                "SELECT * FROM users WHERE github_username=?", (username,)
            ).fetchone()
        else:
            c.execute(
                "UPDATE users SET last_seen=? WHERE github_username=?", (now, username)
            )

    cols = [
        "github_username",
        "runs_used",
        "has_forked",
        "has_starred",
        "has_followed",
        "using_byok",
        "first_seen",
        "last_seen",
    ]
    if len(cols) != len(row):
        logger.warning(
            "Column/value length mismatch in credits: %d cols vs %d values",
            len(cols), len(row),
        )
    return dict(zip(cols, row, strict=False))


def refresh_github_status(username: str) -> dict:
    _init_users_table()
    forked = 1 if has_forked(username) else 0
    starred = 1 if has_starred(username) else 0
    followed = 1 if has_followed(username) else 0
    with _conn() as c:
        c.execute(
            "UPDATE users SET has_forked=?, has_starred=?, has_followed=? WHERE github_username=?",
            (forked, starred, followed, username),
        )
    return {
        "has_forked": bool(forked),
        "has_starred": bool(starred),
        "has_followed": bool(followed),
    }


def get_credits(username: str) -> dict:
    user = get_or_create_user(username)
    lifetime = bool(user["has_forked"]) and bool(user.get("has_followed", 0))
    if lifetime:
        max_free = LIFETIME_ACCESS_RUNS
    elif user["has_starred"]:
        max_free = FREE_RUNS + STAR_BONUS_RUNS
    else:
        max_free = FREE_RUNS
    runs_used = user["runs_used"]
    remaining = max(0, max_free - runs_used)
    can_run_free = remaining > 0 or lifetime
    needs_byok = not can_run_free and not user["using_byok"]
    return {
        "runs_used": runs_used,
        "max_free_runs": max_free,
        "remaining_free": remaining,
        "can_run_free": can_run_free,
        "needs_byok": needs_byok,
        "using_byok": bool(user["using_byok"]),
        "has_forked": bool(user["has_forked"]),
        "has_starred": bool(user["has_starred"]),
        "has_followed": bool(user.get("has_followed", 0)),
        "lifetime": lifetime,
    }


def record_run(username: str):
    _init_users_table()
    with _conn() as c:
        c.execute(
            "UPDATE users SET runs_used = runs_used + 1 WHERE github_username=?",
            (username,),
        )


def enable_byok(username: str):
    _init_users_table()
    with _conn() as c:
        c.execute("UPDATE users SET using_byok=1 WHERE github_username=?", (username,))


def can_run(username: str, byok_key: str = None) -> tuple[bool, str]:
    credits = get_credits(username)
    if credits["can_run_free"]:
        return True, "free"
    if byok_key:
        enable_byok(username)
        return True, "byok"
    return False, "no_credits"
