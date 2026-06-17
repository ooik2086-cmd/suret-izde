# -*- coding: utf-8 -*-
"""Генерация провайдерлері.

Боттың "миын" осы жерде ауыстырамыз:
  • ReplicateProvider — нақты AI (REPLICATE_API_TOKEN болса).
  • DemoProvider      — токенсіз бірден сынау үшін (placeholder қайтарады).

`replicate` пакеті тек қажет болғанда импортталады, сондықтан бұл модульді
сынақтарда токенсіз/пакетсіз де импорттай беруге болады.
"""

import asyncio
import io
import json
import random
from urllib.parse import quote

import aiohttp


async def translate_to_en(text):
    """Қазақша/орысша тапсырманы ағылшыншаға аударады (сурет модельдері
    ағылшынды жақсы түсінеді). Аударма сәтсіз болса — түпнұсқаны қайтарады.
    Кілт қажет емес (Google тегін эндпойнты)."""
    text = (text or "").strip()
    if not text:
        return "beautiful art"
    # Бәрі ASCII (ағылшын) болса — аударудың қажеті жоқ.
    if all(ord(c) < 128 for c in text):
        return text
    try:
        params = {"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text}
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(
                "https://translate.googleapis.com/translate_a/single", params=params
            ) as r:
                data = await r.json(content_type=None)
        out = "".join(seg[0] for seg in data[0] if seg and seg[0]).strip()
        return out or text
    except Exception:
        return text


async def enhance_prompt(text):
    """Тапсырманы ақылды түрде ТҮЗЕП + ағылшыншаға АУДАРЫП + ТОЛЫҚТЫРАДЫ.
    Тегін LLM (Pollinations text). Сәтсіз болса — жай аудармаға қайтады."""
    text = (text or "").strip()
    if not text:
        return "beautiful art, highly detailed, 4k"
    system = (
        "You are an expert text-to-image prompt engineer. The user's request may be "
        "in Kazakh or Russian with typos. Fix it, translate to English, and rewrite it "
        "as ONE single concise vivid image prompt: a comma-separated visual description "
        "(NOT a sentence, NOT an explanation). Add quality tags such as 'highly detailed, "
        "sharp focus, 4k, professional, cinematic lighting'. "
        "IMPORTANT: image models cannot render named national flags or logos correctly, "
        "so if the user mentions one, REPLACE the name with an explicit visual description "
        "of its exact colors and symbols. For the flag of Kazakhstan specifically, write: "
        "'a sky-blue flag with a golden sun with rays in the center above a golden soaring "
        "steppe eagle, and a vertical golden national ornament band along the left edge'. "
        "Output ONLY the final prompt — no quotes, no preamble, no explanation."
    )
    try:
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "private": True,
        }
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post("https://text.pollinations.ai/openai", json=payload) as r:
                data = await r.json(content_type=None)
        out = (data["choices"][0]["message"]["content"] or "").strip().strip('"').strip()
        if out and len(out) > 3:
            return _fix_symbols(out[:1500])
    except Exception:
        pass
    return _fix_symbols(await translate_to_en(text))  # фолбэк


# Модельдер нақты ту/логотипті сала алмайды — атауды сипаттамаға ауыстырамыз.
_KZ_FLAG = ("the flag of Kazakhstan: a bright turquoise-cyan flag (sky-blue, not green, "
            "not teal), with ONE single centered golden sun with 32 straight rays, ONE "
            "single golden soaring steppe eagle directly beneath the sun, and a vertical "
            "golden Kazakh ornament strip along the left edge")


def _fix_symbols(prompt):
    low = prompt.lower()
    if "kazakh" in low and "32 straight rays" not in low:
        prompt += ", " + _KZ_FLAG
    return prompt


