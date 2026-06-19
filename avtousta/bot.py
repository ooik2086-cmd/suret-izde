# -*- coding: utf-8 -*-
"""AvtoUsta — авто шеберлерін табатын маркетплейс боты (aiogram v3).

Екі бөлек рөл: 🙋 Клиент (көлік иесі) және 🛠 Шебер/СТО — әрқайсысы өз
тіркелуімен, профилімен, мәзірімен. 1-кезең: рөл + тіркелу + іздеу.

Іске қосу (жергілікті):
    export BOT_TOKEN=...   # @BotFather-дан
    python bot.py
"""

import asyncio
import logging
import os
import re
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiohttp import web

import config
import db
from i18n import t
from states import ClientReg, MasterReg, Search

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("avtousta")

dp = Dispatcher(storage=MemoryStorage())


# ─────────────────────────── көмекшілер ───────────────────────────
def _md(s):
    """Markdown-ды бұзатын белгілерді пайдаланушы мәтінінен алып тастау."""
    return re.sub(r"[*_`\[\]]", "", str(s or "")).strip()


async def ans(msg, text, kb=None):
    await msg.answer(text, reply_markup=kb, parse_mode="Markdown")


async def edit(c, text, kb=None):
    try:
        await c.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:  # noqa: BLE001 — мазмұн өзгермесе/өшсе, жаңасын жібереміз
        await c.message.answer(text, reply_markup=kb, parse_mode="Markdown")


# ─────────────────────────── пернетақталар ───────────────────────────
def lang_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="setlang:kz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru")],
    ])


def role_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "role_client"), callback_data="role:client")],
        [InlineKeyboardButton(text=t(lang, "role_master"), callback_data="role:master")],
    ])


def mtype_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=config.mtype_label(lang, k), callback_data="mt:" + k)]
        for k in config.MASTER_TYPE_KEYS
    ])


def cats_menu(lang, selected):
    rows, row = [], []
    for key, emoji, kz, ru in config.CATEGORIES:
        mark = "✅ " if key in selected else ""
        label = "%s%s %s" % (mark, emoji, kz if lang == "kz" else ru)
        row.append(InlineKeyboardButton(text=label, callback_data="c:" + key))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t(lang, "cats_done"), callback_data="cats_ok")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def about_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "skip"), callback_data="about_skip")],
    ])


def phone_kb(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "share_phone"), request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True)


def client_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "m_search"), callback_data="cl:search")],
        [InlineKeyboardButton(text=t(lang, "m_roadside"), callback_data="cl:roadside")],
        [InlineKeyboardButton(text=t(lang, "m_request"), callback_data="cl:request")],
        [InlineKeyboardButton(text=t(lang, "m_my_requests"), callback_data="cl:myreq")],
        [
            InlineKeyboardButton(text=t(lang, "m_profile"), callback_data="profile"),
            InlineKeyboardButton(text=t(lang, "m_lang"), callback_data="lang"),
        ],
        [InlineKeyboardButton(text=t(lang, "m_switch"), callback_data="switch")],
    ])


def master_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "m_orders"), callback_data="ma:orders")],
        [InlineKeyboardButton(text=t(lang, "m_jobs"), callback_data="ma:jobs")],
        [InlineKeyboardButton(text=t(lang, "m_rating"), callback_data="ma:rating")],
        [
            InlineKeyboardButton(text=t(lang, "m_promote"), callback_data="ma:promote"),
            InlineKeyboardButton(text=t(lang, "m_sub"), callback_data="ma:sub"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "m_profile"), callback_data="profile"),
            InlineKeyboardButton(text=t(lang, "m_lang"), callback_data="lang"),
        ],
        [InlineKeyboardButton(text=t(lang, "m_switch"), callback_data="switch")],
    ])


def back_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")],
    ])


def search_cat_menu(lang):
    rows, row = [], []
    for key, emoji, kz, ru in config.CATEGORIES:
        label = "%s %s" % (emoji, kz if lang == "kz" else ru)
        row.append(InlineKeyboardButton(text=label, callback_data="sc:" + key))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=t(lang, "cat_any"), callback_data="sc:any")])
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_city_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "search_my_city"), callback_data="smc")],
        [InlineKeyboardButton(text=t(lang, "back"), callback_data="menu")],
    ])


