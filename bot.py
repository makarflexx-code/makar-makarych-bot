# -*- coding: utf-8 -*-
# Макар Макарыч — телеграм-бот БулкиПечь (OpenRouter edition)
# Устойчивый вариант для постоянной работы (VPS / Render / Linux / Windows)
# ---------------------------------------------------------------
# Требования:
#   pip install --upgrade python-telegram-bot openai
# ---------------------------------------------------------------

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger("БулкиПечь")

# === ПУТИ ===
BASE = Path(__file__).parent
MESSAGES_PATH = BASE / "messages.json"
PRICE_PATH = BASE / "price.json"
MEDIA_DIR = BASE / "media"

# === ЗАГРУЗКА ДАННЫХ ===
with open(MESSAGES_PATH, "r", encoding="utf-8") as f:
    MSG = json.load(f)

try:
    with open(PRICE_PATH, "r", encoding="utf-8") as f:
        PRICE: Dict[str, List[Dict[str, Any]]] = json.load(f)
except FileNotFoundError:
    PRICE = {}

# === МЕНЮ ===
MENU_BUTTONS = [
    ["Обучение", "Ценности", "Технология"],
    ["Фразы", "Философия", "О бренде"],
    ["Каталог", "Прайс"],
]

def keyboard():
    return ReplyKeyboardMarkup(MENU_BUTTONS, resize_keyboard=True)

# === ПРИВЕТСТВИЕ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = MSG.get("start", "Привет!") + "\n\n" + MSG.get("menu_hint", "Выбери раздел на клавиатуре ниже 👇")
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard())

# === РОУТЕР ===
async def route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text_raw = update.message.text or ""
    user_text = user_text_raw.strip().lower()

    mapping = {
        "обучение": "obuchenie",
        "ценности": "cennosti",
        "технология": "tehnologiya",
        "фразы": "frazy",
        "философия": "filosofiya",
        "о бренде": "o_brende",
    }

    intros = {
        "обучение": "🎓 Учиться говорить о хлебе — значит чувствовать его душу.",
        "ценности": "💛 Ценности БулкиПечь — это аромат масла, тёплые руки и честная работа:",
        "технология": "⚙️ Технология — наш ритуал ремесла. Каждое утро мы делаем тесто, как музыку:",
        "фразы": "🗣️ Иногда одно слово может вызвать аппетит. Вот примеры:",
        "философия": "🌿 Вкус как искусство. Так мы чувствуем хлеб, тесто и жизнь:",
        "о бренде": "🥐 БулкиПечь — не просто пекарня. Это история о людях, которые делают счастье из муки и масла:",
    }

    key = mapping.get(user_text)
    if key and key in MSG:
        intro = intros.get(user_text, "")
        text = f"{intro}\n\n{MSG[key]}\n\n_— Макар Макарыч, наставник БулкиПечь_ 🥐"
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard())
        return

    if user_text in ("каталог", "/catalog"):
        await catalog_cmd(update, context); return
    if user_text in ("прайс", "/price"):
        await price_cmd(update, context); return

    if user_text_raw.startswith("/ask") or user_text_raw.strip().endswith("?"):
        await ask_cmd(update, context); return

    if have_openai():
        await ask_cmd(update, context); return

    await update.message.reply_text(MSG.get("menu_hint", "Выбери раздел на клавиатуре ниже 👇"), reply_markup=keyboard())

# === КАТАЛОГ / ПРАЙС ===
def price_categories_keyboard() -> InlineKeyboardMarkup:
    if not PRICE:
        return InlineKeyboardMarkup([[InlineKeyboardButton("Прайс не найден", callback_data="noop")]])
    buttons = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in PRICE.keys()]
    return InlineKeyboardMarkup(buttons)

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите категорию:", reply_markup=price_categories_keyboard())

async def catalog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Каталог:", reply_markup=price_categories_keyboard())

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = (query.data or "")
    if data.startswith("cat|"):
        cat = data.split("|", 1)[1]
        items = PRICE.get(cat, [])
        if not items:
            await query.edit_message_text(f"В категории *{cat}* пока пусто.", parse_mode="Markdown")
            return
        kb = [[InlineKeyboardButton(item["name"], callback_data=f"item|{cat}|{i}")]
              for i, item in enumerate(items)]
        await query.edit_message_text(f"Категория: *{cat}*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("item|"):
        _, cat, idx = data.split("|")
        idx = int(idx)
        item = PRICE.get(cat, [])[idx]
        name = item.get("name", "Товар")
        price = item.get("price", "—")
        desc = item.get("desc", "")
        image = item.get("image")
        caption = f"{name}\nЦена: {price} ₽\n{desc}".strip()

        if image:
            path = MEDIA_DIR / image
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        await query.message.reply_photo(photo=InputFile(f), caption=caption)
                except Exception as e:
                    await query.message.reply_text(f"{caption}\n(Ошибка: {e})")
            else:
                await query.message.reply_text(f"{caption}\n(Фото не найдено: {image})")
        else:
            await query.message.reply_text(caption)

        await query.message.reply_text(
            f"Назад к категории *{cat}*:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=f"cat|{cat}")]]),
        )
        return

# === УМНЫЕ ОТВЕТЫ ===
def rule_based_answer(text: str) -> str:
    t = text.lower()
    if "как рассказать" in t or "что сказать" in t or "как продать" in t:
        return ("Говори просто и с теплом: масло 82,5%, ручная работа, долгий отдых теста, хруст. "
                "Например: «Попробуйте — хрустит как француз, но с душой Сибири.»")
    if "цена" in t or "прайс" in t:
        return "Открой /price — там категории и цены."
    if "состав" in t:
        return "Чистый состав: сливочное масло 82,5%, итальянская мука Манитоба, без улучшителей."
    if "заморозка" in t:
        return "Ремесленная технология, без консервантов. Лучше — свежим."
    return "Я рядом, подскажу про вкус, состав, подачу. Спроси, например: «Как рассказать про круассан человеку, который спешит?»"

# === LLM ===
def have_openai() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))

async def ai_answer_llm(prompt: str) -> str:
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return rule_based_answer(prompt)

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        resp = client.chat.completions.create(
            model="openrouter/auto",
            messages=[
                {"role": "system", "content": "Ты — Макар Макарыч, наставник БулкиПечь. Говори по-доброму и со вкусом."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.7,
            timeout=20,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"⚠️ OpenRouter error: {e}")
        return rule_based_answer(prompt)

# === УМНЫЙ ОТВЕТ ===
async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    parts = text.split(" ", 1)
    question = parts[1] if len(parts) > 1 else "Подскажи, как рассказать о круассане."
    reply = await ai_answer_llm(question) if have_openai() else rule_based_answer(question)
    await update.message.reply_text(reply + "\n\n_— Макар Макарыч 🥐_", parse_mode="Markdown")

# === MAIN ===
async def run_bot():
    token = "7560052787:AAFF_Hi8-FLhVEu3_V5nziBh9qPMtuJsoSg"
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("catalog", catalog_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route))

    print("🤖 Макар Макарыч запущен. Работает устойчиво 24/7.")
    await app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        timeout=30,
        poll_interval=2,
        drop_pending_updates=True,
        stop_signals=None  # для стабильности под systemd
    )

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(run_bot())
        except Exception as e:
            logger.error(f"💥 Бот упал: {e}, перезапуск через 10 сек...")
            asyncio.run(asyncio.sleep(10))
