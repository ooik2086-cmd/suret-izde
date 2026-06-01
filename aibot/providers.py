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

from config import MODELS, REPLICATE_API_TOKEN


class GenResult:
    """Генерация нәтижесі."""

    def __init__(self, kind, url=None, caption="", note=""):
        self.kind = kind        # "image" | "video" | "text"
        self.url = url          # дайын файл сілтемесі
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


def _build_input(mode, prompt, image_bytes):
    """Әр режимге Replicate кіріс параметрлерін құрастыру."""
    if mode == "image":
        return {"prompt": prompt}
    if mode == "video":
        return {"prompt": prompt}
    if mode == "restore":
        return {"img": io.BytesIO(image_bytes), "version": "v1.4", "scale": 2}
    if mode == "avatar":
        return {
            "input_image": io.BytesIO(image_bytes),
            "prompt": prompt or "professional studio portrait, clean background, sharp focus",
            "num_outputs": 1,
        }
    raise ValueError("белгісіз режим: %s" % mode)


class ReplicateProvider:
    available = True

    async def generate(self, mode, prompt=None, image_bytes=None):
        import replicate  # кешіктірілген импорт

        model = MODELS[mode]
        inp = _build_input(mode, prompt, image_bytes)
        out = await asyncio.to_thread(replicate.run, model, input=inp)
        url = _first_url(out)
        if not url:
            raise RuntimeError("модель бос нәтиже қайтарды")
        kind = "video" if mode == "video" else "image"
        return GenResult(kind, url=url)


class FreeProvider:
    """Кілтсіз тегін режим.

    Сурет — нақты генерация (Pollinations, API кілті қажет емес, тікелей
    сурет сілтемесін береді). Видео/жаңарту/аватар нақты AI кілтін
    (REPLICATE_API_TOKEN) талап етеді — оларға "needs_token" белгісін
    қайтарамыз, бот пайдаланушыға түсіндіреді.
    """

    available = True

    async def generate(self, mode, prompt=None, image_bytes=None):
        if mode == "image":
            seed = random.randint(1, 10_000_000)
            url = ("https://image.pollinations.ai/prompt/%s"
                   "?width=768&height=768&nologo=true&seed=%d"
                   % (quote((prompt or "art").strip())[:1500], seed))
            return GenResult("image", url=url)
        # Қалған режимдер нақты AI кілтін қажет етеді.
        return GenResult("text", note="needs_token")


class DemoProvider:
    """Желісіз/сынақ режимі — placeholder сурет (нақты генерациясыз)."""

    available = False

    async def generate(self, mode, prompt=None, image_bytes=None):
        await asyncio.sleep(0.1)
        seed = abs(hash((mode, prompt or "", len(image_bytes or b"")))) % 1000
        url = "https://picsum.photos/seed/%d/768/768" % seed
        return GenResult("image", url=url, note="demo")


def get_provider():
    return ReplicateProvider() if REPLICATE_API_TOKEN else FreeProvider()