async def write_song(text):
    """Қарапайым идеядан ТОЛЫҚ ӘН жазады (тегін LLM, Pollinations text).

    Қайтарады: (tags, lyrics)
      • tags   — ағылшын стиль тегтері (жанр/көңіл-күй/вокал) — модель үшін.
      • lyrics — ҚОЛДАНУШЫ ТІЛІНДЕГІ ән мәтіні [verse]/[chorus] құрылымымен.

    Осылай адам қазақша «ауыл туралы көңілді ән» десе — бот толық қазақша
    ән мәтінін жазып, оны вокалмен орындатады («авто пилот»).
    Сәтсіз болса — қарапайым фолбэк қайтарады (зиянсыз)."""
    text = (text or "").strip()
    if not text:
        text = "a cheerful song about life"
    system = (
        "You are a professional songwriter. The user gives a simple idea or theme, "
        "possibly in Kazakh or Russian, possibly with typos. Write a COMPLETE song. "
        "Keep the LYRICS in the SAME language the user wrote in (a Kazakh idea -> "
        "Kazakh lyrics; a Russian idea -> Russian lyrics). Structure the lyrics with "
        "section tags like [verse], [chorus], [bridge] and real line breaks. "
        "Separately choose musical STYLE tags (genre, mood, tempo, instruments, vocal "
        "type) in ENGLISH. Respond with STRICT JSON ONLY, no markdown, exactly: "
        '{\"tags\": \"comma, separated, english, style, tags\", '
        '\"lyrics\": \"the full lyrics with [verse]/[chorus] tags and newlines\"}'
    )
    try:
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "private": True,
        }
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post("https://text.pollinations.ai/openai", json=payload) as r:
                data = await r.json(content_type=None)
        raw = (data["choices"][0]["message"]["content"] or "").strip()
        tags, lyrics = _parse_song_json(raw)
        if lyrics:
            return tags, lyrics
    except Exception:
        pass
    return "pop, catchy, upbeat, clear vocals", text


