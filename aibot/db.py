# -*- coding: utf-8 -*-
"""Тіл параметрі мен тәуліктік қолдану лимитін сақтайтын кішкентай SQLite қабат.

Ескерту: Render тегін жоспарда диск тұрақсыз — қайта деплойда дерекқор нөлденуі
мүмкін. MVP үшін жеткілікті; тұрақты лимит керек болса, сыртқы Postgres қосыңыз.
"""

import datetime
import sqlite3
import threading

from config import DB_PATH, DEFAULT_LANG, LIMITS

_lock = threading.Lock()
_conn = None


def _db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, lang TEXT)"
        )
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS usage("
            "user_id INTEGER, day TEXT, mode TEXT, n INTEGER, "
            "PRIMARY KEY(user_id, day, mode))"
        )
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS credits(user_id INTEGER PRIMARY KEY, n INTEGER)"
        )
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS subs(user_id INTEGER PRIMARY KEY, until TEXT)"
        )
        _conn.commit()
    return _conn


def _today():
    return datetime.date.today().isoformat()


def get_lang(user_id):
    with _lock:
        row = _db().execute(
            "SELECT lang FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
    return row[0] if row and row[0] else DEFAULT_LANG


def set_lang(user_id, lang):
    with _lock:
        _db().execute(
            "INSERT INTO users(user_id, lang) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
            (user_id, lang),
        )
        _db().commit()


def used_today(user_id, mode):
    with _lock:
        row = _db().execute(
            "SELECT n FROM usage WHERE user_id=? AND day=? AND mode=?",
            (user_id, _today(), mode),
        ).fetchone()
    return row[0] if row else 0


def can_use(user_id, mode):
    """(рұқсат па, қанша қолданылды, лимит) қайтарады."""
    limit = LIMITS.get(mode, 0)
    used = used_today(user_id, mode)
    return used < limit, used, limit


def record_use(user_id, mode):
    with _lock:
        _db().execute(
            "INSERT INTO usage(user_id, day, mode, n) VALUES(?,?,?,1) "
            "ON CONFLICT(user_id, day, mode) DO UPDATE SET n = n + 1",
            (user_id, _today(), mode),
        )
        _db().commit()


def usage_summary(user_id):
    return {m: "%d/%d" % (used_today(user_id, m), LIMITS.get(m, 0)) for m in LIMITS}


# ─────────────────────────── кредиттер (сатып алынған генерация) ───────────────────────────
def get_credits(user_id):
    with _lock:
        row = _db().execute(
            "SELECT n FROM credits WHERE user_id=?", (user_id,)
        ).fetchone()
    return row[0] if row else 0


def add_credits(user_id, n):
    with _lock:
        _db().execute(
            "INSERT INTO credits(user_id, n) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET n = n + excluded.n",
            (user_id, n),
        )
        _db().commit()
    return get_credits(user_id)


def use_credit(user_id):
    """Бір кредитті жұмсайды. Сәтті болса True қайтарады."""
    with _lock:
        cur = _db().execute(
            "UPDATE credits SET n = n - 1 WHERE user_id=? AND n > 0", (user_id,)
        )
        _db().commit()
        return cur.rowcount > 0


# ─────────────────────────── жазылым (подписка) ───────────────────────────
def sub_until(user_id):
    """Жазылымның аяқталу уақыты (datetime) немесе None."""
    with _lock:
        row = _db().execute(
            "SELECT until FROM subs WHERE user_id=?", (user_id,)
        ).fetchone()
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
    with _lock:
        _db().execute(
            "INSERT INTO subs(user_id, until) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET until=excluded.until",
            (user_id, until),
        )
        _db().commit()
    return until
