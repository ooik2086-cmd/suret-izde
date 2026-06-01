# -*- coding: utf-8 -*-
"""AI-генератор Telegram боты (aiogram v3).

Іске қосу (жергілікті):
    export BOT_TOKEN=...           # @BotFather-дан
    export REPLICATE_API_TOKEN=... # міндетті емес (болмаса демо режим)
    python bot.py

Render-де web-сервис ретінде жұмыс істейді: long-polling + $PORT-тағы
кішкентай денсаулық тексеру (health) сервері қатар жүреді.
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiohttp import web

import config
import db
from i18n import t
from providers import get_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("aibot")

# Пайдаланушы соңғы таңдаған режим (жадыда; қайта іске қосылса нөлденеді).
user_mode = {}

# Ақылы (Replicate) режимдер — тек сатып алынған кредитпен істейді (зиянсыз).
PAID_MODES = {"combine", "animate"}
# "animate": алдымен ВИДЕО, сосын СУРЕТ. Аралық видео осында (user_id → байт).
animate_video = {}
# "combine": бірнеше сурет жинаймыз (user_id → [байт]) + қосымша нұсқау.
combine_images = {}
combine_prompt = {}

provider = get_provider()


# ─────────────────────────── пернетақталар ───────────────────────────
def main_menu(lang):
    rows = [
        [InlineKeyboardButton(text=t(lang, "menu_image"), callback_data="m:image")],
        [InlineKeyboardButton(text=t(lang, "menu_combine"), callback_data="m:combine")],
        [InlineKeyboardButton(text=t(lang, "menu_animate"), callback_data="m:animate")],
        [InlineKeyboardButton(text=t(lang, "menu_buy"), callback_data="buy")],
        [
            InlineKeyboardButton(text=t(lang, "menu_balance"), callback_data="balance"),
            InlineKeyboardButton(text=t(lang, "menu_lang"), callback_data="lang"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def combine_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "combine_btn"), callback_data="combine_go")],
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")],
    ])


def sub_name(lang, days):
    """Жазылым атауы: 7 күн → апта, әйтпесе ай."""
    return t(lang, "sub_week") if days <= 7 else t(lang, "sub_month")


def buy_menu(lang):
    # Жазылым (шексіз сурет) + кредит пакеттері (ақылы видео/жандандыру т.б.)
    rows = [
        [InlineKeyboardButton(
            text="%s — %d ⭐" % (sub_name(lang, days), stars),
            callback_data="sub:%d" % days)]
        for days, stars in config.SUBSCRIPTIONS
    ]
    rows += [
        [InlineKeyboardButton(
            text=t(lang, "pkg_label", n=n, stars=stars),
            callback_data="pkg:%d:%d" % (n, stars))]
        for n, stars in config.PACKAGES
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def limit_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "menu_buy"), callback_data="buy")],
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")],
    ])


def lang_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="setlang:kz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang:en")],
    ])


def back_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")],
    ])


# ─────────────────────────── хендлерлер ───────────────────────────
dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(m: Message):
    lang = db.get_lang(m.from_user.id)
    await m.answer(t(lang, "welcome"), reply_markup=main_menu(lang))


@dp.callback_query(F.data == "menu")
async def on_menu(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    await c.message.edit_text(t(lang, "welcome"), reply_markup=main_menu(lang))
    await c.answer()


@dp.callback_query(F.data == "lang")
async def on_lang(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    await c.message.edit_text(t(lang, "choose_lang"), reply_markup=lang_menu())
    await c.answer()


@dp.callback_query(F.data.startswith("setlang:"))
async def on_setlang(c: CallbackQuery):
    lang = c.data.split(":", 1)[1]
    db.set_lang(c.from_user.id, lang)
    await c.message.edit_text(t(lang, "welcome"), reply_markup=main_menu(lang))
    await c.answer()


@dp.callback_query(F.data == "balance")
async def on_balance(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    s = db.usage_summary(c.from_user.id)
    text = t(lang, "balance", image=s["image"], combine=s["combine"],
             animate=s["animate"])
    text += "\n" + t(lang, "credits_left", n=db.get_credits(c.from_user.id))
    if db.is_subscribed(c.from_user.id):
        until = db.sub_until(c.from_user.id).date().isoformat()
        text += "\n" + t(lang, "sub_active", until=until)
    await c.message.edit_text(text, reply_markup=back_menu(lang))
    await c.answer()


@dp.callback_query(F.data == "buy")
async def on_buy(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    await c.message.edit_text(t(lang, "buy_title"), reply_markup=buy_menu(lang))
    await c.answer()


@dp.callback_query(F.data.startswith("pkg:"))
async def on_pkg(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    _, n, stars = c.data.split(":")
    n, stars = int(n), int(stars)
    # Telegram Stars: валюта "XTR", provider_token бос жол, баға = жұлдыз саны.
    await c.message.answer_invoice(
        title=t(lang, "invoice_title", n=n),
        description=t(lang, "invoice_desc", n=n),
        payload="credits:%d" % n,
        currency="XTR",
        provider_token="",
        prices=[LabeledPrice(label=t(lang, "pkg_label", n=n, stars=stars), amount=stars)],
    )
    await c.answer()


@dp.callback_query(F.data.startswith("sub:"))
async def on_sub(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    days = int(c.data.split(":", 1)[1])
    stars = dict(config.SUBSCRIPTIONS).get(days)
    if not stars:
        await c.answer()
        return
    name = sub_name(lang, days)
    await c.message.answer_invoice(
        title=t(lang, "sub_invoice_title", name=name),
        description=t(lang, "sub_invoice_desc", name=name),
        payload="sub:%d" % days,
        currency="XTR",
        provider_token="",
        prices=[LabeledPrice(label=name, amount=stars)],
    )
    await c.answer()


@dp.pre_checkout_query()
async def on_pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def on_paid(m: Message):
    lang = db.get_lang(m.from_user.id)
    payload = m.successful_payment.invoice_payload
    if payload.startswith("sub:"):
        days = int(payload.split(":", 1)[1])
        db.add_sub(m.from_user.id, days)
        await m.answer(t(lang, "pay_success_sub", name=sub_name(lang, days)),
                       reply_markup=main_menu(lang))
        return
    n = int(payload.split(":", 1)[1]) if payload.startswith("credits:") else 0
    db.add_credits(m.from_user.id, n)
    await m.answer(t(lang, "pay_success", n=n), reply_markup=main_menu(lang))


@dp.callback_query(F.data.startswith("m:"))
async def on_mode(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    uid = c.from_user.id
    mode = c.data.split(":", 1)[1]
    user_mode[uid] = mode
    # Жаңа режим — ескі аралық деректерді тазалаймыз.
    animate_video.pop(uid, None)
    combine_images.pop(uid, None)
    combine_prompt.pop(uid, None)
    ask = {
        "image": "ask_prompt_image",
        "combine": "ask_combine",
        "animate": "ask_animate_video",
    }[mode]
    await c.message.edit_text(t(lang, ask), reply_markup=back_menu(lang))
    await c.answer()


@dp.message(F.text & ~F.text.startswith("/"))
async def on_text(m: Message):
    lang = db.get_lang(m.from_user.id)
    uid = m.from_user.id
    mode = user_mode.get(uid)
    if mode == "image":
        await run_generation(m, lang, "image", prompt=m.text.strip())
    elif mode == "combine":
        combine_prompt[uid] = m.text.strip()  # қосымша нұсқау (міндетті емес)
        await m.answer(t(lang, "combine_got_prompt"), reply_markup=combine_menu(lang))
    else:
        await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))


@dp.message(F.photo)
async def on_photo(m: Message):
    lang = db.get_lang(m.from_user.id)
    uid = m.from_user.id
    mode = user_mode.get(uid)
    buf = await m.bot.download(m.photo[-1].file_id)
    if mode == "animate":
        # 2/2 қадам: видео бұрын келген — енді осы суретті жандандырамыз.
        vid = animate_video.get(uid)
        if not vid:
            await m.answer(t(lang, "ask_animate_video"), reply_markup=back_menu(lang))
            return
        animate_video.pop(uid, None)
        await run_generation(m, lang, "animate", image_bytes=buf.read(), video_bytes=vid)
        return
    if mode == "combine":
        imgs = combine_images.setdefault(uid, [])
        imgs.append(buf.read())
        await m.answer(t(lang, "combine_count", n=len(imgs)),
                       reply_markup=combine_menu(lang))
        return
    await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))


@dp.callback_query(F.data == "combine_go")
async def on_combine_go(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    uid = c.from_user.id
    imgs = combine_images.get(uid, [])
    if len(imgs) < 2:
        await c.answer(t(lang, "combine_need_more"), show_alert=True)
        return
    await c.answer()
    prompt = combine_prompt.pop(uid, None)
    combine_images.pop(uid, None)
    await run_generation(c.message, lang, "combine", images=imgs[:3],
                         prompt=prompt, uid=uid)


@dp.message(F.video | F.animation | F.video_note | F.document)
async def on_video(m: Message):
    lang = db.get_lang(m.from_user.id)
    uid = m.from_user.id
    if user_mode.get(uid) != "animate":
        await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))
        return
    media = m.video or m.animation or m.video_note or m.document
    try:
        buf = await m.bot.download(media.file_id)
    except Exception:  # noqa: BLE001 — Telegram боты 20 МБ-тан үлкен файлды жүктей алмайды
        await m.answer(t(lang, "video_too_big"), reply_markup=main_menu(lang))
        return
    # 1/2 қадам: видеоны сақтап, енді суретті сұраймыз.
    animate_video[uid] = buf.read()
    await m.answer(t(lang, "ask_animate_photo"), reply_markup=back_menu(lang))


@dp.message(F.text.startswith("/"))
async def on_unknown_cmd(m: Message):
    lang = db.get_lang(m.from_user.id)
    await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))


# ─────────────── видеоның дыбысын нәтижеге қосу (ffmpeg) ───────────────
async def mux_audio(video_url, driving_bytes):
    """Анимация шығысына (дыбыссыз) үлгі видеоның дыбысын/дауысын қосады.
    Сәтсіз болса None қайтарады (сонда дыбыссыз нұсқа жіберіледі)."""
    import subprocess
    import tempfile
    try:
        import aiohttp
        import imageio_ffmpeg
        async with aiohttp.ClientSession() as s:
            async with s.get(video_url, timeout=aiohttp.ClientTimeout(total=180)) as r:
                out_video = await r.read()
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory() as d:
            vp, ap, op = d + "/v.mp4", d + "/a.src", d + "/out.mp4"
            with open(vp, "wb") as f:
                f.write(out_video)
            with open(ap, "wb") as f:
                f.write(driving_bytes)
            cmd = [ff, "-y", "-i", vp, "-i", ap,
                   "-map", "0:v:0", "-map", "1:a:0?",
                   "-c:v", "copy", "-c:a", "aac", "-shortest", op]
            proc = await asyncio.to_thread(
                subprocess.run, cmd, capture_output=True, timeout=120)
            if proc.returncode != 0:
                log.warning("ffmpeg mux сәтсіз: %s", proc.stderr[-300:])
                return None
            with open(op, "rb") as f:
                return f.read()
    except Exception as e:  # noqa: BLE001
        log.warning("mux_audio қатесі: %s", e)
        return None


# ─────────────────────────── генерация ───────────────────────────
async def run_generation(m: Message, lang, mode, prompt=None, image_bytes=None,
                         video_bytes=None, images=None, uid=None):
    if uid is None:
        uid = m.from_user.id
    # charge: нәтиже сәтті болғанда нені есептейміз — "credit" | "limit" | None
    charge = None
    if mode in PAID_MODES:
        # Ақылы режим: тек сатып алынған кредитпен (тегін/шексіз емес) → зиянсыз.
        if db.get_credits(uid) <= 0:
            await m.answer(t(lang, "need_credit"), reply_markup=limit_menu(lang))
            return
        charge = "credit"
    elif db.is_subscribed(uid):
        charge = None  # жазылым = шексіз сурет
    else:
        ok, used, limit = db.can_use(uid, mode)
        if not ok:
            await m.answer(t(lang, "limit_hit", mode=mode, used=used, limit=limit),
                           reply_markup=limit_menu(lang))
            return
        charge = "limit"

    status = await m.answer(t(lang, "working"))
    try:
        res = await provider.generate(
            mode, prompt=prompt, image_bytes=image_bytes,
            video_bytes=video_bytes, images=images)
    except Exception as e:  # noqa: BLE001
        log.exception("generation failed: %s", e)
        await status.edit_text(t(lang, "error"), reply_markup=main_menu(lang))
        return

    # Тегін режимде видео/жаңарту/аватар нақты AI кілтін қажет етеді.
    if res.note == "needs_token":
        await status.edit_text(t(lang, "needs_token"), reply_markup=main_menu(lang))
        return

    # Нәтиже сәтті — енді ғана есептейміз (needs_token болса бұған жетпейді).
    if charge == "credit":
        db.use_credit(uid)
    elif charge == "limit":
        db.record_use(uid, mode)
    caption = t(lang, "done")
    if res.note == "demo":
        caption += "\n" + t(lang, "demo_note")

    try:
        if res.kind == "video":
            # Жандандыруда үлгі видеоның дыбысын/дауысын нәтижеге қосамыз.
            final = await mux_audio(res.url, video_bytes) if (mode == "animate" and video_bytes) else None
            if final:
                await m.answer_video(BufferedInputFile(final, "result.mp4"), caption=caption)
            else:
                await m.answer_video(res.url, caption=caption)
        elif len(res.urls) > 1:
            # Бірнеше сурет нұсқасы — қатар (альбоммен) жіберіледі.
            media = [InputMediaPhoto(media=u) for u in res.urls]
            media[0].caption = caption
            await m.answer_media_group(media)
        else:
            await m.answer_photo(res.url, caption=caption)
        await status.delete()
    except Exception:  # noqa: BLE001
        # Кейбір сілтемелерді Telegram тікелей жүктей алмауы мүмкін — мәтінмен береміз.
        await status.edit_text("%s\n%s" % (caption, res.url), reply_markup=main_menu(lang))

    await m.answer("👇", reply_markup=main_menu(lang))


# ─────────────────── денсаулық тексеру (Render/keep-alive) ───────────────────
async def _health(_req):
    return web.Response(text="ok")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.PORT)
    await site.start()
    log.info("health server on :%d", config.PORT)


async def keep_awake():
    """Render тегін серверін ұйықтатпау үшін өзін-өзі ~10 минут сайын «оятады»
    (өз публик URL-іне сұраныс жібереді → inbound трафик → ұйықтамайды)."""
    url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if not url:
        log.info("keep-alive өшік (RENDER_EXTERNAL_URL жоқ)")
        return
    import aiohttp
    while True:
        await asyncio.sleep(600)  # 10 минут
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                    await r.read()
            log.info("keep-alive ping → %s", url)
        except Exception as e:  # noqa: BLE001
            log.warning("keep-alive ping сәтсіз: %s", e)


async def main():
    if not config.BOT_TOKEN:
        sys.exit("BOT_TOKEN орнатылмаған. @BotFather-дан токен алып, env-ке қойыңыз.")
    if not config.REPLICATE_API_TOKEN:
        log.warning("REPLICATE_API_TOKEN жоқ — ДЕМО режимде жұмыс істейді.")
    bot = Bot(config.BOT_TOKEN)
    await start_health_server()
    asyncio.create_task(keep_awake())  # ұйықтап қалмау үшін
    log.info("bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
