import os
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API_KEY = os.environ.get("GROQ_API_KEY", "")
TG_TOKEN = os.environ.get("TG_TOKEN", "")

PROFILE = {
    "name": os.environ.get("BOT_NAME", "Илона"),
    "specialization": os.environ.get("BOT_SPEC", "Продажа кухонь"),
    "company": os.environ.get("BOT_COMPANY", ""),
    "description": os.environ.get("BOT_DESC", "Помощник по подбору и продаже кухонь"),
    "greeting": os.environ.get("BOT_GREETING", "Здравствуйте! Я Илона, ваш помощник по выбору кухни."),
    "tone": os.environ.get("BOT_TONE", "Дружелюбный, профессиональный"),
}

PRODUCTS = os.environ.get("BOT_PRODUCTS", "Информация не добавлена")
PRICES = os.environ.get("BOT_PRICES", "Информация не добавлена")
FAQ = os.environ.get("BOT_FAQ", "Информация не добавлена")
SKILLS = os.environ.get("BOT_SKILLS", "Консультация")


def build_system_prompt():
    return f"""Ты — {PROFILE['name']}, {PROFILE['specialization']}.
Компания: {PROFILE['company'] or 'Не указана'}
Описание: {PROFILE['description']}
Тон общения: {PROFILE['tone']}

Твои навыки:
{SKILLS}

Товары и услуги:
{PRODUCTS}

Цены:
{PRICES}

Частые вопросы:
{FAQ}

Правила:
- Отвечай на русском
- Будь вежливой и helpful
- Если не знаешь ответ — скажи что уточнишь у специалиста
- Не выдумывай информацию, которой нет в базе
- Отвечай кратко и по делу"""


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(PROFILE["greeting"])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if not API_KEY:
        await update.message.reply_text("Сервис временно недоступен.")
        return

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_text}
    ]

    try:
        client = Groq(api_key=API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")


def main():
    if not TG_TOKEN:
        print("Нет токена Telegram!")
        return
    if not API_KEY:
        print("Нет ключа Groq!")
        return

    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
