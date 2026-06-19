# -*- coding: utf-8 -*-
"""AvtoUsta — тіркелу мен іздеудің FSM күйлері (aiogram v3)."""

from aiogram.fsm.state import State, StatesGroup


class ClientReg(StatesGroup):
    """Клиент (көлік иесі) тіркелуі."""
    name = State()
    city = State()


class MasterReg(StatesGroup):
    """Шебер / СТО тіркелуі."""
    name = State()
    city = State()
    phone = State()
    mtype = State()
    cats = State()
    about = State()


class Search(StatesGroup):
    """Шебер іздеу (санат → қала)."""
    cat = State()
    city = State()
