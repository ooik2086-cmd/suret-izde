# -*- coding: utf-8 -*-
"""Тест оқшаулауы: бұл пакеттің config/db/i18n модульдері басқа боттың
аттас модульдерімен қақтығыспасын (түбірден `pytest` бәрін бірге жүгіртеді)."""
import os
import sys

import pytest

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SHARED = ("config", "db", "i18n", "providers", "states", "bot")


@pytest.fixture(autouse=True)
def _isolate_package_modules():
    for name in _SHARED:
        sys.modules.pop(name, None)
    sys.path.insert(0, PKG)
    yield
