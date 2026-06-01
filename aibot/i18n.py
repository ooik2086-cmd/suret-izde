# -*- coding: utf-8 -*-
"""Қазақша/орысша мәтіндер."""

MODES = ("image", "video", "restore", "avatar")

T = {
    "kz": {
        "lang_name": "🇰🇿 Қазақша",
        "choose_lang": "Тілді таңдаңыз / Выберите язык:",
        "welcome": (
            "👋 Сәлем! Мен — AI-генератор ботымын.\n\n"
            "Не істей аламын:\n"
            "🖼️ Мәтіннен сурет жасау (3 нұсқа)\n"
            "🧩 2-3 суретті біріктіру/өңдеу\n"
            "🎭 Суретті видеодағыдай жандандыру\n\n"
            "Қазақша/орысша жаза беріңіз — қалғанын өзім істеймін.\n"
            "Төмендегі батырмадан керегін таңдаңыз 👇"
        ),
        "menu_image": "🖼️ Сурет жасау",
        "menu_combine": "🧩 Суреттерді біріктіру",
        "menu_video": "🎬 Видео жасау",
        "menu_restore": "🪄 Фото жаңарту",
        "menu_avatar": "🧑‍💼 Аватар жасау",
        "menu_animate": "🎭 Суретті жандандыру",
        "ask_combine": "🧩 2-3 суретті бір-бірлеп жіберіңіз. Қаласаңыз нұсқау жазыңыз (мыс. «екеуін біріктір» немесе «1-шіні 2-шінің түрімен жаса»). Сосын «Біріктіру» басыңыз.",
        "combine_count": "✅ {n} сурет қабылданды. Тағы жіберіңіз немесе «Біріктіру» басыңыз.",
        "combine_got_prompt": "✍️ Нұсқау сақталды. Енді 2-3 сурет жіберіп, «Біріктіру» басыңыз.",
        "combine_need_more": "Кемінде 2 сурет керек.",
        "combine_btn": "🧩 Біріктіру",
        "menu_balance": "📊 Менің лимитім",
        "menu_lang": "🌐 Тіл",
        "ask_prompt_image": "✍️ Қандай сурет керек? Сипаттап жазыңыз (мысалы: «тауда тұрған ақ бөкен, күн батып барады»).",
        "ask_prompt_video": "✍️ Қандай видео керек? Сипаттаңыз (қысқа болсын).",
        "ask_photo_restore": "📷 Жаңартатын ескі/бұлыңғыр фотоны жіберіңіз.",
        "ask_photo_avatar": "📷 Бетіңіз анық көрінетін селфи жіберіңіз — кәсіби портрет жасаймын.",
        "ask_animate_photo": "🖼️ 2/2-қадам: енді суретіңізді жіберіңіз — суреттегі кейіпкер видеодағыдай қозғалады, билейді, мимика мен дыбыс сол қалпы қалады.",
        "ask_animate_video": "🎬 1/2-қадам: үлгі видеоны жіберіңіз (би/қозғалыс/сөйлеу). Видеоның дыбысы мен дауысы сол қалпы сақталады. (20 МБ-қа дейін)",
        "video_too_big": "⚠️ Видео тым үлкен. Telegram боты тек 20 МБ-қа дейін жүктей алады — қысқа/кішірек видео жіберіңіз.",
        "working": "⏳ Жасап жатырмын... біраз күте тұрыңыз (видео ұзағырақ).",
        "done": "✅ Дайын!",
        "limit_hit": "🚫 Бүгінгі тегін лимит бітті ({mode}: {used}/{limit}).\n\n💎 «Сатып алу» арқылы қосымша генерация алыңыз немесе ертең қайта көріңіз.",
        "balance": "📊 Бүгінгі қолдану:\n🖼️ Сурет: {image}\n🧩 Біріктіру: {combine}\n🎭 Жандандыру: {animate}",
        "send_text_not_photo": "Алдымен мәзірден қызметті таңдаңыз 👇 (/start)",
        "send_photo_please": "Мәтін емес, фото жіберіңіз 📷",
        "need_pick_mode": "Алдымен мәзірден не істейтінімізді таңдаңыз 👇",
        "error": "⚠️ Қате шықты, кейінірек қайталап көріңіз.",
        "video_disabled": "🎬 Видео уақытша өшірулі.",
        "demo_note": "⚙️ (Демо режим: нақты AI әлі қосылмаған. REPLICATE_API_TOKEN қосыңыз.)",
        "needs_token": "🔒 Бұл режим нақты AI кілтін қажет етеді. Қазір тегін режимде тек сурет жасау істейді (🖼️).",
        "menu_buy": "💎 Сатып алу",
        "buy_title": "💎 Таңдаңыз (төлем Telegram Stars):\n• Жазылым — ШЕКСІЗ сурет\n• Кредит — видео/жандандыру/аватар (1 кредит = 1 жасау)",
        "sub_week": "📅 1 апта",
        "sub_month": "📆 1 ай",
        "sub_invoice_title": "{name} жазылым",
        "sub_invoice_desc": "{name} ішінде ШЕКСІЗ сурет жасау.",
        "pay_success_sub": "✅ Төлем сәтті! {name} жазылым қосылды — енді шексіз сурет жасаңыз! 🎉",
        "sub_active": "💎 Жазылым белсенді: {until} дейін",
        "need_credit": "🔒 Бұл — ақылы мүмкіндік (видео/жандандыру/аватар/жаңарту).\n«💎 Сатып алу» арқылы кредит алыңыз (1 кредит = 1 жасау).",
        "pkg_label": "{n} генерация — {stars} ⭐",
        "invoice_title": "{n} генерация",
        "invoice_desc": "{n} ақылы кредит (видео / жандандыру / аватар / фото жаңарту). 1 кредит = 1 жасау.",
        "credits_left": "💎 Төленген генерация: {n}",
        "pay_success": "✅ Төлем сәтті! +{n} генерация қосылды. Рақмет! 🎉",
        "back": "⬅️ Мәзір",
    },
    "ru": {
        "lang_name": "🇷🇺 Русский",
        "choose_lang": "Тілді таңдаңыз / Выберите язык:",
        "welcome": (
            "👋 Привет! Я — бот AI-генератор.\n\n"
            "Что умею:\n"
            "🖼️ Создавать изображения по тексту (3 варианта)\n"
            "🧩 Объединять/редактировать 2-3 фото\n"
            "🎭 Оживлять фото как в видео\n\n"
            "Пишите на казахском/русском — остальное сделаю сам.\n"
            "Выберите нужное кнопкой ниже 👇"
        ),
        "menu_image": "🖼️ Сделать фото",
        "menu_combine": "🧩 Объединить фото",
        "menu_video": "🎬 Сделать видео",
        "menu_restore": "🪄 Восстановить фото",
        "menu_avatar": "🧑‍💼 Создать аватар",
        "menu_animate": "🎭 Оживить фото",
        "ask_combine": "🧩 Пришлите 2-3 фото по одному. По желанию напишите инструкцию (напр. «объедини оба» или «сделай 1-е в стиле 2-го»). Затем нажмите «Объединить».",
        "combine_count": "✅ Принято фото: {n}. Пришлите ещё или нажмите «Объединить».",
        "combine_got_prompt": "✍️ Инструкция сохранена. Теперь пришлите 2-3 фото и нажмите «Объединить».",
        "combine_need_more": "Нужно минимум 2 фото.",
        "combine_btn": "🧩 Объединить",
        "menu_balance": "📊 Мой лимит",
        "menu_lang": "🌐 Язык",
        "ask_prompt_image": "✍️ Какое изображение нужно? Опишите (например: «белая антилопа в горах на закате»).",
        "ask_prompt_video": "✍️ Какое видео нужно? Опишите (покороче).",
        "ask_photo_restore": "📷 Пришлите старое/размытое фото для восстановления.",
        "ask_photo_avatar": "📷 Пришлите селфи с чётким лицом — сделаю профессиональный портрет.",
        "ask_animate_photo": "🖼️ Шаг 2/2: теперь пришлите фото — персонаж на фото будет двигаться как в видео, со всей мимикой и звуком.",
        "ask_animate_video": "🎬 Шаг 1/2: пришлите видео-образец (танец/движение/речь). Звук и голос видео сохранятся как есть. (до 20 МБ)",
        "video_too_big": "⚠️ Видео слишком большое. Бот Telegram может загрузить только до 20 МБ — пришлите короче/меньше.",
        "working": "⏳ Генерирую... подождите немного (видео дольше).",
        "done": "✅ Готово!",
        "limit_hit": "🚫 Дневной бесплатный лимит исчерпан ({mode}: {used}/{limit}).\n\n💎 Нажмите «Купить», чтобы получить дополнительные генерации, или попробуйте завтра.",
        "balance": "📊 Сегодня использовано:\n🖼️ Фото: {image}\n🧩 Объединение: {combine}\n🎭 Оживление: {animate}",
        "send_text_not_photo": "Сначала выберите услугу в меню 👇 (/start)",
        "send_photo_please": "Пришлите фото, а не текст 📷",
        "need_pick_mode": "Сначала выберите в меню, что делаем 👇",
        "error": "⚠️ Произошла ошибка, попробуйте позже.",
        "video_disabled": "🎬 Видео временно отключено.",
        "demo_note": "⚙️ (Демо-режим: реальный AI ещё не подключён. Добавьте REPLICATE_API_TOKEN.)",
        "needs_token": "🔒 Этот режим требует реального AI-ключа. Сейчас в бесплатном режиме работает только генерация изображений (🖼️).",
        "menu_buy": "💎 Купить",
        "buy_title": "💎 Выберите (оплата через Telegram Stars):\n• Подписка — БЕЗЛИМИТ фото\n• Кредиты — видео/анимация/аватар (1 кредит = 1 генерация)",
        "sub_week": "📅 1 неделя",
        "sub_month": "📆 1 месяц",
        "sub_invoice_title": "Подписка {name}",
        "sub_invoice_desc": "Безлимитная генерация ФОТО на период «{name}».",
        "pay_success_sub": "✅ Оплата успешна! Подписка {name} активна — безлимитные фото! 🎉",
        "sub_active": "💎 Подписка активна до: {until}",
        "need_credit": "🔒 Это платная функция (видео/анимация/аватар/восстановление).\nНажмите «💎 Купить» и возьмите кредиты (1 кредит = 1 генерация).",
        "pkg_label": "{n} генераций — {stars} ⭐",
        "invoice_title": "{n} генераций",
        "invoice_desc": "{n} платных кредитов (видео / анимация / аватар / восстановление). 1 кредит = 1 генерация.",
        "credits_left": "💎 Оплаченных генераций: {n}",
        "pay_success": "✅ Оплата успешна! Добавлено +{n} генераций. Спасибо! 🎉",
        "back": "⬅️ Меню",
    },
    "en": {
        "lang_name": "🇬🇧 English",
        "choose_lang": "Тілді таңдаңыз / Выберите язык / Choose language:",
        "welcome": (
            "👋 Hi! I'm an AI generator bot.\n\n"
            "What I can do:\n"
            "🖼️ Create images from text (3 options)\n"
            "🧩 Combine/edit 2-3 photos\n"
            "🎭 Animate a photo like in a video\n\n"
            "Write in Kazakh/Russian — I'll do the rest.\n"
            "Pick what you need with a button below 👇"
        ),
        "menu_image": "🖼️ Make image",
        "menu_combine": "🧩 Combine photos",
        "menu_video": "🎬 Make video",
        "menu_restore": "🪄 Restore photo",
        "menu_avatar": "🧑‍💼 Create avatar",
        "menu_animate": "🎭 Animate photo",
        "ask_combine": "🧩 Send 2-3 photos one by one. Optionally add an instruction (e.g. 'combine both' or 'make the 1st in the style of the 2nd'). Then tap 'Combine'.",
        "combine_count": "✅ Photos received: {n}. Send more or tap 'Combine'.",
        "combine_got_prompt": "✍️ Instruction saved. Now send 2-3 photos and tap 'Combine'.",
        "combine_need_more": "At least 2 photos are needed.",
        "combine_btn": "🧩 Combine",
        "menu_balance": "📊 My limit",
        "menu_lang": "🌐 Language",
        "ask_prompt_image": "✍️ What image do you want? Describe it (e.g. 'a white antelope in the mountains at sunset').",
        "ask_prompt_video": "✍️ What video do you want? Describe it (keep it short).",
        "ask_photo_restore": "📷 Send the old/blurry photo to restore.",
        "ask_photo_avatar": "📷 Send a selfie with a clear face — I'll make a professional portrait.",
        "ask_animate_photo": "🖼️ Step 2/2: now send your photo — the character will move like in the video, with all the expressions and audio.",
        "ask_animate_video": "🎬 Step 1/2: send a reference video (dance/motion/speech). The video's sound and voice are kept as-is. (up to 20 MB)",
        "video_too_big": "⚠️ The video is too big. A Telegram bot can only download up to 20 MB — send a shorter/smaller one.",
        "working": "⏳ Working on it... please wait a bit (video takes longer).",
        "done": "✅ Done!",
        "limit_hit": "🚫 Today's free limit is used up ({mode}: {used}/{limit}).\n\n💎 Tap 'Buy' for extra generations, or try again tomorrow.",
        "balance": "📊 Used today:\n🖼️ Image: {image}\n🧩 Combine: {combine}\n🎭 Animate: {animate}",
        "send_text_not_photo": "First pick a service in the menu 👇 (/start)",
        "send_photo_please": "Send a photo, not text 📷",
        "need_pick_mode": "First choose what to do from the menu 👇",
        "error": "⚠️ Something went wrong, please try again later.",
        "video_disabled": "🎬 Video is temporarily disabled.",
        "demo_note": "⚙️ (Demo mode: real AI not connected yet. Add REPLICATE_API_TOKEN.)",
        "needs_token": "🔒 This mode needs a real AI key. In free mode only image generation works (🖼️).",
        "menu_buy": "💎 Buy",
        "buy_title": "💎 Choose (pay via Telegram Stars):\n• Subscription — UNLIMITED images\n• Credits — video/animation/avatar (1 credit = 1 generation)",
        "sub_week": "📅 1 week",
        "sub_month": "📆 1 month",
        "sub_invoice_title": "{name} subscription",
        "sub_invoice_desc": "Unlimited IMAGE generation for the '{name}' period.",
        "pay_success_sub": "✅ Payment successful! {name} subscription is active — unlimited images! 🎉",
        "sub_active": "💎 Subscription active until: {until}",
        "need_credit": "🔒 This is a paid feature (video/animation/avatar/restore).\nTap '💎 Buy' and get credits (1 credit = 1 generation).",
        "pkg_label": "{n} generations — {stars} ⭐",
        "invoice_title": "{n} generations",
        "invoice_desc": "{n} paid credits (video / animation / avatar / restore). 1 credit = 1 generation.",
        "credits_left": "💎 Paid generations: {n}",
        "pay_success": "✅ Payment successful! +{n} generations added. Thank you! 🎉",
        "back": "⬅️ Menu",
    },
}


def t(lang, key, **kw):
    d = T.get(lang) or T["kz"]
    s = d.get(key) or T["kz"].get(key) or key
    return s.format(**kw) if kw else s
