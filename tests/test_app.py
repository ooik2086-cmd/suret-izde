# -*- coding: utf-8 -*-
"""
app.py үшін автоматты сынақтар (желіге шықпайды).

Сыртқы хостарға нақты сұраныс жібермейміз — _post пен upload_image
функцияларын monkeypatch арқылы алмастырамыз. Сол себепті сынақтар
интернетсіз де, CI-да да тұрақты әрі жылдам жұмыс істейді.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as appmod  # noqa: E402


@pytest.fixture
def client():
    appmod.app.config["TESTING"] = True
    with appmod.app.test_client() as c:
        yield c


# ─────────────────────────── парсерлер ───────────────────────────
def test_p_plain_accepts_url():
    assert appmod._p_plain("https://catbox.moe/x.jpg") == "https://catbox.moe/x.jpg"


def test_p_plain_rejects_non_url():
    assert appmod._p_plain("error: something") is None


def test_p_uguu_parses_first_url():
    r = json.dumps({"files": [{"url": "https://uguu.se/a.jpg"}]})
    assert appmod._p_uguu(r) == "https://uguu.se/a.jpg"


def test_p_uguu_handles_bad_json():
    assert appmod._p_uguu("not json") is None


def test_p_tmpfiles_rewrites_to_direct_link():
    r = json.dumps({"data": {"url": "https://tmpfiles.org/123/x.jpg"}})
    assert appmod._p_tmpfiles(r) == "https://tmpfiles.org/dl/123/x.jpg"


def test_p_tmpfiles_handles_bad_json():
    assert appmod._p_tmpfiles("{}") is None


# ─────────────────────────── multipart ───────────────────────────
def test_multipart_contains_fields_and_file():
    boundary, body = appmod._multipart(
        {"reqtype": "fileupload"},
        {"fileToUpload": ("photo.jpg", b"\x89PNG", "image/jpeg")},
    )
    assert boundary in body.decode("latin-1")
    text = body.decode("latin-1")
    assert 'name="reqtype"' in text
    assert 'filename="photo.jpg"' in text
    assert body.rstrip().endswith(("--%s--" % boundary).encode())


# ─────────────────────────── upload_image ───────────────────────────
def test_upload_image_returns_first_success(monkeypatch):
    # Бірінші хост (catbox, _p_plain) бірден URL қайтарады.
    monkeypatch.setattr(appmod, "_post", lambda *a, **k: "https://catbox.moe/ok.jpg")
    assert appmod.upload_image(b"data", "p.jpg") == "https://catbox.moe/ok.jpg"


def test_upload_image_falls_back_to_next_host(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, *a, **k):
        calls["n"] += 1
        if "catbox" in url:
            raise RuntimeError("catbox down")
        return "https://0x0.st/zzz.png"  # келесі хост _p_plain

    monkeypatch.setattr(appmod, "_post", fake_post)
    got = appmod.upload_image(b"data", "p.jpg")
    assert got == "https://0x0.st/zzz.png"
    assert calls["n"] >= 2  # кемінде бір фолбэк болды


def test_upload_image_raises_when_all_hosts_fail(monkeypatch):
    def fake_post(*a, **k):
        raise RuntimeError("network unreachable")

    monkeypatch.setattr(appmod, "_post", fake_post)
    with pytest.raises(RuntimeError):
        appmod.upload_image(b"data", "p.jpg")


# ─────────────────────────── маршруттар ───────────────────────────
def test_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.content_type


@pytest.mark.parametrize("marker", [
    'data-l="en"', 'data-t="legend"', "NEEDS_LOGIN", "function lab",
    "searchAll", "comboBlock", "manifest.webmanifest",
    # жаңа желілер мен сурет сілтемесін көшіру мүмкіндігі
    "Pinterest", "Reddit", "Twitch", "function copyLink", "fallbackCopy",
])
def test_index_contains_feature_markers(client, marker):
    # check.yml тірі сайтта осы белгілерді іздейді — бұл жерде жергілікті бекітеміз.
    body = client.get("/").get_data(as_text=True)
    assert marker in body


def test_manifest_valid_json(client):
    r = client.get("/manifest.webmanifest")
    assert r.status_code == 200
    assert "application/manifest+json" in r.content_type
    data = json.loads(r.get_data(as_text=True))
    assert data["start_url"] == "/"
    assert len(data["icons"]) == 2


def test_service_worker_served(client):
    r = client.get("/sw.js")
    assert r.status_code == 200
    assert "javascript" in r.content_type
    assert "self.addEventListener" in r.get_data(as_text=True)


@pytest.mark.parametrize("path", ["/icon-192.png", "/icon-512.png"])
def test_icons_served(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.content_type == "image/png"


# ─────────────────────────── /upload эндпойнт ───────────────────────────
def test_upload_no_file_returns_400(client):
    r = client.post("/upload")
    assert r.status_code == 400
    assert r.get_json()["error"] == "no file"


def test_upload_success_returns_url(client, monkeypatch):
    monkeypatch.setattr(appmod, "upload_image", lambda raw, fn="p.jpg": "https://host/x.jpg")
    r = client.post("/upload", data={"photo": (_png(), "p.png")},
                     content_type="multipart/form-data")
    assert r.status_code == 200
    assert r.get_json()["url"] == "https://host/x.jpg"


def test_upload_failure_returns_500(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("all hosts failed")

    monkeypatch.setattr(appmod, "upload_image", boom)
    r = client.post("/upload", data={"photo": (_png(), "p.png")},
                    content_type="multipart/form-data")
    assert r.status_code == 500
    assert "all hosts failed" in r.get_json()["error"]


def _png():
    """Кішкентай жарамды PNG ағыны (1x1 пиксель)."""
    import base64
    import io
    raw = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQAY3Y2wAAAAAElFTkSuQmCC"
    )
    return io.BytesIO(raw)
