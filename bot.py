import os
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters
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


def get_calc_buttons(step, calc):
    if step == "type":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Прямая", callback_data="calc_1"),
             InlineKeyboardButton("Угловая", callback_data="calc_2")]
        ])
    elif step == "fridge":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="calc_1"),
             InlineKeyboardButton("Нет", callback_data="calc_2")]
        ])
    elif step == "antresol_fridge":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="calc_1"),
             InlineKeyboardButton("Нет", callback_data="calc_2")]
        ])
    elif step == "height":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("716 мм", callback_data="calc_1"),
             InlineKeyboardButton("916 мм", callback_data="calc_2"),
             InlineKeyboardButton("1016 мм", callback_data="calc_3")]
        ])
    elif step == "antresols":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="calc_1"),
             InlineKeyboardButton("Нет", callback_data="calc_2")]
        ])
    elif step == "material":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("ЛДСП", callback_data="calc_1"),
             InlineKeyboardButton("МДФ-ПВХ", callback_data="calc_2")],
            [InlineKeyboardButton("МДФ-AGT", callback_data="calc_3"),
             InlineKeyboardButton("МДФ-Эмаль", callback_data="calc_4")]
        ])
    elif step == "wall_panel":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Да", callback_data="calc_1"),
             InlineKeyboardButton("Нет", callback_data="calc_2")]
        ])
    elif step == "penals":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Холодильник", callback_data="calc_p1"),
             InlineKeyboardButton("Техника", callback_data="calc_p2"),
             InlineKeyboardButton("Продукты", callback_data="calc_p3")],
            [InlineKeyboardButton("Нет пеналов", callback_data="calc_p0"),
             InlineKeyboardButton("Готово", callback_data="calc_done")]
        ])
    elif step == "antresol_penals":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Холодильник", callback_data="calc_a1"),
             InlineKeyboardButton("Техника", callback_data="calc_a2"),
             InlineKeyboardButton("Продукты", callback_data="calc_a3")],
            [InlineKeyboardButton("Нет антресолей", callback_data="calc_a0"),
             InlineKeyboardButton("Готово", callback_data="calc_adone")]
        ])
    return None


CALC_QUESTIONS = {
    "type": "Выберите тип кухни:",
    "wall_a": "Введите длину стены А в мм (например: 2400):",
    "wall_b": "Введите длину стены Б в мм (например: 1800):",
    "fridge": "Холодильник входит в размеры кухни?",
    "antresol_fridge": "Установить антресоль над холодильником?",
    "height": "Выберите высоту верхних модулей:",
    "antresols": "Установить антресоли над верхними шкафами?",
    "material": "Выберите материал фасадов:",
    "wall_panel": "Установить стеновую панель (фартук)?",
    "penals": "Выберите пеналы (можно несколько):",
    "antresol_penals": "Антресоли над пеналами (можно несколько):"
}

STEP_ORDER = ["type", "wall_a", "wall_b", "fridge", "antresol_fridge",
              "height", "antresols", "material", "wall_panel", "penals", "antresol_penals"]


async def start_cmd(update: Update, context: CallbackContext):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Рассчитать кухню", callback_data="start_calc")],
        [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")]
    ])
    await update.message.reply_text(
        f"{PROFILE['greeting']}\n\nЧем могу помочь?",
        reply_markup=keyboard
    )


async def calc_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_calcs[user_id] = KitchenCalc()
    calc = user_calcs[user_id]
    step = STEP_ORDER[calc.step]
    buttons = get_calc_buttons(step, calc)
    await update.message.reply_text(
        f"Калькулятор кухни\n\n{CALC_QUESTIONS[step]}",
        reply_markup=buttons
    )


