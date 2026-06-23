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
        report.append(f"Итоговая длина для расчета: {calc_length}мм\n")
        report.append("🗄 Корпус")
        report.append(f"Стоимость корпусов: {furniture_cost:,.0f}₽".replace(',', ' '))

        if penal_count > 0:
            penal_cost = penal_count * PRICE[f"Пенал_{d['material']}"]
            kitchen_total += penal_cost
            report.append(f"- Пеналов ({penal_count} шт.): {penal_cost:,.0f}₽".replace(',', ' '))

        antresol_cost = 0
        if d["antresol_fridge"]:
            antresol_cost += PRICE["Антресоль"]
        if d["antresols"]:
            antresol_cost += (calc_length * 0.3 / 1000) * PRICE["Погонный_метр"]
        antresol_penal_count = len(d["antresol_penals"])
        antresol_cost += antresol_penal_count * PRICE["Антресоль_пенал"]
        if antresol_cost > 0:
            kitchen_total += antresol_cost
            report.append(f"\n🔝 Антресоли: {antresol_cost:,.0f}₽".replace(',', ' '))
            if antresol_penal_count > 0:
                report.append(f"  - Над пеналами: {antresol_penal_count} шт.")

        lower_front = 716
        upper_front = d["height"]
        facade_area = ((lower_front + upper_front) * calc_length) / 1e6
        facade_cost = facade_area * PRICE[f"Фасад_{d['material']}"]
        kitchen_total += facade_cost
        report.append(f"\n🎨 Фасады (низ {lower_front} мм + верх {upper_front} мм)")
        report.append(f"Материал: {d['material']}")
        report.append(f"Стоимость {facade_cost:,.0f}₽".replace(',', ' '))

        countertop_length = calc_length - (600 if d["type"] == "угловая" else 0)
        countertop_count = math.ceil(countertop_length / 3000)
        countertop_cost = countertop_count * PRICE["Столешница"]
        kitchen_total += countertop_cost

        wall_panel_cost = 0
        if d["wall_panel"]:
            wall_panel_count = math.ceil(calc_length / 3000)
            wall_panel_cost = wall_panel_count * PRICE["Стеновая_панель"]
            kitchen_total += wall_panel_cost

        report.append(f"\n🔲 Столешница и фартук")
        report.append(f"Столешница: {countertop_cost:,.0f}₽".replace(',', ' '))
        if wall_panel_cost > 0:
            report.append(f"Стеновая панель: {wall_panel_cost:,.0f}₽".replace(',', ' '))

        dryer_cost = PRICE["Сушка"]
        handle_cost = math.ceil(calc_length / 600) * PRICE["Ручка"]
        plinth_cost = math.ceil((calc_length + 1200) / 4000) * PRICE["Цоколь"]
        kitchen_total += dryer_cost + handle_cost + plinth_cost

        report.append(f"\n🔩 Фурнитура")
        report.append(f"Посудосушитель: {dryer_cost:,.0f}₽".replace(',', ' '))
        report.append(f"Ручки: {handle_cost:,.0f}₽".replace(',', ' '))
        report.append(f"Цоколь: {plinth_cost:,.0f}₽".replace(',', ' '))

        report.append(f"\n💰 *ИТОГО СТОИМОСТЬ КУХНИ*: {kitchen_total:,.0f}₽".replace(',', ' '))

        delivery_cost = PRICE["Доставка"]
        assembly_cost = kitchen_total * PRICE["Сборка"]

        report.append(f"\n🚚 Услуги")
        report.append(f"- Доставка: {delivery_cost:,.0f}₽".replace(',', ' '))
        report.append(f"- Базовая сборка: {assembly_cost:,.0f}₽".replace(',', ' '))

        report.append(f"\n⚠️ Для точного расчета необходим утвержденный проект")
        report.append(f"Оставьте заявку на сайте: https://kitchen360.ru и получите 🎁")

        return "\n".join(report)
