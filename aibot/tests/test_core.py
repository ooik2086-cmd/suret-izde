# -*- coding: utf-8 -*-
"""aibot негізгі логикасының сынақтары (Telegram/желі қажет емес).

Тек таза модульдер тексеріледі: i18n, db (SQLite), providers (DemoProvider).
aiogram мен replicate импортталмайды.
"""

import os
import sys

import pytest

AIBOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AIBOT)


@pytest.fixture
def tmpdb(tmp_path, monkeypatch):
    # Әр сынаққа бөлек уақытша дерекқор.
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t.db"))
    for mod in ("config", "db"):
        sys.modules.pop(mod, None)
    import db
    return db


# ─────────────────────────── i18n ───────────────────────────
def test_i18n_all_keys_present_in_both_langs():
    import i18n
    kz, ru = set(i18n.T["kz"]), set(i18n.T["ru"])
    assert kz == ru, "KZ/RU кілттері сәйкес келмейді: %s" % (kz ^ ru)


def test_i18n_format_and_fallback():
    import i18n
    msg = i18n.t("kz", "limit_hit", mode="image", used=5, limit=5)
    assert "5/5" in msg
    # белгісіз тіл → kz-ке түседі, белгісіз кілт → кілттің өзі
    assert i18n.t("xx", "menu_image") == i18n.T["kz"]["menu_image"]
    assert i18n.t("kz", "no_such_key") == "no_such_key"


# ─────────────────────────── db: тіл ───────────────────────────
def test_lang_default_and_set(tmpdb):
    assert tmpdb.get_lang(111) == "kz"
    tmpdb.set_lang(111, "ru")
    assert tmpdb.get_lang(111) == "ru"


# ─────────────────────────── db: лимиттер ───────────────────────────
def test_limit_counts_and_blocks(tmpdb):
    uid = 222
    ok, used, limit = tmpdb.can_use(uid, "video")  # әдепкі лимит 1
    assert ok and used == 0 and limit == 1
    tmpdb.record_use(uid, "video")
    ok, used, limit = tmpdb.can_use(uid, "video")
    assert not ok and used == 1
    # басқа режим бөлек есептеледі
    ok2, _, _ = tmpdb.can_use(uid, "image")
    assert ok2


def test_usage_summary_shape(tmpdb):
    s = tmpdb.usage_summary(333)
    assert set(s.keys()) == {"image", "video", "restore", "avatar"}
    assert s["image"].endswith("/5")


# ─────────────────────────── providers ───────────────────────────
def test_demo_provider_returns_image_url():
    import asyncio
    import providers
    p = providers.DemoProvider()
    res = asyncio.run(p.generate("image", prompt="кеме"))
    assert res.kind == "image"
    assert res.url.startswith("http")
    assert res.note == "demo"


def test_get_provider_demo_without_token(monkeypatch):
    sys.modules.pop("config", None)
    sys.modules.pop("providers", None)
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
    import providers
    assert isinstance(providers.get_provider(), providers.DemoProvider)


def test_first_url_handles_list_and_object():
    import providers

    class Fake:
        url = "https://x/y.png"

    assert providers._first_url(["https://a/b.png", "c"]) == "https://a/b.png"
    assert providers._first_url(Fake()) == "https://x/y.png"
    assert providers._first_url(None) is None
