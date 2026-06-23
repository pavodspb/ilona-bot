import os
import json
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

CONFIG_FILE = "config.json"
API_KEY_FILE = "Илона.txt"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return os.environ.get("GROQ_API_KEY", "")


def build_system_prompt(config):
    p = config.get("profile", {})
    k = config.get("knowledge", {})
    skills = config.get("skills", [])

    products = "\n".join(k.get("products", []))
    prices = "\n".join(k.get("prices", []))
    faq = "\n".join(k.get("faq", []))

    return f"""Ты — {p.get('name', 'Ассистент')}, {p.get('specialization', 'специалист')}.
Компания: {p.get('company', 'Не указана')}
Описание: {p.get('description', '')}
Тон общения: {p.get('tone', 'Профессиональный')}

Твои навыки:
{chr(10).join('- ' + s for s in skills) if skills else '- Консультация'}

Товары и услуги:
{products if products else 'Информация не добавлена'}

Цены:
{prices if prices else 'Информация не добавлена'}

Частые вопросы:
{faq if faq else 'Информация не добавлена'}

Правила:
- Отвечай на русском
- Будь вежливой и helpful
- Если не знаешь ответ — скажи что уточнишь у специалиста
- Не выдумывай информацию, которой нет в базе
- Отвечай кратко и по делу"""


config = load_config()
API_KEY = get_api_key()
SYSTEM_PROMPT = build_system_prompt(config)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = config.get("profile", {})
    greeting = p.get("greeting", "Здравствуйте! Чем могу помочь?")
    await update.message.reply_text(greeting)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if not API_KEY:
        await update.message.reply_text("Сервис временно недоступен. Попробуйте позже.")
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
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
    token = config.get("telegram", {}).get("token", "")
    if not token:
        print("Нет токена Telegram бота!")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