async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "start_calc":
        user_calcs[user_id] = KitchenCalc()
        calc = user_calcs[user_id]
        step = STEP_ORDER[calc.step]
        buttons = get_calc_buttons(step, calc)
        await query.edit_message_text(
            f"Калькулятор кухни\n\n{CALC_QUESTIONS[step]}",
            reply_markup=buttons
        )
        return

    if data == "ask_question":
        await query.edit_message_text("Задайте вопрос — я постараюсь помочь!")
        return

    if user_id not in user_calcs:
        await query.edit_message_text("Сессия калькулятора истекла. Нажмите /calc заново.")
        return

    calc = user_calcs[user_id]
    step = STEP_ORDER[calc.step]

    if data.startswith("calc_p"):
        if data == "calc_p0":
            calc.data["penals"] = []
            calc.step += 1
        elif data == "calc_done":
            calc.step += 1
        else:
            num = data.replace("calc_p", "")
            names = {"1": "холодильник", "2": "техника", "3": "продукты"}
            if names[num] not in calc.data["penals"]:
                calc.data["penals"].append(names[num])
            penals_text = ", ".join(calc.data["penals"]) if calc.data["penals"] else "нет"
            await query.edit_message_text(
                f"Калькулятор кухни\n\nВыберите пеналы (можно несколько):\nВыбрано: {penals_text}",
                reply_markup=get_calc_buttons("penals", calc)
            )
            return

    elif data.startswith("calc_a"):
        if data == "calc_a0":
            calc.data["antresol_penals"] = []
            calc.step += 1
        elif data == "calc_adone":
            calc.step += 1
        else:
            num = data.replace("calc_a", "")
            names = {"1": "холодильник", "2": "техника", "3": "продукты"}
            if names[num] not in calc.data["antresol_penals"]:
                calc.data["antresol_penals"].append(names[num])
            penals_text = ", ".join(calc.data["antresol_penals"]) if calc.data["antresol_penals"] else "нет"
            await query.edit_message_text(
                f"Калькулятор кухни\n\nАнтресоли над пеналами (можно несколько):\nВыбрано: {penals_text}",
                reply_markup=get_calc_buttons("antresol_penals", calc)
            )
            return

    elif data.startswith("calc_"):
        answer = data.replace("calc_", "")

        if step == "type":
            calc.data["type"] = "прямая" if answer == "1" else "угловая"
            calc.step += 1
        elif step == "fridge":
            calc.data["fridge"] = answer == "1"
            calc.step += 1
        elif step == "antresol_fridge":
            calc.data["antresol_fridge"] = answer == "1"
            calc.step += 1
        elif step == "height":
            heights = {"1": 716, "2": 916, "3": 1016}
            calc.data["height"] = heights[answer]
            calc.step += 1
        elif step == "antresols":
            calc.data["antresols"] = answer == "1"
            calc.step += 1
        elif step == "material":
            materials = {"1": "ЛДСП", "2": "ПВХ", "3": "AGT", "4": "Эмаль"}
            calc.data["material"] = materials[answer]
            calc.step += 1
        elif step == "wall_panel":
            calc.data["wall_panel"] = answer == "1"
            calc.step += 1

    if step == "wall_a" or step == "wall_b":
        try:
            val = int(query.message.text.split(":", 1)[-1].strip().split()[0])
            if val > 0:
                calc.data[step] = val
                calc.step += 1
        except (ValueError, IndexError):
            await query.edit_message_text("Пожалуйста, введите число в поле ввода.")
            return

    if calc.step >= len(STEP_ORDER):
        result = calc.calculate()
        await query.edit_message_text(result)
        del user_calcs[user_id]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Новый расчет", callback_data="start_calc")],
            [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")]
        ])
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Хотите сделать еще расчет или задать вопрос?",
            reply_markup=keyboard
        )
        return

    next_step = STEP_ORDER[calc.step]

    if next_step in ("wall_a", "wall_b"):
        if next_step == "wall_b" and calc.data["type"] != "угловая":
            calc.step += 1
            if calc.step >= len(STEP_ORDER):
                result = calc.calculate()
                await query.edit_message_text(result)
                del user_calcs[user_id]
                return
            next_step = STEP_ORDER[calc.step]

        await query.edit_message_text(
            f"Калькулятор кухни\n\n{CALC_QUESTIONS[next_step]}"
        )
        return

    buttons = get_calc_buttons(next_step, calc)
    await query.edit_message_text(
        f"Калькулятор кухни\n\n{CALC_QUESTIONS[next_step]}",
        reply_markup=buttons
    )


async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if user_id in user_calcs:
        calc = user_calcs[user_id]
        step = STEP_ORDER[calc.step]

        if step in ("wall_a", "wall_b"):
            try:
                val = int(user_text)
                if val > 0:
                    calc.data[step] = val
                    calc.step += 1

                    if step == "wall_b" or (step == "wall_a" and calc.data["type"] != "угловая"):
                        if calc.data["type"] != "угловая":
                            calc.step += 1

                    if calc.step >= len(STEP_ORDER):
                        result = calc.calculate()
                        await update.message.reply_text(result)
                        del user_calcs[user_id]
                        keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton("Новый расчет", callback_data="start_calc")],
                            [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")]
                        ])
                        await update.message.reply_text("Хотите еще расчет?", reply_markup=keyboard)
                        return

                    next_step = STEP_ORDER[calc.step]
                    buttons = get_calc_buttons(next_step, calc)
                    await update.message.reply_text(
                        f"Калькулятор кухни\n\n{CALC_QUESTIONS[next_step]}",
                        reply_markup=buttons
                    )
                    return
                else:
                    await update.message.reply_text("Введите положительное число:")
            except ValueError:
                await update.message.reply_text("Пожалуйста, введите число:")
        return

    if not API_KEY:
        await update.message.reply_text("Сервис временно недоступен.")
        return

    lower = user_text.lower()
    calc_keywords = ["рассчит", "цена", "стоим", "сколько сто", "калькулятор", "расчет кухн", "расчёт кухн", "calc"]
    if any(kw in lower for kw in calc_keywords):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Рассчитать кухню", callback_data="start_calc")]
        ])
        await update.message.reply_text(
            "Хотите рассчитать стоимость кухни?\n\nНажмите кнопку ниже!",
            reply_markup=keyboard
        )
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
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
