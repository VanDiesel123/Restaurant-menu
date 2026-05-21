import copy
import asyncio
from prisma import Prisma

class RestaurantModel:
    def __init__(self):
        """
        ІНІЦІАЛІЗАЦІЯ ОБ'ЄКТА МОДЕЛІ.
        """
        self.db = Prisma()
        # Тимчасові змінні стану для збереження зв'язку з контролером
        self.current_table_num = 7       # Поточний обраний стіл у CREATE та EDIT (int)
        self.selected_category = "Страви" # Поточна категорія меню (str)
        self.selected_dish = None         # Назва поточної обраної страви (str або None)
        
        # Робочі буфери оперативної пам'яті контролера (не потребують збереження в таблиці БД)
        self.current_dish_ingredients = [] # Список словників поточних кастомних інгредієнтів страви
        self.basket_dishes = []            # Тимчасовий кошик поточного незавершеного замовлення

        # --- СТРУКТУРИ ДАНИХ (БЕКЕНД-РОЗРОБНИК МАЄ ПЕРЕНЕСТИ ЦЕ В ТАБЛИЦІ БД) ---
        # 1. Таблиця Orders / OrderItems: { order_id (int): {"table": int, "dishes": [list of snapshots]} }
        self.my_orders_database = {} 
        self.next_order_id = 1 # Лічильник автоінкременту для ID нових чеків (Primary Key)
        
        # 2. Таблиця Menu / Categories: Динамічна структура меню ресторану та базових цін
        self.menu_data = {
            "Страви": {},
            "Напої": {},
        }

        # 3. Таблиця DishConfigurations: Зберігає тривалість приготування страв 
        self.dish_cooking_time = {
            "Борщ український": 25, "Плов з телятиною": 35, "Салат Цезар": 15,
            "Стейк Рибай": 20, "Суп томатний": 15, "Деруни зі сметаною": 20,
            "Вареники з капустою": 15, "Пельмені домашні": 15, "Шашлик свинячий": 25,
            "Котлета по-київськи": 20
        }
        
        # 4. Таблиця DishDescriptions: Текстові рядки описів страв для середньої колонки
        self.descriptions = {
            "Борщ український": [
                "Традиційний український борщ на м'ясному бульйоні.",
                "Подається зі свіжою сметаною, зеленню та пампушками.",
                "Має насичений буряковий колір та легку кислинку.",
                "Готується за старовинним рецептом наших шеф-кухарів."
            ],
            "Плов з телятиною": [
                "Ароматний розсипчастий рис із ніжною телятиною.",
                "З додаванням зіри, барбарису та часнику.",
                "Готується у справжньому чавунному казані."
            ],
            "Салат Цезар": [
                "Класичний салат із соковитою курячою грудинкою.",
                "Хрусткі сухарики, пармезан та фірмовий соус Цезар.",
                "Легка та поживна страва для обіду."
            ],
            "Стейк Рибай": [
                "Преміальний стейк із мармурової яловичини.",
                "Ступінь просмаження за вашим вибором.",
                "Подається з ароматним маслом та розмарином."
            ],
            "Суп томатний": [
                "Густий суп зі стиглих томатів та базиліку.",
                "Подається із грінками та краплею оливкової олії."
            ],
            "Деруни зі сметаною": [
                "Традиційні хрусткі деруни з тертої картоплі.",
                "Смажаться до золотистої скоринки.",
                "Подаються гарячими зі свіжою сметаною."
            ],
            "Вареники з капустою": [
                "Домашні вареники з тушкованою капустою.",
                "Поливаються засмажкою з цибулі та олії."
            ],
            "Пельмені домашні": [
                "Пельмені ручного ліплення з міксом фаршу.",
                "Подаються з вершковим маслом та оцтом за бажанням."
            ],
            "Шашлик свинячий": [
                "Ніжний шашлик з ошийка, маринований у спеціях.",
                "Подається з маринованою цибулею та соусом."
            ],
            "Котлета по-київськи": [
                "Легендарна соковита котлета у хрусткій паніровці.",
                "Всередині ховається ароматне вершкове масло з зеленню."
            ]
        }
        
        # 5. Таблиця Recipes: Технологічні карти страв { dish_name (str): { ing_name (str): "вартість_маркер" } }
        self.dish_ingredients_matrix = {
            "Борщ український": {
                "Яловичина (г)": "100 $", "Буряк (г)": "80 &", "Капуста (г)": "50 *",
                "Картопля (г)": "60 *", "Сметана (г)": "30 *", "Пампушки (шт)": "2 &",
                "Часник (част)": "3 *", "Зелень (г)": "10 *", "Сало (г)": "20 *",
                "Цибуля зелена (г)": "15 *", "Квасоля (г)": "0 !", "Перець чилі (шт)": "0 !"
            },
            "Плов з телятиною": {
                "Рис (г)": "150 $", "Телятина (г)": "120 $", "Mорква (г)": "50 &",
                "Цибуля (г)": "40 *", "Зіра (г)": "5 *", "Барбарис (г)": "5 *",
                "Часник головка (шт)": "1 *", "Родзинки (г)": "15 *", "Гострий перець (шт)": "0 !"
            },
            "Салат Цезар": {
                "Куряче філе (г)": "100 $", "Листя салату (г)": "80 &", "Пармезан (г)": "20 &",
                "Сухарики (г)": "15 *", "Соус Цезар (г)": "30 *", "Томати чері (шт)": "4 *",
                "Перепелині яйця (шт)": "3 *", "Бекон хрусткий (г)": "0 !"
            },
            "Стейк Рибай": {
                "Мармурова яловичина (г)": "300 $", "Вершкове масло (г)": "20 &", "Розмарин (гілочка)": "1 *",
                "Часник (част)": "2 *", "Соус Барбекю (г)": "0 !", "Соус Грибний (г)": "0 !", "Спаржа на грилі (г)": "0 !"
            },
            "Суп томатний": {
                "Tomaty (g)": "200 $", "Bazylik (g)": "5 &", "Grinky (sht)": "2 *",
                "Oliya (ml)": "10 &", "Parmezan (g)": "10 *", "Chasnyk (ch)": "1 *", "Mocarela (g)": "0 !"
            },
            "Деруни зі сметаною": {
                "Картопля (г)": "250 $", "Цибуля (г)": "30 &", "Сметана (г)": "50 *",
                "Смажена цибуля (г)": "20 *", "Гриби смажені (г)": "0 !", "Шкварки (г)": "0 !"
            },
            "Вареники з капустою": {
                "Тісто (г)": "150 $", "Tuшкована капуста (г)": "150 $", "Цибулева засмажка (г)": "40 &",
                "Сметана (г)": "50 *", "Шкварки (г)": "0 !"
            },
            "Пельмені домашні": {
                "Мікс фаршу (г)": "150 $", "Тісто (г)": "120 $", "Вершкове масло (г)": "15 &",
                "Сметана (г)": "40 *", "Оцет (мл)": "0 !", "Гірчиця (г)": "0 !", "Зелень кріп (г)": "5 *"
            },
            "Шашлик свинячий": {
                "Svyanyaj oshyik (g)": "200 $", "Marynovana cybulya (g)": "50 &", "Sous (g)": "40 *",
                "Lavash (шт)": "1 *", "Kynza (g)": "0 !", "Perec (g)": "0 !"
            },
            "Котлета по-київськи": {
                "Kuryache file (g)": "150 $", "Vershkove maslo (g)": "30 $", "Panirovka (g)": "20 &",
                "Krip (g)": "5 &", "Pyure (g)": "0 !", "Goroshok (g)": "0 !"
            }
        }

        # 6. Таблиця IngredientPrices: Матриця вартості грама/одиниці продукту для кожної страви
        self.dish_ingredients_price_matrix = {}
        
        # 7. Таблиця IngredientsPool: Загальний глобальний перелік усіх можливих складників (list of str)
        self.global_ingredients_pool = []

        # 8. Нова колонка/таблиця глобальних цін інгредієнтів (перенесено з Prisma)
        self.global_ingredients_prices = {
            "Яловичина (г)": 0.60,
            "Буряк (г)": 0.10,
            "Капуста (г)": 0.08,
            "Картопля (г)": 0.10,
            "Сметана (г)": 0.40,
            "Пампушки (шт)": 8.00,
            "Часник (част)": 1.50,
            "Зелень (г)": 0.70,
            "Сало (г)": 0.90,
            "Цибуля зелена (г)": 0.50,
            "Квасоля (г)": 0.35,
            "Перець чилі (шт)": 6.00,
            "Рис (г)": 0.20,
            "Телятина (г)": 0.75,
            "Mорква (г)": 0.12, 
            "Цибуля (г)": 0.08,
            "Зіра (г)": 1.50,
            "Барбарис (г)": 2.00,
            "Часник головка (шт)": 7.00,
            "Родзинки (г)": 0.50,
            "Гострий перець (шт)": 4.50,
            "Куряче філе (г)": 0.65,
            "Листя салату (г)": 0.30,
            "Пармезан (г)": 1.10,
            "Сухарики (г)": 0.20,
            "Соус Цезар (г)": 0.50,
            "Томати чері (шт)": 3.50,
            "Перепелині яйця (шт)": 4.00,
            "Бекон хрусткий (г)": 0.85,
            "Мармурова яловичина (г)": 1.05,
            "Вершкове масло (г)": 0.50,
            "Розмарин (гілочка)": 10.00,
            "Соус Барбекю (г)": 0.40,
            "Соус Грибний (г)": 0.45,
            "Спаржа на грилі (г)": 0.90
        }

    async def connect_db(self):
        """Підключається до бази даних PostgreSQL"""
        await self.db.connect()
        print("Модель успішно підключена до PostgreSQL!")
        
        # =====================================================================
        # 1. ЗАВАНТАЖЕННЯ СТРАВ ТА НАПОЇВ
        # =====================================================================
        all_dishes = await self.db.dish.find_many()
        
        self.menu_data["Страви"] = {}
        self.menu_data["Напої"] = {}
        
        drinks_list = ["Кава", "Чай", "Кола", "Лимонад", "Сік", "Еспресо", "Капучино"]
        
        for dish in all_dishes:
            if dish.Dish_name in drinks_list:
                self.menu_data["Напої"][dish.Dish_name] = float(dish.Price)
            else:
                self.menu_data["Страви"][dish.Dish_name] = float(dish.Price)
            
        print("Меню успішно завантажено та розсортовано!")

        # =====================================================================
        # 2. НОВИЙ БЛОК: ЗАВАНТАЖЕННЯ ІНГРЕДІЄНТІВ ТА ЇХНІХ ЦІН З БД
        # =====================================================================
        self.global_ingredients_pool = []
        
        correct_prices_dict = {
            "Яловичина (г)": 0.60, "Буряк (г)": 0.10, "Капуста (г)": 0.08, "Картопля (г)": 0.10,
            "Сметана (г)": 0.40, "Пампушки (шт)": 8.00, "Часник (част)": 1.50, "Зелень (г)": 0.70,
            "Сало (г)": 0.90, "Цибуля зелена (г)": 0.50, "Квасоля (г)": 0.35, "Перець чилі (шт)": 6.00,
            "Рис (г)": 0.20, "Телятина (г)": 0.75, "Mорква (г)": 0.12, "Цибуля (г)": 0.08,
            "Зіра (г)": 1.50, "Барбарис (г)": 2.00, "Часник головка (шт)": 7.00, "Родзинки (г)": 0.50,
            "Гострий перець (шт)": 4.50, "Куряче філе (г)": 0.65, "Листя салату (г)": 0.30,
            "Пармезан (г)": 1.10, "Сухарики (г)": 0.20, "Соус Цезар (г)": 0.50, "Томати чері (шт)": 3.50,
            "Перепелині яйця (шт)": 4.00, "Бекон хрусткий (г)": 0.85, "Мармурова яловичина (г)": 1.05,
            "Вершкове масло (г)": 0.50, "Розмарин (гілочка)": 10.00, "Соус Барбекю (г)": 0.40,
            "Соус Грибний (г)": 0.45, "Спаржа на грилі (г)": 0.90
        }

        all_ingredients = await self.db.ingredient.find_many()

        for ing in all_ingredients:
            ing_name = ing.Ing_name  
            db_price = float(ing.Ing_price)
            self.global_ingredients_pool.append(ing_name)
            
            correct_price = correct_prices_dict.get(ing_name, 0.50)
            
            if db_price != correct_price:
                await self.db.ingredient.update_many(
                    where={"Ing_name": ing_name},  
                    data={"Ing_price": correct_price}
                )
                print(f"Базу оновлено: {ing_name} = {correct_price} грн")
                self.global_ingredients_prices[ing_name] = correct_price
            else:
                self.global_ingredients_prices[ing_name] = db_price

        # =====================================================================
        # 3. АВТОМАТИЧНА СИНХРОНІЗАЦІЯ РЕЦЕПТІВ З БАЗОЮ ДАНИХ
        # =====================================================================

        all_recipe_items = await self.db.recipeitem.find_many()
        
        # Якщо в БД ще немає рецептів, записуємо їх туди з нашого словника (один раз)
        if not all_recipe_items:
            print("Ініціалізація рецептів у базі даних...")
            for dish_name, ingredients in self.dish_ingredients_matrix.items():
                for ing_name, meta in ingredients.items():
                    await self.db.recipeitem.create(
                        data={
                            "dish_name": dish_name,
                            "ing_name": ing_name,
                            "meta_data": meta
                        }
                    )
            print("Матрицю рецептів успішно збережено в PostgreSQL")
        else:
            self.dish_ingredients_matrix = {}
            
            for category in self.menu_data.values():
                for d_name in category:
                    self.dish_ingredients_matrix[d_name] = {}
                    
            for item in all_recipe_items:
                if item.dish_name not in self.dish_ingredients_matrix:
                    self.dish_ingredients_matrix[item.dish_name] = {}
                self.dish_ingredients_matrix[item.dish_name][item.ing_name] = item.meta_data

    async def disconnect_db(self):
        """Відключається від бази даних"""
        if self.db.is_connected():
            await self.db.disconnect()

    # =========================================================================
    # Р О З Д І Л  1 та 2:  У П Р А В Л І Н Н Я  М Е Н Ю  Т А  Р Е Ц Е П Т У Р О Ю
    # =========================================================================

    def rename_dish_in_database(self, old_name, new_name):
        """Зміна назви страви у всіх словниках та базі даних PostgreSQL"""
        new_name = new_name.strip()
        if not new_name or old_name == new_name:
            return
            
        # 1. Переносю дані в нові ключі у словниках оперативної пам'яті
        for category in self.menu_data:
            if old_name in self.menu_data[category]:
                # Бераю всі дані зі старої назви і кладемо в нову, а стару стираємо
                self.menu_data[category][new_name] = self.menu_data[category].pop(old_name)
                break
                
        if old_name in self.dish_cooking_time:
            self.dish_cooking_time[new_name] = self.dish_cooking_time.pop(old_name)
        if old_name in self.descriptions:
            self.descriptions[new_name] = self.descriptions.pop(old_name)
        if old_name in self.dish_ingredients_matrix:
            self.dish_ingredients_matrix[new_name] = self.dish_ingredients_matrix.pop(old_name)
            
        # Якщо ця страва зараз обрана в налаштуваннях - оновлюю вибір
        if getattr(self, 'selected_dish', None) == old_name:
            self.selected_dish = new_name
            
        # 2. Оновлюю дані назавжди в PostgreSQL
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_rename_dish(old_name, new_name))

    async def _async_rename_dish(self, old_name, new_name):
        """Асинхронний помічник для оновлення імені в усіх таблицях БД"""
        # Оновлюю ім'я у головній таблиці страв
        target = await self.db.dish.find_first(where={"Dish_name": old_name})
        if target:
            await self.db.dish.update(
                where={"Dish_id": target.Dish_id},
                data={"Dish_name": new_name}
            )
            
        # Каскадно оновлюю прив'язані рецепти в таблиці
        await self.db.recipeitem.update_many(
            where={"dish_name": old_name},
            data={"dish_name": new_name}
        )
        print(f"Назву страви успішно змінено: '{old_name}' -> '{new_name}'!")

    def change_global_ingredient_price(self, dish, ing, amount):
        """
        Ручна зміна вартості одного конкретного інгредієнта для вибраної страви.
        
        Аргументи:
            dish (str): Назва страви, в якій змінюється ціна складника.
            ing (str): Назва інгредієнта, ціну якого редагують.
            amount (float): Величина зміни (позитивна чи негативна, наприклад: +0.10 або -0.10).
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Виконати UPDATE вартості грама в таблиці інгредієнтів.
        Забезпечити нижній ліміт ціни (значення не може бути меншим або рівним 0.00).
        """
        pass


    def delete_ingredient_type_completely(self, ing_name):
        """Повне видалення інгредієнта з пулу, всіх рецептів та бази даних"""
        if ing_name in self.global_ingredients_pool:
            # 1. Видаляю з оперативної пам'яті
            self.global_ingredients_pool.remove(ing_name)
            if ing_name in self.global_ingredients_prices:
                del self.global_ingredients_prices[ing_name]
                
            # Видаляю цей інгредієнт з усіх локальних матриць рецептів страв
            for dish in self.dish_ingredients_matrix:
                if ing_name in self.dish_ingredients_matrix[dish]:
                    del self.dish_ingredients_matrix[dish][ing_name]

            # 2. Видаляю з бази даних PostgreSQL
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_delete_ingredient(ing_name))

    async def _async_delete_ingredient(self, ing_name):
        """Асинхронний помічник для видалення інгредієнта з усього коду БД"""
        # Видаляю згадки інгредієнта з усіх технологічних карт страв
        await self.db.recipeitem.delete_many(where={"ing_name": ing_name})
        # Видаляю сам інгредієнт з таблиці Ingredient
        await self.db.ingredient.delete_many(where={"Ing_name": ing_name})
        print(f"Інгредієнт '{ing_name}' повністю стерто з бази даних ресторану!")
    

    def change_global_dish_base_price(self, category, dish, amount):
        """Зміна базової вартості страви в меню з оновленням у БД"""
        if category in self.menu_data and dish in self.menu_data[category]:
            old_price = self.menu_data[category][dish]
            new_price = max(5.0, old_price + amount)  # Не даю ціні впасти нижче 5 грн
            
            # 1. Оновлюю ціну в оперативній пам'яті
            self.menu_data[category][dish] = float(new_price)
            
            # 2. Відправляю нову ціну в PostgreSQL
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_update_dish_price(dish, new_price))

    async def _async_update_dish_price(self, dish_name, new_price):
        """Асинхронний помічник для збереження нової ціни страви"""
        target_dish = await self.db.dish.find_first(where={"Dish_name": dish_name})
        if target_dish:
            await self.db.dish.update(
                where={"Dish_id": target_dish.Dish_id},
                data={"Price": float(new_price)}
            )
            print(f"Базу оновлено: {dish_name} тепер коштує {new_price} грн!")

    def change_global_cooking_time(self, dish, amount):
        """Редагування базового часу приготування страви"""
        # Якщо страви ще немає в словнику, даю їй базові 20 хвилин
        if dish not in self.dish_cooking_time:
            self.dish_cooking_time[dish] = 20
            
        # Змінюю час, але не дозволяюзробити його меншим за 1 хвилину
        self.dish_cooking_time[dish] = max(1, self.dish_cooking_time[dish] + amount)

    def delete_dish_from_menu_completely(self, dish):
        """Повне видалення страви з меню, її рецептів та бази даних"""
        
        # 1. Автоматично шукаю страву в категоріях і видаляю з пам'яті
        for category in self.menu_data:
            if dish in self.menu_data[category]:
                del self.menu_data[category][dish]
                break
                
        if dish in self.dish_cooking_time:
            del self.dish_cooking_time[dish]
        if dish in self.descriptions:
            del self.descriptions[dish]
        
        self.dish_ingredients_matrix[dish] = {}

        # 2. Видаляю з бази даних PostgreSQL
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_delete_dish(dish))

    async def _async_delete_dish(self, dish_name):
        """Асинхронний помічник для очищення таблиць у БД"""
        # Спочатку видаляю всі складники цієї страви з таблиці рецептів
        await self.db.recipeitem.delete_many(where={"dish_name": dish_name})
        # Тепер видаляю саму страву з таблиці Dish
        await self.db.dish.delete_many(where={"Dish_name": dish_name})
        print(f"Страва '{dish_name}' та її рецепти повністю видалені з PostgreSQL!")

    def change_default_ingredient_amount(self, dish, ing_name, amount):
        """Зміна кількості грамів/штук у Налаштуваннях з оновленням у БД"""
        if dish in self.dish_ingredients_matrix and ing_name in self.dish_ingredients_matrix[dish]:
            meta_str = self.dish_ingredients_matrix[dish][ing_name]
            val_str, symbol = meta_str.split()
            
            # Не дозволяю опустити базову кількість нижче 0
            new_val = max(0, int(val_str) + amount)
            new_meta = f"{new_val} {symbol}"
            
            self.dish_ingredients_matrix[dish][ing_name] = new_meta
            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_update_recipe(dish, ing_name, new_meta))

    async def _async_update_recipe(self, dish_name, ing_name, new_meta):
        target = await self.db.recipeitem.find_first(
            where={"dish_name": dish_name, "ing_name": ing_name}
        )
        if target:
            await self.db.recipeitem.update(
                where={"id": target.id},
                data={"meta_data": new_meta}
            )
            print(f"Рецепт оновлено в БД: {dish_name} -> {ing_name}: {new_meta}")

    def remove_ingredient_from_default_dish(self, dish_name, ing_name):
        """
        Тимчасове виключення необов'язкового складника з дефолтного рецепту страви (Пункт 2.3.1 ТЗ).
        
        Аргументи:
            dish_name (str): Назва страви.
            ing_name (str): Назва інгредієнта.
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Оновити запис у таблиці рецептур Recipes для цього інгредієнта, 
        встановивши маркер деактивації порції ('0 !'). Повністю видаляти рядок не можна, 
        щоб адмін міг у майбутньому знову підключити цей складник через панель додавання.
        """
        pass

    def add_ingredient_to_default_dish(self, dish, ing_name):
        """Додавання абсолютно нового складника до Налаштувань з оновленням у БД"""
        if not dish: return
        if dish not in self.dish_ingredients_matrix:
            self.dish_ingredients_matrix[dish] = {}
            
        if ing_name not in self.dish_ingredients_matrix[dish]:
            new_meta = "0 *"
            self.dish_ingredients_matrix[dish][ing_name] = new_meta
            
            # Додаємо запис у БД
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_add_recipe_item(dish, ing_name, new_meta))

    async def _async_add_recipe_item(self, dish_name, ing_name, new_meta):
        await self.db.recipeitem.create(
            data={
                "dish_name": dish_name,
                "ing_name": ing_name,
                "meta_data": new_meta
            }
        )
        print(f"В базу рецептів додано: {dish_name} -> {ing_name}")

    def add_new_ingredient_type(self, name):
        """Створення абсолютно нового типу інгредієнта з оновленням у БД"""
        # Перевіряю, чи немає вже такого інгредієнта у списку
        if not name.strip() or name in self.global_ingredients_pool:
            return
            
        # 1. Записую в оперативну пам'ять
        self.global_ingredients_pool.append(name)
        self.global_ingredients_prices[name] = 0.50 # Дефолтна ціна 0.50 грн за одиницю
        
        # 2. Зберігаю інгредієнт у базу даних PostgreSQL
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_add_ingredient_to_db(name))

    async def _async_add_ingredient_to_db(self, ing_name):
        """Асинхронний помічник для створення інгредієнта"""
        await self.db.ingredient.create(
            data={
                "Ing_name": ing_name,
                "Ing_price": 0.50
            }
        )
        print(f"Новий інгредієнт '{ing_name}' додано до бази даних!")

    def add_new_dish_to_menu(self, name):
        """Створення та ініціалізація нової страви в меню з оновленням у БД"""
        # Перевіряю, чи назва не порожня і чи немає вже такої страви
        if not name.strip() or name in self.menu_data["Страви"]:
            return
            
        # 1. Записую в оперативну пам'ять (щоб візуал оновився миттєво)
        self.menu_data["Страви"][name] = 100.0  # Дефолтна ціна (100 грн)
        self.dish_cooking_time[name] = 20       # Дефолтний час приготування
        self.descriptions[name] = ["Кастомна страва від Адміністратора."]
        self.dish_ingredients_matrix[name] = {}
        
        # 2. Зберігаю нову страву в базу даних PostgreSQL
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_add_dish_to_db(name))

    async def _async_add_dish_to_db(self, dish_name):
        """Асинхронний помічник для створення страви"""
        await self.db.dish.create(
            data={
                "Dish_name": dish_name,
                "Price": 100.0,
                "Cooking_time": 20
            }
        )
        print(f"Нову страву '{dish_name}' додано до бази даних!")


    # =========================================================================
    # Р О З Д І Л  3:  У П Р А В Л І Н Н Я  З А М О В Л Е Н Н Я М И  (К О Ш И К)
    # =========================================================================

    def change_table_number(self, amount):
        """
        Зміна номера столика для поточного робочого процесу оформлення (Пункт 3.3.3 ТЗ).
        Обмежує діапазон столиків від 1 до 20.
        
        Аргументи:
            amount (int): Напрямок зміни стола (+1 або -1).
        Повертає:
            None (Оновлює self.current_table_num локально)
        """
        self.current_table_num += amount
        if self.current_table_num < 1: self.current_table_num = 1
        if self.current_table_num > 20: self.current_table_num = 20

    async def select_dish(self, dish_name):
        self.current_extra_price = 0.0
        self.selected_dish = dish_name
        self.current_dish_ingredients = []

        # логіка пошуку страви в базі даних, схожа на попередні

        dish = await self.db.dish.find_unique(
            where = {"Dish_name" : dish_name}
        )
        if not dish:
            return
        
        links = await self.db.dishingredient.find_many(
            where = {"DishId" : dish.Dish_id}
        )
        
        for link in links:
            ingredient = await self.db.ingredient.find_unique(
                where = {"Ingredient_id" : link.IngredientId}
            )
        
            if ingredient:
                self.current_dish_ingredients.append({
                    "name" : ingredient.Ing_name,
                    "count" : 50,
                    "symbol" : "*"
                })

    def load_dish_from_snapshot(self, snapshot):
        """
        Завантаження збереженого зліпка страви з кошика назад у робочу область для редагування компонентів.
        Викликається, коли користувач клікає по страві всередині свого кошика замовлення.
        
        Аргументи:
            snapshot (dict): Словник-зліпок стану страви, який містить її назву та кастомні кількості.
        Повертає:
            None (Ініціалізує self.current_dish_ingredients кастомними грамами зі зліпка)
            
        БЕКЕНД-ЗАДАЧА: Зчитати назву страви зі зліпка, підняти її базову структуру рецепту з Recipes.
        Якщо інгредієнт присутній у кастомному зліпку — завантажити його вагу звідти, інакше — взяти дефолт бази.
        """
        self.selected_dish = snapshot["DISH_NAME"]
        self.current_dish_ingredients = []
        pass

    def get_current_dish_price(self):
        # Якщо страву не вибрано - сума 0
        if not getattr(self, 'selected_dish', None): 
            return 0.0
            
        # Беремо "відкалібровані" ціни для рідних інгредієнтів страви
        price_rules = getattr(self, 'dish_ingredients_price_matrix', {}).get(self.selected_dish, {})
        total = 0.0
        
        for ing in self.current_dish_ingredients:
            name = ing["name"]
            count = ing["count"]
            
            # 1. Якщо це рідний інгредієнт рецепту
            if name in price_rules:
                price = price_rules[name]
                
            # 2. Якщо це "чужий" інгредієнт (доданий з правої панелі)
            # Беремо його РЕАЛЬНУ ціну з бази даних
            elif hasattr(self, 'global_ingredients_prices') and name in self.global_ingredients_prices:
                price = self.global_ingredients_prices[name]
                
            # 3. Підстраховка на випадок збою
            else:
                price = 0.50
                
            total += count * price
            
        return round(total, 2)

    def save_current_dish_snapshot(self, index=None):
        """
        Збереження поточної сконфігурованої страви зі своїми кастомними грамами в тимчасовий кошик замовлення.
        
        Аргументи:
            index (int, optional): Якщо задано — індекс існуючої страви в кошику, яку ми перезаписуємо при кастомізації.
                                  Якщо None — страва додається в кошик як нова позиція.
        Повертає:
            None (Оновлює масив списку self.basket_dishes)
        """
        if not self.selected_dish: return
        snapshot = {"DISH_NAME": self.selected_dish}
        for ing in self.current_dish_ingredients: 
            snapshot[ing["name"]] = ing["count"]
        snapshot["FACT_PRICE"] = self.get_current_dish_price()
        
        if index is not None and 0 <= index < len(self.basket_dishes): 
            self.basket_dishes[index] = snapshot
        else: 
            self.basket_dishes.append(snapshot)

    def remove_dish_from_order(self, index):
        """
        Видалення однієї вибраної страви з тимчасового кошика поточного замовлення (Пункт 3.3.1 ТЗ).
        
        Аргументи:
            index (int): Порядковий індекс елемента в масиві списку кошика котролера.
        Повертає:
            None (Видаляє об'єкт із self.basket_dishes)
        """
        if 0 <= index < len(self.basket_dishes): 
            self.basket_dishes.pop(index)

    def get_total_order_price(self):
        """
        Розрахунок повної сумарної вартості всього поточного кошика (Пункт 3.3.2 ТЗ).
        
        Аргументи:
            None
        Повертає:
            float: Загальна сума вартості всіх кастомізованих страв у кошику.
        """
        return sum(snapshot["FACT_PRICE"] for snapshot in self.basket_dishes)

    def load_order_for_editing(self, order_id):
        """Завантажує архівне замовлення назад у робочий кошик"""
        if order_id in self.my_orders_database:
            order_data = self.my_orders_database[order_id]
            
            # 1. Відновлюємо номер столика
            self.current_table_num = order_data["table"]
            
            # 2. Перекидаємо страви з чека у тимчасовий кошик контролера
            import copy
            self.basket_dishes = copy.deepcopy(order_data["dishes"])
            
            print(f"Замовлення №{order_id} відкрито для редагування!")
            return True
            
        return False

    def save_edited_order(self, order_id):
        """
        Фіксація та перезапис раніше піднятого архівного замовлення новими зміненими даними (Пункт 3.3 ТЗ).
        
        Аргументи:
            order_id (int): Унікальний номер чека, який редагувався.
        Повертає:
            bool: True при успішному оновленні рядків у базі даних, False — у разі помилки.
            
        БЕКЕНД-ЗАДАЧА: Виконати комплексний UPDATE запит у таблиці замовлень для рядка order_id.
        Записати новий номер столика та оновлений список зліпків кастомізованих страв із кошика, після чого очистити кошик.
        """
        return False

    async def confirm_and_close_order(self):

        # 1. Перевіряємо, чи не порожній кошик. Якщо порожній - нічого зберігати.
        if not self.basket_dishes:
            return False

        # 2. Рахуємо загальну суму чека (викликаємо нашу синхронну функцію)
        total_price = self.get_total_order_price()

        # 3. Створюємо новий запис у таблиці Order (Замовлення)
        # Prisma автоматично генерує унікальний ID для цього чека
        new_order = await self.db.order.create(
            data={
                "Table_name": self.current_table_num,
                "Total_price": float(total_price),
                "Order_type": "IN_RESTAURANT"
            }
        )

        # 4. Перебираємо всі страви з кошика і прив'язуємо їх до цього чека
        for item in self.basket_dishes:
            dish_name = item["DISH_NAME"]
            
            # Знаходимо ID страви за назвою
            dish = await self.db.dish.find_unique(
                where={"Dish_name": dish_name}
            )
            
            if dish:
                # Записуємо позицію в таблицю OrderItem (зв'язок чека і страви)
                await self.db.orderitem.create(
                    data = {
                        "OrderId": new_order.Order_id,
                        "DishId": dish.Dish_id,
                        "Quantity": 1
                    }
                )

        # 5. Очищаємо кошик і скидаємо столик для наступного клієнта
        self.basket_dishes = []
        self.current_table_num = 7
        
        print(f"Замовлення №{new_order.Order_id} успішно збережено в базу!")
        return True

    def delete_order_by_id(self, order_id):
        """Синхронний міст для Pygame для видалення чека"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_delete_order(order_id))

    async def _async_delete_order(self, order_id):
        """Асинхронно видаляє чек та всі його страви з бази"""

        await self.db.orderitem.delete_many(where={"OrderId": order_id})
        
        await self.db.order.delete(where={"Order_id": order_id})
        print(f"Замовлення №{order_id} назавжди видалено з бази!")

    def get_order_keys(self):
        """
        Отримання впорядкованого списку ідентифікаторів усіх зареєстрованих замовлень (Пункт 3.4 ТЗ).
        
        Аргументи:
            None
        Повертає:
            list of int: Відсортований список унікальних номерів чеків, наявних в архіві бази даних.
            
        БЕКЕНД-ЗАДАЧА: Виконати SELECT id FROM Orders ORDER BY id ASC. Повернути отриманий чистий масив.
        """
        return []


    # =========================================================================
    # Р О З Д І Л  4:  Ф І Л Ь Т Р А Ц І Я  Т А  «Ж И В И Й»  П О Ш У К
    # =========================================================================

    def get_available_ingredients(self):
        base_pool = [
            "Яловичина (г)", "Буряк (г)", "Капуста (г)", "Картопля (г)", "Сметана (г)", 
            "Пампушки (шт)", "Часник (част)", "Зелень (г)", "Сало (г)", "Цибуля зелена (г)", 
            "Квасоля (г)", "Перець чилі (шт)", "Рис (г)", "Телятина (г)", "Mорква (г)", 
            "Цибуля (г)", "Зіра (г)", "Барбарис (г)", "Часник головка (шт)", "Родзинки (г)", 
            "Гострий перець (шт)", "Куряче філе (г)", "Листя салату (г)", "Пармезан (г)", 
            "Сухарики (г)", "Соус Цезар (г)", "Томати чері (шт)", "Перепелині яйця (шт)", 
            "Бекон хрусткий (г)", "Мармурова яловичина (г)", "Вершкове масло (г)", 
            "Розмарин (гілочка)", "Соус Барбекю (г)", "Соус Грибний (г)", "Спаржа на грилі (г)"
        ]
        
        all_possible = getattr(self, 'global_ingredients_pool', base_pool)
        
        if not all_possible:
            all_possible = base_pool

        already_added = []
        if hasattr(self, 'current_dish_ingredients'):
            for ing in self.current_dish_ingredients:
                already_added.append(ing.get('name', ''))
                
        available = []

        for ing in all_possible:
            if ing not in already_added:
                available.append(ing)

        return sorted(available)


    def add_ingredient_back(self, ing_name):
        if not self.selected_dish:
            return
            
        start_count = 50 if "(г)" in ing_name else 10
            
        if ing_name in self.dish_ingredients_matrix.get(self.selected_dish, {}):
            meta = self.dish_ingredients_matrix[self.selected_dish][ing_name]
            val_str, symbol = meta.split()
            self.current_dish_ingredients.append({"name": ing_name, "count": start_count, "symbol": symbol})
        else:
            self.current_dish_ingredients.append({"name": ing_name, "count": start_count, "symbol": "*"})

    def change_ingredient_count(self, idx, amount):
        if 0 <= idx < len(self.current_dish_ingredients):
            old_count = self.current_dish_ingredients[idx]['count']
            self.current_dish_ingredients[idx]['count'] += amount
            
            if self.current_dish_ingredients[idx]['count'] < 0:
                self.current_dish_ingredients[idx]['count'] = 0
                
            actual_difference = self.current_dish_ingredients[idx]['count'] - old_count
            
            price_per_unit = 0.5 
            
            if not hasattr(self, 'current_extra_price'):
                self.current_extra_price = 0.0
                
            self.current_extra_price += actual_difference * price_per_unit
    def get_filtered_order_keys(self, query):
        """Синхронний міст для Pygame, щоб дочекатися базу даних"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._fetch_orders_from_db(query))

    async def _fetch_orders_from_db(self, query):
        """Асинхронно витягує всі чеки з PostgreSQL та готує їх для візуалу"""
        self.my_orders_database = {}
    
        all_orders = await self.db.order.find_many()
        
        valid_keys = []
        
        for order in all_orders:
            order_id = order.Order_id
            table_num = order.Table_name if order.Table_name else 0
            
            # Шукаємо страви, які належать саме цьому чеку
            items = await self.db.orderitem.find_many(where={"OrderId": order_id})
            
            dishes_list = []
            for item in items:
                # Знаходимо інформацію про страву за її ID
                dish = await self.db.dish.find_unique(where={"Dish_id": item.DishId})
                if dish:
                    # Пакуємо так, як цього очікує візуал
                    dishes_list.append({
                        "DISH_NAME": dish.Dish_name,
                        "FACT_PRICE": float(dish.Price) * item.Quantity
                    })
            
            self.my_orders_database[order_id] = {
                "table": table_num,
                "dishes": dishes_list
            }
            
            if not query:
                valid_keys.append(order_id)
            else:
                if str(table_num) == query:
                    valid_keys.append(order_id)
                elif any(query.lower() in d["DISH_NAME"].lower() for d in dishes_list):
                    valid_keys.append(order_id)
                    
        valid_keys.sort()
        return valid_keys