# ─────────────────────────── негізгі мәзір ───────────────────────────
async def show_main(uid, msg=None, c=None):
    role = db.get_role(uid)
    lang = db.get_lang(uid)
    if role == config.ROLE_MASTER:
        title, kb = t(lang, "menu_master_title"), master_menu(lang)
    else:
        title, kb = t(lang, "menu_client_title"), client_menu(lang)
    if c is not None:
        await edit(c, title, kb)
    else:
        await ans(msg, title, kb)


# ─────────────────────────── /start ───────────────────────────
@dp.message(CommandStart())
async def on_start(m: Message, state: FSMContext):
    await state.clear()
    uid = m.from_user.id
    if db.is_registered(uid):
        await show_main(uid, msg=m)
        return
    if db.get_user(uid):  # тілі бар, рөлі жоқ → рөл сұраймыз
        lang = db.get_lang(uid)
        await ans(m, t(lang, "start_pick_role"), role_menu(lang))
    else:  # жаңа адам → алдымен тіл
        await ans(m, t(config.DEFAULT_LANG, "choose_lang"), lang_menu())


@dp.message(Command("cancel"))
async def on_cancel(m: Message, state: FSMContext):
    await state.clear()
    lang = db.get_lang(m.from_user.id)
    await ans(m, t(lang, "cancelled"))
    if db.is_registered(m.from_user.id):
        await show_main(m.from_user.id, msg=m)


# ─────────────────────────── тіл ───────────────────────────
@dp.callback_query(F.data == "lang")
async def on_lang(c: CallbackQuery):
    await edit(c, t(db.get_lang(c.from_user.id), "choose_lang"), lang_menu())
    await c.answer()


@dp.callback_query(F.data.startswith("setlang:"))
async def on_setlang(c: CallbackQuery):
    lang = c.data.split(":", 1)[1]
    db.set_lang(c.from_user.id, lang)
    if db.is_registered(c.from_user.id):
        await show_main(c.from_user.id, c=c)
    else:
        await edit(c, t(lang, "start_pick_role"), role_menu(lang))
    await c.answer()


# ─────────────────────────── рөл таңдау ───────────────────────────
@dp.callback_query(F.data == "switch")
async def on_switch(c: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = db.get_lang(c.from_user.id)
    await edit(c, t(lang, "start_pick_role"), role_menu(lang))
    await c.answer()


@dp.callback_query(F.data == "role:client")
async def on_role_client(c: CallbackQuery, state: FSMContext):
    lang = db.get_lang(c.from_user.id)
    await state.set_state(ClientReg.name)
    await edit(c, t(lang, "ask_name_client"))
    await c.answer()


@dp.callback_query(F.data == "role:master")
async def on_role_master(c: CallbackQuery, state: FSMContext):
    lang = db.get_lang(c.from_user.id)
    await state.set_state(MasterReg.name)
    await edit(c, t(lang, "ask_name_master"))
    await c.answer()


# ─────────────────────────── клиент тіркелуі ───────────────────────────
@dp.message(ClientReg.name)
async def reg_client_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip())
    await state.set_state(ClientReg.city)
    await ans(m, t(db.get_lang(m.from_user.id), "ask_city"))


@dp.message(ClientReg.city)
async def reg_client_city(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = db.get_lang(m.from_user.id)
    db.register_client(m.from_user.id, data.get("name", ""), m.text.strip(), lang)
    await state.clear()
    await ans(m, t(lang, "reg_client_done"))
    await show_main(m.from_user.id, msg=m)


# ─────────────────────────── шебер тіркелуі ───────────────────────────
@dp.message(MasterReg.name)
async def reg_master_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip())
    await state.set_state(MasterReg.city)
    await ans(m, t(db.get_lang(m.from_user.id), "ask_city"))


@dp.message(MasterReg.city)
async def reg_master_city(m: Message, state: FSMContext):
    await state.update_data(city=m.text.strip())
    await state.set_state(MasterReg.phone)
    lang = db.get_lang(m.from_user.id)
    await ans(m, t(lang, "ask_phone"), phone_kb(lang))


