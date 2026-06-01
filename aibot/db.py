# -*- coding: utf-8 -*-
"""Тіл, тәуліктік лимит, кредит және жазылымды сақтайтын дерекқор қабаты.

Екі режим:
  • DATABASE_URL берілсе  → Postgres (тұрақты, Render қайта іске қосылса да сақталады)
  • берілмесе/қосылмаса    → жергілікті SQLite (фолбэк, әрі сынақтар үшін)

SQL екеуіне де сәйкес жазылған; айырмашылық тек "?" (SQLite) ↔ "%s" (Postgres).
"""

import datetime
import sqlite3
import threading

from config import DATABASE_URL, DB_PATH, DEFAULT_LANG, LIMITS

_lock = threading.Lock()
_conn = None
_PG = False  # қазір Postgres қолданып жатырмыз ба

_DDL = (
    "CREATE TABLE IF NOT EXISTS users(user_id BIGINT PRIMARY KEY, lang TEXT)",
    "CREATE TABLE IF NOT EXISTS usage("
    "user_id BIGINT, day TEXT, mode TEXT, n INTEGER, "
    "PRIMARY KEY(user_id, day, mode))",
    "CREATE TABLE IF NOT EXISTS credits(user_id BIGINT PRIMARY KEY, n INTEGER)",
    "CREATE TABLE IF NOT EXISTS subs(user_id BIGINT PRIMARY KEY, until TEXT)",
)


def _connect():
    """Postgres-ке қосылуға тырысады; сәтсіз болса SQLite-қа қайтады."""
    global _PG
    if DATABASE_URL:
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
            conn.autocommit = True
            _PG = True
            return conn
        except Exception as e:  # noqa: BLE001
            print("⚠️ Postgres қосылмады (%s) — SQLite-қа көшемін." % e)
    _PG = False
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def _db():
    global _conn
    if _conn is None:
        _conn = _connect()
        cur = _conn.cursor()
        for ddl in _DDL:
            cur.execute(ddl)
        if not _PG:
            _conn.commit()
        cur.close()
    return _conn


def _q(sql):
    return sql.replace("?", "%s") if _PG else sql


def _exec(sql, params=(), fetch=None):
    """Сұранысты орындайды. fetch: None | "one" | "all". (нәтиже, rowcount) қайтарады."""
    with _lock:
        cur = _db().cursor()
        cur.execute(_q(sql), params)
        out = None
        if fetch == "one":
            out = cur.fetchone()
        elif fetch == "all":
            out = cur.fetchall()
        rc = cur.rowcount
        if not _PG:
            _conn.commit()
        cur.close()
        return out, rc


def _today():
    return datetime.date.today().isoformat()


# ─────────────────────────── тіл ───────────────────────────
def get_lang(user_id):
    row, _ = _exec("SELECT lang FROM users WHERE user_id=?", (user_id,), "one")
    return row[0] if row and row[0] else DEFAULT_LANG


def set_lang(user_id, lang):
    _exec(
        "INSERT INTO users(user_id, lang) VALUES(?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
        (user_id, lang),
    )


# ─────────────────────────── тәуліктік лимит ───────────────────────────
def used_today(user_id, mode):
    row, _ = _exec(
        "SELECT n FROM usage WHERE user_id=? AND day=? AND mode=?",
        (user_id, _today(), mode), "one",
    )
    return row[0] if row else 0


def can_use(user_id, mode):
    """(рұқсат па, қанша қолданылды, лимит) қайтарады."""
    limit = LIMITS.get(mode, 0)
    used = used_today(user_id, mode)
    return used < limit, used, limit


def record_use(user_id, mode):
    _exec(
        "INSERT INTO usage(user_id, day, mode, n) VALUES(?,?,?,1) "
        "ON CONFLICT(user_id, day, mode) DO UPDATE SET n = n + 1",
        (user_id, _today(), mode),
    )


def usage_summary(user_id):
    return {m: "%d/%d" % (used_today(user_id, m), LIMITS.get(m, 0)) for m in LIMITS}


# ─────────────────────────── кредиттер ───────────────────────────
def get_credits(user_id):
    row, _ = _exec("SELECT n FROM credits WHERE user_id=?", (user_id,), "one")
    return row[0] if row else 0


def add_credits(user_id, n):
    _exec(
        "INSERT INTO credits(user_id, n) VALUES(?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET n = n + excluded.n",
        (user_id, n),
    )
    return get_credits(user_id)


def use_credit(user_id):
    """Бір кредитті жұмсайды. Сәтті болса True."""
    _, rc = _exec("UPDATE credits SET n = n - 1 WHERE user_id=? AND n > 0", (user_id,))
    return rc > 0


# ─────────────────────────── жазылым (подписка) ───────────────────────────
def sub_until(user_id):
    row, _ = _exec("SELECT until FROM subs WHERE user_id=?", (user_id,), "one")
    if not row or not row[0]:
        return None
    try:
        return datetime.datetime.fromisoformat(row[0])
    except ValueError:
        return None


def is_subscribed(user_id):
    u = sub_until(user_id)
    return bool(u and u > datetime.datetime.utcnow())


def add_sub(user_id, days):
    """Жазылымды `days` күнге ұзартады (белсенді болса — соңынан қосады)."""
    now = datetime.datetime.utcnow()
    cur = sub_until(user_id)
    base = cur if (cur and cur > now) else now
    until = (base + datetime.timedelta(days=days)).isoformat()
    _exec(
        "INSERT INTO subs(user_id, until) VALUES(?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET until=excluded.until",
        (user_id, until),
    )
    return until