def _parse_song_json(raw):
    """LLM шығысынан (tags, lyrics) ажыратады. Markdown/қоршаулар болса тазалайды."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        nl = raw.find("\n")
        if nl != -1 and raw[:nl].strip().lower() in ("json", ""):
            raw = raw[nl + 1:]
    i, j = raw.find("{"), raw.rfind("}")
    if i != -1 and j != -1 and j > i:
        raw = raw[i:j + 1]
    try:
        obj = json.loads(raw)
        tags = (obj.get("tags") or "").strip()
        lyrics = (obj.get("lyrics") or "").strip()
        return (tags or "pop"), lyrics
    except Exception:
        return "pop", ""


from config import (
    ANIMATE_IMAGE_FIELD,
    ANIMATE_VIDEO_FIELD,
    COMBINE_IMAGE_FIELD,
    IMAGE_VARIANTS,
    MODELS,
    MUSIC_DURATION,
    MUSIC_DURATION_FIELD,
    MUSIC_LYRICS_FIELD,
    MUSIC_TAGS_FIELD,
    REPLICATE_API_TOKEN,
)


class GenResult:
    """Генерация нәтижесі."""

    def __init__(self, kind, url=None, caption="", note="", urls=None):
        self.kind = kind        # "image" | "video" | "text"
        self.url = url          # дайын файл сілтемесі (біреу)
        self.urls = urls or ([url] if url else [])  # бірнеше нұсқа (альбом)
        self.caption = caption
        self.note = note        # қосымша ескертпе (мыс. демо)


def _first_url(out):
    """Replicate шығысынан бірінші файл сілтемесін алу."""
    if out is None:
        return None
    if isinstance(out, (list, tuple)):
        out = out[0] if out else None
    if out is None:
        return None
    # Жаңа клиентте FileOutput объектісі; str() сілтеме береді.
    return getattr(out, "url", None) or str(out)


def _build_input(mode, prompt, image_bytes, video_bytes=None, images=None):
    """Әр режимге Replicate кіріс параметрлерін құрастыру."""
    if mode == "image":
        return {"prompt": prompt}
    if mode == "combine":
        # 2-3 суретті біріктіру/өңдеу. Суреттер тізіммен беріледі.
        inp = {COMBINE_IMAGE_FIELD: [io.BytesIO(b) for b in (images or [])]}
        inp["prompt"] = prompt or "combine these images into one cohesive image"
        return inp
    if mode == "animate":
        # Сурет (кейіпкер) + видео (қозғалыс) → жандандырылған видео.
        return {
            ANIMATE_IMAGE_FIELD: io.BytesIO(image_bytes),
            ANIMATE_VIDEO_FIELD: io.BytesIO(video_bytes),
        }
    raise ValueError("белгісіз режим: %s" % mode)


def _build_music_input(tags, lyrics):
    """🎵 Музыка моделіне (ACE-Step т.б.) кіріс параметрлерін құрастыру."""
    inp = {
        MUSIC_TAGS_FIELD: tags or "pop",
        MUSIC_LYRICS_FIELD: lyrics or "[verse]\nla la la la",
    }
    if MUSIC_DURATION_FIELD:
        inp[MUSIC_DURATION_FIELD] = MUSIC_DURATION
    return inp


class ReplicateProvider:
    available = True

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None, images=None):
        import replicate  # кешіктірілген импорт

        model = MODELS[mode]
        if mode == "music":
            # «Авто пилот»: бот алдымен әнді өзі жазады (мәтін + стиль), сосын орындатады.
            tags, lyrics = await write_song(prompt)
            inp = _build_music_input(tags, lyrics)
        else:
            inp = _build_input(mode, prompt, image_bytes, video_bytes, images)
        out = await asyncio.to_thread(replicate.run, model, input=inp)
        url = _first_url(out)
        if not url:
            raise RuntimeError("модель бос нәтиже қайтарды")
        if mode == "music":
            # Әннің мәтінін бірге қайтарамыз — пайдаланушы сөзін көреді.
            return GenResult("audio", url=url, caption=(lyrics or "")[:900])
        kind = "video" if mode in ("video", "animate") else "image"
        return GenResult(kind, url=url)


class FreeProvider:
    """Кілтсіз тегін режим.

    Сурет — нақты генерация (Pollinations, API кілті қажет емес, тікелей
    сурет сілтемесін береді). Видео/жаңарту/аватар нақты AI кілтін
    (REPLICATE_API_TOKEN) талап етеді — оларға "needs_token" белгісін
    қайтарамыз, бот пайдаланушыға түсіндіреді.
    """

    available = True

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None,
                       images=None, width=1024, height=1024):
        if mode == "image":
            en = await enhance_prompt(prompt)  # түзейді+аударады+толықтырады
            urls = []
            for _ in range(max(1, IMAGE_VARIANTS)):
                seed = random.randint(1, 10_000_000)
                urls.append(
                    "https://image.pollinations.ai/prompt/%s"
                    "?width=%d&height=%d&model=flux&nologo=true&seed=%d"
                    % (quote(en)[:1500], width, height, seed))
            return GenResult("image", url=urls[0], urls=urls)
        # Қалған режимдер нақты AI кілтін қажет етеді.
        return GenResult("text", note="needs_token")


class DemoProvider:
    """Желісіз/сынақ режимі — placeholder сурет (нақты генерациясыз)."""

    available = False

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None, images=None):
        await asyncio.sleep(0.1)
        seed = abs(hash((mode, prompt or "", len(image_bytes or b"")))) % 1000
        url = "https://picsum.photos/seed/%d/768/768" % seed
        return GenResult("image", url=url, note="demo")


class HybridProvider:
    """Аралас режим (әдепкі).

    • Сурет — әрқашан ТЕГІН (Pollinations, ақша/кредит қажет емес).
    • Видео/жаңарту/аватар/жандандыру — Replicate (REPLICATE_API_TOKEN болса);
      кілт жоқ болса "needs_token" қайтарады.

    Осылай Replicate-те кредит болмаса да, бот сурет жасай береді.
    """

    available = True

    def __init__(self):
        self._free = FreeProvider()
        self._replicate = ReplicateProvider() if REPLICATE_API_TOKEN else None

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None,
                       images=None, width=1024, height=1024):
        if mode == "image":
            return await self._free.generate(mode, prompt=prompt, width=width, height=height)
        if self._replicate is not None:
            return await self._replicate.generate(
                mode, prompt=prompt, image_bytes=image_bytes,
                video_bytes=video_bytes, images=images)
        return GenResult("text", note="needs_token")


def get_provider():
    return HybridProvider()
