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


class DemoProvider:
    """Токенсіз режим — нақты генерациясыз, тек көрнекі placeholder."""

    available = False

    async def generate(self, mode, prompt=None, image_bytes=None):
        await asyncio.sleep(0.5)
        seed = abs(hash((mode, prompt or "", len(image_bytes or b"")))) % 1000
        url = "https://picsum.photos/seed/%d/768/768" % seed
        return GenResult("image", url=url, note="demo")


def get_provider():
    return ReplicateProvider() if REPLICATE_API_TOKEN else DemoProvider()