@dp.message(MasterReg.phone)
async def reg_master_phone(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else (m.text or "").strip()
    await state.update_data(phone=phone, cats=[])
    await state.set_state(MasterReg.mtype)
    lang = db.get_lang(m.from_user.id)
    await m.answer("📞 ✅", reply_markup=ReplyKeyboardRemove())
    await ans(m, t(lang, "ask_mtype"), mtype_menu(lang))


@dp.callback_query(MasterReg.mtype, F.data.startswith("mt:"))
async def reg_master_mtype(c: CallbackQuery, state: FSMContext):
    await state.update_data(mtype=c.data.split(":", 1)[1])
    await state.set_state(MasterReg.cats)
    lang = db.get_lang(c.from_user.id)
    await edit(c, t(lang, "ask_cats"), cats_menu(lang, set()))
    await c.answer()


@dp.callback_query(MasterReg.cats, F.data.startswith("c:"))
async def reg_master_cat_toggle(c: CallbackQuery, state: FSMContext):
    key = c.data.split(":", 1)[1]
    data = await state.get_data()
    cats = set(data.get("cats", []))
    cats.symmetric_difference_update({key})
    await state.update_data(cats=list(cats))
    lang = db.get_lang(c.from_user.id)
    try:
        await c.message.edit_reply_markup(reply_markup=cats_menu(lang, cats))
    except Exception:  # noqa: BLE001
        pass
    await c.answer()


@dp.callback_query(MasterReg.cats, F.data == "cats_ok")
async def reg_master_cats_done(c: CallbackQuery, state: FSMContext):
    lang = db.get_lang(c.from_user.id)
    data = await state.get_data()
    if not data.get("cats"):
        await c.answer(t(lang, "cats_need_one"), show_alert=True)
        return
    await state.set_state(MasterReg.about)
    await edit(c, t(lang, "ask_about"), about_menu(lang))
    await c.answer()


async def _finish_master(m_or_c, uid, state, about):
    data = await state.get_data()
    lang = db.get_lang(uid)
    db.register_master(uid, data.get("name", ""), data.get("city", ""),
                       data.get("phone", ""), data.get("mtype", ""), about,
                       data.get("cats", []), lang)
    await state.clear()
    bot = m_or_c.bot
    msg = await bot.send_message(uid, t(lang, "reg_master_done"), parse_mode="Markdown")
    await show_main(uid, msg=msg)
    # Әкімшіге жаңа шебер туралы хабар (міндетті емес).
    if config.ADMIN_ID:
        try:
            await bot.send_message(
                config.ADMIN_ID,
                "🆕 Жаңа шебер: %s (%s), id=%d" % (
                    _md(data.get("name", "")), _md(data.get("city", "")), uid))
        except Exception:  # noqa: BLE001
            pass


@dp.message(MasterReg.about)
async def reg_master_about_text(m: Message, state: FSMContext):
    await _finish_master(m, m.from_user.id, state, m.text.strip())


@dp.callback_query(MasterReg.about, F.data == "about_skip")
async def reg_master_about_skip(c: CallbackQuery, state: FSMContext):
    await c.answer()
    await _finish_master(c, c.from_user.id, state, "")


# ─────────────────────────── негізгі мәзірге қайту ───────────────────────────
@dp.callback_query(F.data == "menu")
async def on_menu(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main(c.from_user.id, c=c)
    await c.answer()


# ─────────────────────────── профиль ───────────────────────────
@dp.callback_query(F.data == "profile")
async def on_profile(c: CallbackQuery):
    uid = c.from_user.id
    lang = db.get_lang(uid)
    if db.get_role(uid) == config.ROLE_MASTER:
        d = db.get_master(uid)
        await edit(c, master_card(lang, d), back_menu(lang))
    else:
        u = db.get_user(uid) or {}
        await edit(c, t(lang, "profile_client", name=_md(u.get("name", "")),
                        city=_md(u.get("city", ""))), back_menu(lang))
    await c.answer()


# ─────────────────────────── шебер мәзірінің тармақтары ───────────────────────────
@dp.callback_query(F.data == "ma:rating")
async def on_rating(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    d = db.get_master(c.from_user.id)
    rating = d["rating"] if d and d["rating_cnt"] else 0
    cnt = d["rating_cnt"] if d else 0
    await edit(c, t(lang, "rating_view", rating=rating, cnt=cnt), back_menu(lang))
    await c.answer()


@dp.callback_query(F.data == "ma:promote")
async def on_promote(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    await edit(c, t(lang, "promote_info"), back_menu(lang))
    await c.answer()


@dp.callback_query(F.data == "ma:sub")
async def on_sub(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    await edit(c, t(lang, "sub_info"), back_menu(lang))
    await c.answer()


@dp.callback_query(F.data.in_({"ma:orders", "ma:jobs", "cl:request", "cl:myreq"}))
async def on_soon(c: CallbackQuery):
    lang = db.get_lang(c.from_user.id)
    await edit(c, t(lang, "soon"), back_menu(lang))
    await c.answer()


# ─────────────────────────── іздеу (клиент) ───────────────────────────
def master_card(lang, d):
    if not d:
        return "—"
    badge = (t(lang, "w_verified") + "\n") if d.get("verified") else ""
    if d["rating_cnt"]:
        rating = "%s ⭐ (%d %s)" % (d["rating"], d["rating_cnt"], t(lang, "w_reviews"))
    else:
        rating = "⭐ %s" % t(lang, "w_new")
    cats = ", ".join(config.cat_label(lang, x) for x in d.get("cats", [])) or "—"
    about = ("\n📝 " + _md(d["about"])) if d.get("about") else ""
    return ("👨‍🔧 *%s*\n%s📍 %s · %s\n🛠 %s\n%s\n📞 %s%s" % (
        _md(d["name"]), badge, _md(d["city"]),
        config.mtype_label(lang, d.get("mtype", "")), cats, rating,
        _md(d.get("phone", "")), about))


async def do_search(target, lang, cat, city, header=None):
    results = db.search_masters(city=city, cat=(None if cat in (None, "any") else cat))
    if not results:
        await ans(target, t(lang, "search_none"), back_menu(lang))
        return
    await ans(target, header or t(lang, "search_header", n=len(results)))
    for d in results[:config.SEARCH_PAGE_SIZE]:
        await ans(target, master_card(lang, d))
    await ans(target, "👇", client_menu(lang))


@dp.callback_query(F.data == "cl:search")
async def on_search(c: CallbackQuery, state: FSMContext):
    lang = db.get_lang(c.from_user.id)
    await state.set_state(Search.cat)
    await edit(c, t(lang, "search_pick_cat"), search_cat_menu(lang))
    await c.answer()


@dp.callback_query(Search.cat, F.data.startswith("sc:"))
async def on_search_cat(c: CallbackQuery, state: FSMContext):
    await state.update_data(cat=c.data.split(":", 1)[1])
    await state.set_state(Search.city)
    lang = db.get_lang(c.from_user.id)
    await edit(c, t(lang, "search_pick_city"), search_city_menu(lang))
    await c.answer()


@dp.callback_query(Search.city, F.data == "smc")
async def on_search_my_city(c: CallbackQuery, state: FSMContext):
    uid = c.from_user.id
    lang = db.get_lang(uid)
    city = (db.get_user(uid) or {}).get("city") or ""
    data = await state.get_data()
    await state.clear()
    await c.answer()
    await do_search(c.message, lang, data.get("cat"), city)


@dp.message(Search.city)
async def on_search_city_text(m: Message, state: FSMContext):
    uid = m.from_user.id
    lang = db.get_lang(uid)
    city = m.text.strip()
    data = await state.get_data()
    await state.clear()
    await do_search(m, lang, data.get("cat"), city)


# ─────────────────────────── жолдағы көмек (клиент) ───────────────────────────
@dp.callback_query(F.data == "cl:roadside")
async def on_roadside(c: CallbackQuery, state: FSMContext):
    await state.clear()
    uid = c.from_user.id
    lang = db.get_lang(uid)
    city = (db.get_user(uid) or {}).get("city") or ""
    await c.answer()
    await do_search(c.message, lang, "any", city,
                    header=t(lang, "roadside_header", city=_md(city)))


# ─────────────────────────── күтілмеген хабар ───────────────────────────
@dp.message()
async def on_any(m: Message):
    uid = m.from_user.id
    lang = db.get_lang(uid)
    if db.is_registered(uid):
        await show_main(uid, msg=m)
    else:
        await ans(m, t(lang, "not_registered"))


# ─────────────────── денсаулық тексеру (Render/keep-alive) ───────────────────
async def _health(_req):
    return web.Response(text="ok")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", config.PORT).start()
    log.info("health server on :%d", config.PORT)


async def keep_awake():
    url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if not url:
        return
    import aiohttp
    while True:
        await asyncio.sleep(600)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                    await r.read()
        except Exception as e:  # noqa: BLE001
            log.warning("keep-alive ping сәтсіз: %s", e)


async def main():
    if not config.BOT_TOKEN:
        sys.exit("BOT_TOKEN орнатылмаған. @BotFather-дан токен алып, env-ке қойыңыз.")
    bot = Bot(config.BOT_TOKEN)
    await start_health_server()
    asyncio.create_task(keep_awake())
    log.info("AvtoUsta bot polling started (masters in DB: %d)", db.count_masters())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
