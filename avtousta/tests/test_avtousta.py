# -*- coding: utf-8 -*-
"""AvtoUsta негізгі логикасының сынақтары (Telegram/желі қажет емес).

Тек таза модульдер: i18n, config, db (SQLite). aiogram импортталмайды.
"""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


@pytest.fixture
def tmpdb(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    for mod in ("config", "db"):
        sys.modules.pop(mod, None)
    import db
    return db


# ─────────────────────────── i18n ───────────────────────────
def test_i18n_all_keys_present_in_all_langs():
    import i18n
    kz, ru = set(i18n.T["kz"]), set(i18n.T["ru"])
    assert kz == ru, "KZ/RU сәйкес емес: %s" % (kz ^ ru)


def test_i18n_format_and_fallback():
    import i18n
    msg = i18n.t("kz", "search_header", n=3)
    assert "3" in msg
    assert i18n.t("xx", "m_search") == i18n.T["kz"]["m_search"]
    assert i18n.t("kz", "no_such_key") == "no_such_key"


# ─────────────────────────── config ───────────────────────────
def test_config_categories_and_types():
    import config
    assert len(config.CATEGORIES) >= 5
    assert len(config.MASTER_TYPES) >= 2
    # Әр санат — 4 элемент (key, emoji, kz, ru).
    assert all(len(c) == 4 for c in config.CATEGORIES)
    assert config.cat_label("kz", "motor")
    assert config.cat_label("ru", "motor") != config.cat_label("kz", "motor")
    assert config.mtype_label("kz", "mobile")
    # Белгісіз кілт — өзін қайтарады (құламайды).
    assert config.cat_label("kz", "nope") == "nope"


# ─────────────────────────── db: тіл ───────────────────────────
def test_lang_default_and_set(tmpdb):
    assert tmpdb.get_lang(1) == "kz"
    tmpdb.set_lang(1, "ru")
    assert tmpdb.get_lang(1) == "ru"


# ─────────────────────────── db: клиент тіркелуі ───────────────────────────
def test_register_client(tmpdb):
    uid = 10
    assert tmpdb.is_registered(uid) is False
    tmpdb.register_client(uid, "Айдос", "Алматы", "kz")
    assert tmpdb.is_registered(uid) is True
    assert tmpdb.get_role(uid) == "client"
    u = tmpdb.get_user(uid)
    assert u["name"] == "Айдос" and u["city"] == "Алматы" and u["lang"] == "kz"


# ─────────────────────────── db: шебер тіркелуі ───────────────────────────
def test_register_master_and_profile(tmpdb):
    uid = 20
    tmpdb.register_master(uid, "СТО Бұлақ", "Астана", "+77011112233",
                          "sto", "10 жыл тәжірибе", ["motor", "electric"], "kz")
    assert tmpdb.get_role(uid) == "master"
    d = tmpdb.get_master(uid)
    assert d["name"] == "СТО Бұлақ" and d["city"] == "Астана"
    assert d["mtype"] == "sto" and d["phone"] == "+77011112233"
    assert set(d["cats"]) == {"motor", "electric"}
    assert d["rating"] == 0.0 and d["verified"] == 0


def test_master_cats_dedup_and_update(tmpdb):
    uid = 21
    tmpdb.register_master(uid, "A", "Шымкент", "1", "garage", "", ["body", "body"], "kz")
    assert tmpdb.get_master_cats(uid) == ["body"]
    tmpdb.set_master_cats(uid, ["tires", "ac"])
    assert set(tmpdb.get_master_cats(uid)) == {"tires", "ac"}


# ─────────────────────────── db: рейтинг ───────────────────────────
def test_master_rating(tmpdb):
    uid = 30
    tmpdb.register_master(uid, "M", "Тараз", "1", "mobile", "", ["motor"], "kz")
    tmpdb.add_master_rating(uid, 5)
    tmpdb.add_master_rating(uid, 4)
    d = tmpdb.get_master(uid)
    assert d["rating_cnt"] == 2 and d["rating"] == 4.5


def test_verify_master(tmpdb):
    uid = 31
    tmpdb.register_master(uid, "M", "Тараз", "1", "sto", "", ["motor"], "kz")
    tmpdb.set_master_verified(uid, True)
    assert tmpdb.get_master(uid)["verified"] == 1


# ─────────────────────────── db: іздеу ───────────────────────────
def test_search_by_city_and_category(tmpdb):
    tmpdb.register_master(101, "Мотор устасы", "Алматы", "1", "sto", "", ["motor"], "kz")
    tmpdb.register_master(102, "Электрик", "Алматы", "2", "garage", "", ["electric"], "kz")
    tmpdb.register_master(103, "Басқа қала", "Астана", "3", "sto", "", ["motor"], "kz")
    # Қала + санат бойынша сүзу.
    res = tmpdb.search_masters(city="Алматы", cat="motor")
    assert [d["user_id"] for d in res] == [101]
    # Қала бойынша (бар санат) — екеуі.
    res2 = tmpdb.search_masters(city="алматы")  # регистрге тәуелсіз
    assert {d["user_id"] for d in res2} == {101, 102}
    # Басқа қала бөлек.
    assert {d["user_id"] for d in tmpdb.search_masters(city="Астана")} == {103}


def test_search_orders_rated_first(tmpdb):
    tmpdb.register_master(201, "Бағасыз", "Орал", "1", "sto", "", ["motor"], "kz")
    tmpdb.register_master(202, "Жоғары рейтинг", "Орал", "2", "sto", "", ["motor"], "kz")
    tmpdb.add_master_rating(202, 5)
    res = tmpdb.search_masters(city="Орал", cat="motor")
    assert res[0]["user_id"] == 202  # рейтингі бар шебер жоғарыда


def test_search_empty(tmpdb):
    assert tmpdb.search_masters(city="ЖоқҚала", cat="motor") == []
    assert tmpdb.count_masters() == 0
