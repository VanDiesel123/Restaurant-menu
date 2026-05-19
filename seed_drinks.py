import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()
    print("Підключено до бази даних для завантаження напоїв...")

    # Список напоїв з цінами (назви мають точно збігатися з drinks_list у твоїй моделі)
    drinks_to_add = [
        {"Dish_name": "Кава", "Price": 45.0},
        {"Dish_name": "Чай", "Price": 35.0},
        {"Dish_name": "Кола", "Price": 40.0},
        {"Dish_name": "Лимонад", "Price": 55.0},
        {"Dish_name": "Сік", "Price": 30.0},
        {"Dish_name": "Еспресо", "Price": 40.0},
        {"Dish_name": "Капучино", "Price": 50.0}
    ]

    for drink in drinks_to_add:
        # Перевіряємо, чи раптом такий напій уже не існує в базі
        existing = await db.dish.find_unique(
            where={"Dish_name": drink["Dish_name"]}
        )
        
        if not existing:
            await db.dish.create(data=drink)
            print(f"Напій успішно додано: {drink['Dish_name']} — {drink['Price']} грн.")
        else:
            print(f"Напій '{drink['Dish_name']}' вже є в базі даних.")

    await db.disconnect()
    print("Базу даних успішно оновлено!")

if __name__ == "__main__":
    asyncio.run(main())