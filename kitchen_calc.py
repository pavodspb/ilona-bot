import math


PRICE = {
    "Сушка": 2856,
    "Цоколь": 2550,
    "Ручка": 510,
    "Столешница": 8500,
    "Стеновая_панель": 5100,
    "Доставка": 7000,
    "Сборка": 0.12,
    "Погонный_метр": 30000,
    "Антресоль": 5400,
    "Антресоль_пенал": 5400,
    "Фасад_ЛДСП": 2000,
    "Фасад_ПВХ": 8000,
    "Фасад_AGT": 12000,
    "Фасад_Эмаль": 15000,
    "Пенал_ЛДСП": 20000,
    "Пенал_ПВХ": 30000,
    "Пенал_AGT": 35000,
    "Пенал_Эмаль": 35000
}

STEPS = [
    "type",
    "wall_a",
    "wall_b",
    "fridge",
    "antresol_fridge",
    "height",
    "antresols",
    "material",
    "wall_panel",
    "penals",
    "antresol_penals"
]

QUESTIONS = {
    "type": "Выберите тип кухни:\n1. Прямая\n2. Угловая\n\nОтветьте: 1 или 2",
    "wall_a": "Введите длину стены А в мм (например: 2400):",
    "wall_b": "Введите длину стены Б в мм (например: 1800):",
    "fridge": "Холодильник входит в размеры кухни?\n1. Да\n2. Нет",
    "antresol_fridge": "Установить антресоль над холодильником?\n1. Да\n2. Нет",
    "height": "Выберите высоту верхних модулей:\n1. 716 мм\n2. 916 мм\n3. 1016 мм",
    "antresols": "Установить антресоли над верхними шкафами?\n1. Да\n2. Нет",
    "material": "Выберите материал фасадов:\n1. ЛДСП\n2. МДФ-ПВХ\n3. МДФ-AGT\n4. МДФ-Эмаль",
    "wall_panel": "Установить стеновую панель (фартук)?\n1. Да\n2. Нет",
    "penals": "Выберите пеналы (через запятую):\n1. Холодильник\n2. Техника\n3. Продукты\n\nПример: 1,3 или просто 0 если нет",
    "antresol_penals": "Антресоли над пеналами (через запятую):\n1. Холодильник\n2. Техника\n3. Продукты\n\nПример: 1 или 0 если нет"
}

HEIGHTS = {"1": 716, "2": 916, "3": 1016}
MATERIALS = {"1": "ЛДСП", "2": "ПВХ", "3": "AGT", "4": "Эмаль"}
PENAL_NAMES = {"1": "холодильник", "2": "техника", "3": "продукты"}


