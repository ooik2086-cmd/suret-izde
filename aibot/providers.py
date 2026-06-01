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
        "You are an expert image-prompt engineer. The user's request may be in "
        "Kazakh or Russian and may contain typos. Fix it, translate to English, "
        "and rewrite it as ONE concise vivid English image-generation prompt with "
        "useful visual detail and quality tags (lighting, style, 'highly detailed', "
        "'4k'). Output ONLY the final prompt — no quotes, no explanation."
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
            return out[:1500]
    except Exception:
        pass
    return await translate_to_en(text)  # фолбэк


from config import (
    ANIMATE_IMAGE_FIELD,
    ANIMATE_VIDEO_FIELD,
    COMBINE_IMAGE_FIELD,
    IMAGE_VARIANTS,
    MODELS,
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


class ReplicateProvider:
    available = True

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None, images=None):
        import replicate  # кешіктірілген импорт

        model = MODELS[mode]
        inp = _build_input(mode, prompt, image_bytes, video_bytes, images)
        out = await asyncio.to_thread(replicate.run, model, input=inp)
        url = _first_url(out)
        if not url:
            raise RuntimeError("модель бос нәтиже қайтарды")
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

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None, images=None):
        if mode == "image":
            en = await enhance_prompt(prompt)  # түзейді+аударады+толықтырады
            urls = []
            for _ in range(max(1, IMAGE_VARIANTS)):
                seed = random.randint(1, 10_000_000)
                urls.append(
                    "https://image.pollinations.ai/prompt/%s"
                    "?width=1024&height=1024&model=flux&nologo=true&seed=%d"
                    % (quote(en)[:1500], seed))
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

    async def generate(self, mode, prompt=None, image_bytes=None, video_bytes=None, images=None):
        if mode == "image":
            return await self._free.generate(mode, prompt=prompt)
        if self._replicate is not None:
            return await self._replicate.generate(
                mode, prompt=prompt, image_bytes=image_bytes,
                video_bytes=video_bytes, images=images)
        return GenResult("text", note="needs_token")


def get_provider():
    return HybridProvider()
