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
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

PROMPT_MODES = {"image", "video"}   # мәтін сұрайтын режимдер
PHOTO_MODES = {"restore", "avatar"}  # фото сұрайтын режимдер

provider = get_provider()


# ─────────────────────────── пернетақталар ───────────────────────────
def main_menu(lang):
    rows = [
        [InlineKeyboardButton(text=t(lang, "menu_image"), callback_data="m:image")],
    ]
    if not config.DISABLE_VIDEO:
        rows.append([InlineKeyboardButton(text=t(lang, "menu_video"), callback_data="m:video")])
    rows += [
        [InlineKeyboardButton(text=t(lang, "menu_restore"), callback_data="m:restore")],
        [InlineKeyboardButton(text=t(lang, "menu_avatar"), callback_data="m:avatar")],
        [InlineKeyboardButton(text=t(lang, "menu_buy"), callback_data="buy")],
        [
            InlineKeyboardButton(text=t(lang, "menu_balance"), callback_data="balance"),
            InlineKeyboardButton(text=t(lang, "menu_lang"), callback_data="lang"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def buy_menu(lang):
    rows = [
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
    text = t(lang, "balance", image=s["image"], video=s["video"],
             restore=s["restore"], avatar=s["avatar"])
    text += "\n" + t(lang, "credits_left", n=db.get_credits(c.from_user.id))
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


@dp.pre_checkout_query()
async def on_pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def on_paid(m: Message):
    lang = db.get_lang(m.from_user.id)
    payload = m.successful_payment.invoice_payload
    n = int(payload.split(":", 1)[1]) if payload.startswith("credits:") else 0
    db.add_credits(m.from_user.id, n)
    await m.answer(t(lang, "pay_success", n=n), reply_markup=main_menu(lang))


@dp.callback_query(F.data.startswith("m:"))
async def on_mode(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    mode = c.data.split(":", 1)[1]
    if mode == "video" and config.DISABLE_VIDEO:
        await c.answer(t(lang, "video_disabled"), show_alert=True)
        return
    user_mode[c.from_user.id] = mode
    ask = {
        "image": "ask_prompt_image", "video": "ask_prompt_video",
        "restore": "ask_photo_restore", "avatar": "ask_photo_avatar",
    }[mode]
    await c.message.edit_text(t(lang, ask), reply_markup=back_menu(lang))
    await c.answer()


@dp.message(F.text & ~F.text.startswith("/"))
async def on_text(m: Message):
    lang = db.get_lang(m.from_user.id)
    mode = user_mode.get(m.from_user.id)
    if mode not in PROMPT_MODES:
        await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))
        return
    await run_generation(m, lang, mode, prompt=m.text.strip())


@dp.message(F.photo)
async def on_photo(m: Message):
    lang = db.get_lang(m.from_user.id)
    mode = user_mode.get(m.from_user.id)
    if mode not in PHOTO_MODES:
        await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))
        return
    buf = await m.bot.download(m.photo[-1].file_id)
    await run_generation(m, lang, mode, image_bytes=buf.read())


@dp.message(F.text.startswith("/"))
async def on_unknown_cmd(m: Message):
    lang = db.get_lang(m.from_user.id)
    await m.answer(t(lang, "need_pick_mode"), reply_markup=main_menu(lang))


# ─────────────────────────── генерация ───────────────────────────
async def run_generation(m: Message, lang, mode, prompt=None, image_bytes=None):
    uid = m.from_user.id
    ok, used, limit = db.can_use(uid, mode)
    use_paid = False
    if not ok:
        if db.get_credits(uid) > 0:
            use_paid = True  # тегін лимит бітті — төленген кредиттен аламыз
        else:
            await m.answer(t(lang, "limit_hit", mode=mode, used=used, limit=limit),
                           reply_markup=limit_menu(lang))
            return

    status = await m.answer(t(lang, "working"))
    try:
        res = await provider.generate(mode, prompt=prompt, image_bytes=image_bytes)
    except Exception as e:  # noqa: BLE001
        log.exception("generation failed: %s", e)
        await status.edit_text(t(lang, "error"), reply_markup=main_menu(lang))
        return

    # Тегін режимде видео/жаңарту/аватар нақты AI кілтін қажет етеді.
    if res.note == "needs_token":
        await status.edit_text(t(lang, "needs_token"), reply_markup=main_menu(lang))
        return

    # Нәтиже сәтті — енді ғана есептейміз (кредит немесе тегін лимит).
    if use_paid:
        db.use_credit(uid)
    else:
        db.record_use(uid, mode)
    caption = t(lang, "done")
    if res.note == "demo":
        caption += "\n" + t(lang, "demo_note")

    try:
        if res.kind == "video":
            await m.answer_video(res.url, caption=caption)
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


async def main():
    if not config.BOT_TOKEN:
        sys.exit("BOT_TOKEN орнатылмаған. @BotFather-дан токен алып, env-ке қойыңыз.")
    if not config.REPLICATE_API_TOKEN:
        log.warning("REPLICATE_API_TOKEN жоқ — ДЕМО режимде жұмыс істейді.")
    bot = Bot(config.BOT_TOKEN)
    await start_health_server()
    log.info("bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