class KitchenCalc:
    def __init__(self):
        self.reset()

    def reset(self):
        self.step = 0
        self.data = {
            "type": "",
            "wall_a": 0,
            "wall_b": 0,
            "fridge": False,
            "antresol_fridge": False,
            "height": 716,
            "antresols": False,
            "material": "ЛДСП",
            "wall_panel": False,
            "penals": [],
            "antresol_penals": []
        }

    def get_question(self):
        if self.step >= len(STEPS):
            return None
        key = STEPS[self.step]
        return QUESTIONS[key]

    def process_answer(self, answer):
        key = STEPS[self.step]
        answer = answer.strip()

        try:
            if key == "type":
                if answer not in ("1", "2"):
                    return "Пожалуйста, выберите 1 или 2"
                self.data["type"] = "прямая" if answer == "1" else "угловая"

            elif key == "wall_a":
                val = int(answer)
                if val <= 0:
                    return "Длина должна быть положительным числом"
                self.data["wall_a"] = val

            elif key == "wall_b":
                if self.data["type"] != "угловая":
                    self.step += 1
                    return self.get_question()
                val = int(answer)
                if val <= 0:
                    return "Длина должна быть положительным числом"
                self.data["wall_b"] = val

            elif key == "fridge":
                if answer not in ("1", "2"):
                    return "Пожалуйста, выберите 1 или 2"
                self.data["fridge"] = answer == "1"

            elif key == "antresol_fridge":
                if answer not in ("1", "2"):
                    return "Пожалуйста, выберите 1 или 2"
                self.data["antresol_fridge"] = answer == "1"

            elif key == "height":
                if answer not in HEIGHTS:
                    return "Пожалуйста, выберите 1, 2 или 3"
                self.data["height"] = HEIGHTS[answer]

            elif key == "antresols":
                if answer not in ("1", "2"):
                    return "Пожалуйста, выберите 1 или 2"
                self.data["antresols"] = answer == "1"

            elif key == "material":
                if answer not in MATERIALS:
                    return "Пожалуйста, выберите от 1 до 4"
                self.data["material"] = MATERIALS[answer]

            elif key == "wall_panel":
                if answer not in ("1", "2"):
                    return "Пожалуйста, выберите 1 или 2"
                self.data["wall_panel"] = answer == "1"

            elif key == "penals":
                if answer == "0":
                    self.data["penals"] = []
                else:
                    nums = [x.strip() for x in answer.split(",")]
                    self.data["penals"] = [PENAL_NAMES[n] for n in nums if n in PENAL_NAMES]

            elif key == "antresol_penals":
                if answer == "0":
                    self.data["antresol_penals"] = []
                else:
                    nums = [x.strip() for x in answer.split(",")]
                    self.data["antresol_penals"] = [PENAL_NAMES[n] for n in nums if n in PENAL_NAMES]

            self.step += 1
            if self.step < len(STEPS):
                key_next = STEPS[self.step]
                if key_next == "wall_b" and self.data["type"] != "угловая":
                    self.step += 1
                if self.step < len(STEPS):
                    return QUESTIONS[STEPS[self.step]]

            return None

        except (ValueError, KeyError):
            return "Некорректный ввод. Попробуйте ещё раз."

    def calculate(self):
        d = self.data
        total_length = d["wall_a"] + (d["wall_b"] if d["type"] == "угловая" else 0)
        penal_count = len(d["penals"])
        subtract = 600 * (1 if d["fridge"] else 0) + 600 * penal_count
        calc_length = max(0, total_length - subtract)

        report = []
        kitchen_total = 0

        furniture_cost = (calc_length / 1000) * PRICE["Погонный_метр"]
        kitchen_total += furniture_cost
        report.append(f"Общая длина кухни: {total_length / 1000:.2f}м")
        report.append(f"Длина для расчета: {calc_length}мм\n")
        report.append("--- Корпус ---")
        report.append(f"Стоимость корпусов: {furniture_cost:,.0f} руб.")

        if penal_count > 0:
            penal_cost = penal_count * PRICE[f"Пенал_{d['material']}"]
            kitchen_total += penal_cost
            report.append(f"Пеналов ({penal_count} шт.): {penal_cost:,.0f} руб.")

        antresol_cost = 0
        if d["antresol_fridge"]:
            antresol_cost += PRICE["Антресоль"]
        if d["antresols"]:
            antresol_cost += (calc_length * 0.3 / 1000) * PRICE["Погонный_метр"]
        antresol_penal_count = len(d["antresol_penals"])
        antresol_cost += antresol_penal_count * PRICE["Антресоль_пенал"]
        if antresol_cost > 0:
            kitchen_total += antresol_cost
            report.append(f"\n--- Антресоли ---")
            report.append(f"Стоимость: {antresol_cost:,.0f} руб.")

        lower_front = 716
        upper_front = d["height"]
        facade_area = ((lower_front + upper_front) * calc_length) / 1e6
        facade_cost = facade_area * PRICE[f"Фасад_{d['material']}"]
        kitchen_total += facade_cost
        report.append(f"\n--- Фасады (низ 716мм + верх {upper_front}мм) ---")
        report.append(f"Материал: {d['material']}")
        report.append(f"Стоимость: {facade_cost:,.0f} руб.")

        countertop_length = calc_length - (600 if d["type"] == "угловая" else 0)
        countertop_count = math.ceil(countertop_length / 3000)
        countertop_cost = countertop_count * PRICE["Столешница"]
        kitchen_total += countertop_cost

        wall_panel_cost = 0
        if d["wall_panel"]:
            wall_panel_count = math.ceil(calc_length / 3000)
            wall_panel_cost = wall_panel_count * PRICE["Стеновая_панель"]
            kitchen_total += wall_panel_cost

        report.append(f"\n--- Столешница и фартук ---")
        report.append(f"Столешница: {countertop_cost:,.0f} руб.")
        if wall_panel_cost > 0:
            report.append(f"Стеновая панель: {wall_panel_cost:,.0f} руб.")

        dryer_cost = PRICE["Сушка"]
        handle_cost = math.ceil(calc_length / 600) * PRICE["Ручка"]
        plinth_cost = math.ceil((calc_length + 1200) / 4000) * PRICE["Цоколь"]
        kitchen_total += dryer_cost + handle_cost + plinth_cost

        report.append(f"\n--- Фурнитура ---")
        report.append(f"Посудосушитель: {dryer_cost:,.0f} руб.")
        report.append(f"Ручки: {handle_cost:,.0f} руб.")
        report.append(f"Цоколь: {plinth_cost:,.0f} руб.")

        report.append(f"\nИТОГО СТОИМОСТЬ КУХНИ: {kitchen_total:,.0f} руб.")

        delivery_cost = PRICE["Доставка"]
        assembly_cost = kitchen_total * PRICE["Сборка"]

        report.append(f"\n--- Услуги ---")
        report.append(f"Доставка: {delivery_cost:,.0f} руб.")
        report.append(f"Базовая сборка: {assembly_cost:,.0f} руб.")
        report.append(f"\nИТОГО С УСЛУГАМИ: {kitchen_total + delivery_cost + assembly_cost:,.0f} руб.")

        report.append(f"\nДля точного расчета необходим утвержденный проект.")
        report.append(f"Оставьте заявку и получите скидку!")

        return "\n".join(report)
