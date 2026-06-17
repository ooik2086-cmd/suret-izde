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
def test_i18n_all_keys_present_in_all_langs():
    import i18n
    kz, ru, en = set(i18n.T["kz"]), set(i18n.T["ru"]), set(i18n.T["en"])
    assert kz == ru, "KZ/RU сәйкес емес: %s" % (kz ^ ru)
    assert kz == en, "KZ/EN сәйкес емес: %s" % (kz ^ en)


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
    # Сурет — тегін лимитпен (әдепкі 5).
    ok, used, limit = tmpdb.can_use(uid, "image")
    assert ok and used == 0 and limit == 100
    tmpdb.record_use(uid, "image")
    ok, used, _ = tmpdb.can_use(uid, "image")
    assert ok and used == 1
    # Ақылы режим (видео) — тегін лимит 0 (тек кредитпен).
    okv, _, limv = tmpdb.can_use(uid, "video")
    assert not okv and limv == 0


def test_usage_summary_shape(tmpdb):
    s = tmpdb.usage_summary(333)
    assert {"image", "combine", "animate"} <= set(s.keys())
    assert s["image"].endswith("/100")


# ─────────────────────────── db: кредиттер (төлем) ───────────────────────────
def test_credits_add_and_use(tmpdb):
    uid = 444
    assert tmpdb.get_credits(uid) == 0
    assert tmpdb.add_credits(uid, 10) == 10
    assert tmpdb.add_credits(uid, 5) == 15      # қосылады
    assert tmpdb.use_credit(uid) is True
    assert tmpdb.get_credits(uid) == 14


def test_use_credit_when_empty_returns_false(tmpdb):
    assert tmpdb.use_credit(555) is False
    assert tmpdb.get_credits(555) == 0


# ─────────────────────────── db: жазылым (подписка) ───────────────────────────
def test_subscription_activates_and_extends(tmpdb):
    uid = 777
    assert tmpdb.is_subscribed(uid) is False
    tmpdb.add_sub(uid, 7)
    assert tmpdb.is_subscribed(uid) is True
    first = tmpdb.sub_until(uid)
    tmpdb.add_sub(uid, 30)  # белсендінің соңынан қосылады
    assert tmpdb.sub_until(uid) > first


def test_no_subscription_by_default(tmpdb):
    assert tmpdb.is_subscribed(888) is False
    assert tmpdb.sub_until(888) is None


# ─────────────────────────── providers ───────────────────────────
def test_free_provider_real_image_url():
    import asyncio
    import providers
    res = asyncio.run(providers.FreeProvider().generate("image", prompt="кеме теңізде"))
    assert res.kind == "image"
    assert res.url.startswith("https://image.pollinations.ai/prompt/")
    assert res.note == ""  # тегін режимде сурет — нақты генерация


def test_free_provider_paid_modes_need_token():
    import asyncio
    import providers
    for mode in ("combine", "animate"):
        res = asyncio.run(providers.FreeProvider().generate(mode, prompt="x"))
        assert res.note == "needs_token"


def test_build_input_animate_uses_configured_fields():
    import providers
    import config
    inp = providers._build_input("animate", "", b"img-bytes", b"vid-bytes")
    assert config.ANIMATE_IMAGE_FIELD in inp
    assert config.ANIMATE_VIDEO_FIELD in inp


def test_build_input_combine_passes_images():
    import providers
    import config
    inp = providers._build_input("combine", "merge", None, images=[b"a", b"b"])
    assert config.COMBINE_IMAGE_FIELD in inp
    assert len(inp[config.COMBINE_IMAGE_FIELD]) == 2
    assert inp["prompt"] == "merge"


def test_modes_in_limits():
    import config
    assert {"image", "combine", "animate", "music"} <= set(config.LIMITS)


def test_music_in_models_and_limits():
    import config
    assert "music" in config.MODELS and config.MODELS["music"]
    assert "music" in config.LIMITS


def test_build_music_input_uses_configured_fields():
    import config
    import providers
    inp = providers._build_music_input("pop, upbeat", "[verse]\nhello")
    assert inp[config.MUSIC_TAGS_FIELD] == "pop, upbeat"
    assert inp[config.MUSIC_LYRICS_FIELD] == "[verse]\nhello"
    assert inp[config.MUSIC_DURATION_FIELD] == config.MUSIC_DURATION


def test_build_music_input_has_safe_defaults():
    import providers
    inp = providers._build_music_input("", "")
    # Бос болса да модель құламас үшін фолбэк мәндер беріледі.
    assert all(v for v in inp.values())


def test_parse_song_json_plain_and_fenced():
    import providers
    tags, lyrics = providers._parse_song_json(
        '{"tags": "rock, loud", "lyrics": "[verse]\\nla la"}')
    assert tags == "rock, loud" and "la la" in lyrics
    # Markdown ```json ... ``` қоршауын да тазалай алады.
    tags2, lyrics2 = providers._parse_song_json(
        '```json\n{"tags": "jazz", "lyrics": "smooth"}\n```')
    assert tags2 == "jazz" and lyrics2 == "smooth"
    # Бұзық кіріс — қауіпсіз фолбэк (бос lyrics).
    tags3, lyrics3 = providers._parse_song_json("not json at all")
    assert tags3 == "pop" and lyrics3 == ""


def test_free_provider_music_needs_token():
    import asyncio
    import providers
    res = asyncio.run(providers.FreeProvider().generate("music", prompt="ауыл туралы ән"))
    assert res.note == "needs_token"


def test_demo_provider_returns_placeholder():
    import asyncio
    import providers
    res = asyncio.run(providers.DemoProvider().generate("image", prompt="кеме"))
    assert res.kind == "image" and res.url.startswith("http") and res.note == "demo"


def test_get_provider_is_hybrid(monkeypatch):
    sys.modules.pop("config", None)
    sys.modules.pop("providers", None)
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
    import providers
    assert isinstance(providers.get_provider(), providers.HybridProvider)


def test_hybrid_image_is_free_other_needs_token(monkeypatch):
    import asyncio
    sys.modules.pop("config", None)
    sys.modules.pop("providers", None)
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
    import providers
    p = providers.HybridProvider()
    img = asyncio.run(p.generate("image", prompt="теңіз"))
    assert img.url.startswith("https://image.pollinations.ai/prompt/")
    vid = asyncio.run(p.generate("video", prompt="x"))
    assert vid.note == "needs_token"


def test_first_url_handles_list_and_object():
    import providers

    class Fake:
        url = "https://x/y.png"

    assert providers._first_url(["https://a/b.png", "c"]) == "https://a/b.png"
    assert providers._first_url(Fake()) == "https://x/y.png"
    assert providers._first_url(None) is None
