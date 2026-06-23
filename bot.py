import os
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from kitchen_calc import KitchenCalc

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

user_calcs = {}


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
- Отвечай кратко и по делу
- Если просят рассчитать кухню — предложи калькулятор: /calc"""


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(PROFILE["greeting"])


async def calc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_calcs[user_id] = KitchenCalc()
    question = user_calcs[user_id].get_question()
    await update.message.reply_text(f"Калькулятор кухни\n\n{question}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if user_id in user_calcs:
        calc = user_calcs[user_id]
        response = calc.process_answer(user_text)

        if response:
            await update.message.reply_text(response)
        elif calc.step >= len(calc.data):
            result = calc.calculate()
            await update.message.reply_text(result)
            del user_calcs[user_id]
            await update.message.reply_text("Хотите сделать еще расчет? /calc\nИли задайте вопрос!")
        else:
            question = calc.get_question()
            if question:
                await update.message.reply_text(question)
        return

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
    app.add_handler(CommandHandler("calc", calc_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
