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

        # 3. Таблиця DishConfigurations: Зберігає тривалість приготування страв { dish_name (str): minutes (int) }
        self.dish_cooking_time = {}
        
        # 4. Таблиця DishDescriptions: Текстові рядки описів страв для середньої колонки { dish_name (str): [lines] }
        self.descriptions = {}
        
        # 5. Таблиця Recipes: Технологічні карти страв { dish_name (str): { ing_name (str): "вартість_маркер" } }
        self.dish_ingredients_matrix = {}

        # 6. Таблиця IngredientPrices: Матриця вартості грама/одиниці продукту для кожної страви
        self.dish_ingredients_price_matrix = {}
        
        # 7. Таблиця IngredientsPool: Загальний глобальний перелік усіх можливих складників (list of str)
        self.global_ingredients_pool = []

    async def connect_db(self):
        """Підключається до бази даних PostgreSQL"""
        await self.db.connect()
        print("Модель успішно підключена до PostgreSQL!")
        
        all_dishes = await self.db.dish.find_many()
        
        # Очищаємо обидві категорії перед завантаженням
        self.menu_data["Страви"] = {}
        self.menu_data["Напої"] = {}
        
        # Створюємо "шпаргалку" для програми: які назви вважати напоями
        drinks_list = ["Кава", "Чай", "Кола", "Лимонад", "Сік", "Еспресо", "Капучино"]
        
        # Перебираємо всі записи з бази
        for dish in all_dishes:
            # Якщо назва є в нашому списку напоїв — кладемо у "Напої"
            if dish.Dish_name in drinks_list:
                self.menu_data["Напої"][dish.Dish_name] = float(dish.Price)
            # Усе інше вважаємо "Стравами"
            else:
                self.menu_data["Страви"][dish.Dish_name] = float(dish.Price)
            
        print("Меню успішно завантажено та розсортовано!")

    async def disconnect_db(self):
        """Відключається від бази даних"""
        if self.db.is_connected():
            await self.db.disconnect()

    # =========================================================================
    # Р О З Д І Л  1 та 2:  У П Р А В Л І Н Н Я  М Е Н Ю  Т А  Р Е Ц Е П Т У Р О Ю
    # =========================================================================

    def rename_dish_in_database(self, old_name, new_name):
        """
        Перейменування існуючої страви у базі даних (Пункт 2.3.2 ТЗ).
        
        Аргументи:
            old_name (str): Поточна унікальна назва страви (старий ключ).
            new_name (str): Нова текстова назва страви (новий ключ).
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Виконати UPDATE запит у таблицях меню, рецептів, описів та 
        інгредієнтів. Також каскадно оновити назву страви в архівних замовленнях, якщо потрібно.
        """
        pass

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

    def change_global_dish_base_price(self, category, dish, amount):
        """
        Зміна базової вартості страви в меню з пропорційним масштабуванням цін інгредієнтів (Пункт 2.3.3 ТЗ).
        
        Аргументи:
            category (str): Назва категорії, до якої належить страва ("Страви", "Напої"...).
            dish (str): Назва страви, ціну якої змінює адміністратор.
            amount (int): Величина кроку зміни ціни (наприклад: +5 або -5).
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: 
            1. Зчитати поточну ціну з таблиці меню.
            2. Вирахувати коефіцієнт зміни k = (стара_ціна + amount) / стара_ціна.
            3. Записати нову ціну страви у таблицю меню.
            4. Оновити таблицю IngredientPrices для цієї страви, помноживши ціну КОЖНОГО її інгредієнта на k.
        """
        pass

    def change_global_cooking_time(self, dish, amount):
        """
        Редагування базового часу приготування страви (Пункт 2.3.4 ТЗ).
        
        Аргументи:
            dish (str): Назва страви.
            amount (int): Крок зміни часу в хвилинах (наприклад: +1 або -1).
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Виконати UPDATE тривалості приготування у відповідній таблиці конфігурацій (мінімум 1 хв).
        """
        pass

    def delete_dish_from_menu_completely(self, name):
        """
        Повне каскадне видалення страви з меню ресторану (Пункт 2.2 ТЗ).
        
        Аргументи:
            name (str): Назва страви, яку видаляє адміністратор.
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Виконати каскадний DELETE запит. Видалити рядок страви з меню, 
        а також очистити пов'язані з нею записи в таблицях рецептур, цін інгредієнтів та описів.
        """
        pass

    def change_default_ingredient_amount(self, dish_name, ing_name, amount):
        """
        Зміна дефолтної (базової) кількості грамів/одиниць інгредієнта в рецепті (Пункт 1.3 ТЗ).
        
        Аргументи:
            dish_name (str): Назва страви.
            ing_name (str): Назва інгредієнта у складі страви.
            amount (int): Крок зміни кількості (наприклад: +10 або -10).
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Оновити числове значення ваги у полі метаданих таблиці рецептур Recipes. 
        Якщо вага зменшується до 0, а маркер типу інгредієнта є необов'язковим ('*' або '!'), 
        перевести його в режим прихованого деактивованого стану ('0 !').
        """
        pass

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

    def add_ingredient_to_default_dish(self, dish_name, ing_name):
        """
        Додавання нового складника до дефолтної технологічної карти страви (Пункт 2.3.1 ТЗ).
        Також автоматично коригує базову вартість страви, додаючи ціну нової порції.
        
        Аргументи:
            dish_name (str): Назва страви, в яку додають продукт.
            ing_name (str): Назва продукту із загального пулу глобальних інгредієнтів.
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: 
            1. Записати дефолтну початкову вагу і тип ('50 *') у таблицю Recipes для цієї страви.
            2. Перевірити наявність інгредієнта в таблиці цін IngredientPrices для цієї страви. Якщо немає — задати дефолт (наприклад, 0.50 грн/г).
            3. Вирахувати вартість доданої порції: 50г * ціна_за_грам.
            4. Виконати UPDATE базової вартості цієї страви в таблиці меню menu_data, додавши отриману вартість порції.
        """
        pass

    def add_new_ingredient_type(self, name):
        """
        Створення абсолютно нового типу інгредієнта в глобальній системі (Пункт 1.1 ТЗ).
        
        Аргументи:
            name (str): Назва нового продукту (наприклад: "Авокадо (г)").
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Виконати INSERT запит у глобальну таблицю/пул доступних інгредієнтів IngredientsPool.
        """
        pass

    def add_new_dish_to_menu(self, name):
        """
        Створення та первинна ініціалізація нової порожньої страви в меню (Пункт 2.1 ТЗ).
        
        Аргументи:
            name (str): Назва нової страви.
        Повертає:
            None
            
        БЕКЕНД-ЗАДАЧА: Виконати INSERT запису нової страви із дефолтною ціною (наприклад, 100 грн) у категорію меню.
        Створити супутні порожні або дефолтні рядки конфігурацій у таблицях часу приготування, описів та рецептур.
        """
        pass


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
        # Якщо страву не вибрано - ціна 0
        if not self.selected_dish: 
            return 0.0
            
        # Беру базову ціну з нашого словника, який ми завантажили при старті
        base_price = self.menu_data.get(self.selected_category, {}).get(self.selected_dish, 0.0)
        return float(base_price)

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
        """
        Отримання відсортованого списку інгредієнтів, які ще НЕ додані до поточної страви.
        Використовується для наповнення правої колонки доступних продуктів у режимі додавання складників.
        
        Аргументи:
            None
        Повертає:
            list of str: Перелік назв доступних для вибору продуктів із глобального пулу.
        """
        return []

    def add_ingredient_back(self, ing_name):
        """
        Повернення раніше видаленого необов'язкового інгредієнта назад до складу поточної робочої страви у CREATE.
        
        Аргументи:
            ing_name (str): Назва продукту.
        Повертає:
            None (Додає об'єкт конфігурації у self.current_dish_ingredients)
        """
        pass

    def change_ingredient_count(self, idx, amount):
        # Перевіряю, чи існує такий інгредієнт
        if 0 <= idx < len(self.current_dish_ingredients):
            # Змінюю його кількість
            self.current_dish_ingredients[idx]['count'] += amount
            
            # Вага не може бути меншою за нуль
            if self.current_dish_ingredients[idx]['count'] < 0:
                self.current_dish_ingredients[idx]['count'] = 0
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