# -*- coding: utf-8 -*-
"""AvtoUsta дерекқор қабаты (рөл, профиль, шебер, санат, рейтинг).

Екі режим (aibot-тағыдай):
  • DATABASE_URL берілсе → Postgres (тұрақты)
  • берілмесе          → жергілікті SQLite (фолбэк + сынақтар)
"""

import datetime
import sqlite3
import threading

from config import DATABASE_URL, DB_PATH, DEFAULT_LANG, ROLE_MASTER

_lock = threading.Lock()
_conn = None
_PG = False

_DDL = (
    # Барлық пайдаланушы (рөлі: client | master | NULL=тіркелмеген).
    "CREATE TABLE IF NOT EXISTS users("
    "user_id BIGINT PRIMARY KEY, role TEXT, lang TEXT, "
    "name TEXT, city TEXT, phone TEXT, created TEXT)",
    # Шебер профилінің кеңейтімі.
    "CREATE TABLE IF NOT EXISTS masters("
    "user_id BIGINT PRIMARY KEY, mtype TEXT, about TEXT, "
    "verified INTEGER DEFAULT 0, rating_sum INTEGER DEFAULT 0, "
    "rating_cnt INTEGER DEFAULT 0, promoted_until TEXT, sub_until TEXT)",
    # Шебердің мамандықтары (көп-көпке).
    "CREATE TABLE IF NOT EXISTS master_cats("
    "user_id BIGINT, cat TEXT, PRIMARY KEY(user_id, cat))",
)


def _connect():
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
    with _lock:
        cur = _db().cursor()
        cur.execute(_q(sql), params)
        out = None
        if fetch == "one":
            out = cur.fetchone()
        elif fetch == "all":
            out = cur.fetchall()
        if not _PG:
            _conn.commit()
        cur.close()
        return out


def _now():
    return datetime.datetime.utcnow().isoformat()


# ─────────────────────────── тіл ───────────────────────────
def get_lang(user_id):
    row = _exec("SELECT lang FROM users WHERE user_id=?", (user_id,), "one")
    return row[0] if row and row[0] else DEFAULT_LANG


def set_lang(user_id, lang):
    _exec(
        "INSERT INTO users(user_id, lang, created) VALUES(?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
        (user_id, lang, _now()),
    )


# ─────────────────────────── рөл / профиль ───────────────────────────
def get_user(user_id):
    row = _exec(
        "SELECT user_id, role, lang, name, city, phone, created "
        "FROM users WHERE user_id=?", (user_id,), "one")
    if not row:
        return None
    keys = ("user_id", "role", "lang", "name", "city", "phone", "created")
    return dict(zip(keys, row))


def get_role(user_id):
    u = get_user(user_id)
    return u["role"] if u else None


def is_registered(user_id):
    """Рөлі бар (клиент не шебер ретінде тіркелген) бе?"""
    return get_role(user_id) in ("client", "master")


def _save_lang_keep(user_id, lang):
    """Тілді сақтап қою (тіркелуге дейін таңдалуы мүмкін)."""
    if lang:
        set_lang(user_id, lang)


def register_client(user_id, name, city, lang=None):
    _save_lang_keep(user_id, lang)
    _exec(
        "INSERT INTO users(user_id, role, name, city, created) VALUES(?,?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET role=excluded.role, "
        "name=excluded.name, city=excluded.city",
        (user_id, "client", name, city, _now()),
    )


def register_master(user_id, name, city, phone, mtype, about, cats, lang=None):
    _save_lang_keep(user_id, lang)
    _exec(
        "INSERT INTO users(user_id, role, name, city, phone, created) "
        "VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET role=excluded.role, "
        "name=excluded.name, city=excluded.city, phone=excluded.phone",
        (user_id, "master", name, city, phone, _now()),
    )
    _exec(
        "INSERT INTO masters(user_id, mtype, about) VALUES(?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET mtype=excluded.mtype, about=excluded.about",
        (user_id, mtype, about),
    )
    set_master_cats(user_id, cats)


def set_master_cats(user_id, cats):
    _exec("DELETE FROM master_cats WHERE user_id=?", (user_id,))
    for cat in dict.fromkeys(cats):  # қайталануды алып тастаймыз
        _exec("INSERT INTO master_cats(user_id, cat) VALUES(?,?) "
              "ON CONFLICT(user_id, cat) DO NOTHING", (user_id, cat))


def get_master_cats(user_id):
    rows = _exec("SELECT cat FROM master_cats WHERE user_id=?", (user_id,), "all") or []
    return [r[0] for r in rows]


def get_master(user_id):
    """Шебердің толық профилі (users + masters + cats) немесе None."""
    row = _exec(
        "SELECT u.user_id, u.name, u.city, u.phone, m.mtype, m.about, "
        "m.verified, m.rating_sum, m.rating_cnt, m.promoted_until, m.sub_until "
        "FROM users u JOIN masters m ON u.user_id=m.user_id "
        "WHERE u.user_id=? AND u.role=?",
        (user_id, ROLE_MASTER), "one")
    if not row:
        return None
    keys = ("user_id", "name", "city", "phone", "mtype", "about", "verified",
            "rating_sum", "rating_cnt", "promoted_until", "sub_until")
    d = dict(zip(keys, row))
    d["cats"] = get_master_cats(user_id)
    d["rating"] = round(d["rating_sum"] / d["rating_cnt"], 1) if d["rating_cnt"] else 0.0
    d["promoted"] = _is_future(d["promoted_until"])
    return d


def set_master_verified(user_id, verified=True):
    _exec("UPDATE masters SET verified=? WHERE user_id=?",
          (1 if verified else 0, user_id))


def add_master_rating(user_id, stars):
    """Шеберге баға қосады (1-5 жұлдыз)."""
    stars = max(1, min(5, int(stars)))
    _exec("UPDATE masters SET rating_sum=rating_sum+?, rating_cnt=rating_cnt+1 "
          "WHERE user_id=?", (stars, user_id))


# ─────────────────────────── іздеу ───────────────────────────
def _is_future(iso):
    if not iso:
        return False
    try:
        return datetime.datetime.fromisoformat(iso) > datetime.datetime.utcnow()
    except ValueError:
        return False


def search_masters(city=None, cat=None):
    """Қала (+ міндетті емес санат) бойынша шеберлерді табады.
    Сұрыптау: алдымен TOP (жарнамаланған), сосын рейтинг жоғары.

    Қала Python-да casefold-пен салыстырылады — SQLite LOWER() кириллицаны
    аудармайды, сондықтан backend-ке тәуелсіз бірыңғай нәтиже береміз."""
    sql = (
        "SELECT u.user_id, u.name, u.city, u.phone, m.mtype, m.about, "
        "m.verified, m.rating_sum, m.rating_cnt, m.promoted_until "
        "FROM users u JOIN masters m ON u.user_id=m.user_id ")
    params = []
    if cat:
        sql += "JOIN master_cats c ON c.user_id=u.user_id AND c.cat=? "
        params.append(cat)
    sql += "WHERE u.role='master'"
    rows = _exec(sql, tuple(params), "all") or []
    want_city = (city or "").strip().casefold()
    keys = ("user_id", "name", "city", "phone", "mtype", "about", "verified",
            "rating_sum", "rating_cnt", "promoted_until")
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        if want_city and (d["city"] or "").strip().casefold() != want_city:
            continue
        d["cats"] = get_master_cats(d["user_id"])
        d["rating"] = round(d["rating_sum"] / d["rating_cnt"], 1) if d["rating_cnt"] else 0.0
        d["promoted"] = _is_future(d["promoted_until"])
        out.append(d)
    out.sort(key=lambda d: (d["promoted"], d["rating"], d["rating_cnt"]), reverse=True)
    return out


def count_masters():
    row = _exec("SELECT COUNT(*) FROM users WHERE role='master'", (), "one")
    return row[0] if row else 0
