import copy

class RestaurantModel:
    def __init__(self):
        # База даних замовлень: { order_id: {"table": X, "dishes": [...] } }
        self.my_orders_database = {}
        self.next_order_id = 1
        self.current_table_num = 7
        
        self.menu_data = {
            "Страви": {
                "Борщ український": 120, 
                "Плов з телятиною": 150, 
                "Салат Цезар": 140, 
                "Стейк Рибай": 350,
                "Суп томатний": 95,
                "Деруни зі сметаною": 85,
                "Вареники з капустою": 75,
                "Пельмені домашні": 110,
                "Шашлик свинячий": 180,
                "Котлета по-київськи": 130
            },
            "Напої": {
                "Сік яблучний": 40, 
                "Вода мінеральна": 25, 
                "Кола склянка": 35,
                "Капучино": 50,
                "Еспресо": 35,
                "Чай зелений": 40,
                "Лимонад імбирний": 60,
                "Тонік": 45
            }
        }

        # Базовий час приготування страв у хвилинах
        self.dish_cooking_time = {
            "Борщ український": 25, "Плов з телятиною": 35, "Салат Цезар": 15,
            "Стейк Рибай": 20, "Суп томатний": 15, "Деруни зі сметаною": 20,
            "Вареники з капустою": 15, "Пельмені домашні": 15, "Шашлик свинячий": 25,
            "Котлета по-київськи": 20
        }
        
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

        self.dish_ingredients_price_matrix = {
            "Борщ український": {
                "Яловичина (г)": 0.60, "Буряк (г)": 0.10, "Капуста (г)": 0.08, "Картопля (г)": 0.10,
                "Сметана (г)": 0.40, "Пампушки (шт)": 8.00, "Часник (част)": 1.50, "Зелень (г)": 0.70,
                "Сало (г)": 0.90, "Цибуля зелена (г)": 0.50, "Квасоля (г)": 0.35, "Перець чилі (шт)": 6.00
            },
            "Плов з телятиною": {
                "Рис (г)": 0.20, "Телятина (г)": 0.75, "Морква (г)": 0.12, "Цибуля (г)": 0.08,
                "Зіра (г)": 1.50, "Барбарис (г)": 2.00, "Часник головка (шт)": 7.00, "Родзинки (г)": 0.50,
                "Гострий перець (шт)": 4.50
            },
            "Салат Цезар": {
                "Куряче філе (г)": 0.65, "Листя салату (г)": 0.30, "Пармезан (г)": 1.10, "Сухарики (г)": 0.20,
                "Соус Цезар (г)": 0.50, "Томати чері (шт)": 3.50, "Перепелині яйця (шт)": 4.00, "Бекон хрусткий (г)": 0.85
            },
            "Стейк Рибай": {
                "Мармурова яловичина (г)": 1.05, "Вершкове масло (г)": 0.50, "Розмарин (гілочка)": 10.00,
                "Часник (част)": 2.00, "Соус Барбекю (г)": 0.40, "Соус Грибний (г)": 0.45, "Спаржа на грилі (г)": 0.90
            },
            "Суп томатний": {
                "Tomaty (g)": 0.30, "Bazylik (g)": 1.20, "Grinky (sht)": 4.50, "Oliya (ml)": 0.60, 
                "Parmezan (g)": 1.10, "Chasnyk (ch)": 1.50, "Mocarela (g)": 0.75
            },
            "Деруни зі сметаною": {
                "Картопля (г)": 0.15, "Цибуля (г)": 0.08, "Сметана (г)": 0.40, 
                "Смажена цибуля (г)": 0.30, "Гриби смажені (г)": 0.55, "Шкварки (г)": 0.70
            },
            "Вареники з капустою": {
                "Тісто (г)": 0.15, "Тушкована капуста (г)": 0.20, "Цибулева засмажка (г)": 0.35, 
                "Сметана (г)": 0.40, "Шкварки (г)": 0.70
            },
            "Пельмені домашні": {
                "Мікс фаршу (г)": 0.45, "Тісто (г)": 0.15, "Вершкове масло (г)": 0.50, 
                "Сметана (г)": 0.40, "Оцет (мл)": 0.30, "Гірчиця (г)": 0.35, "Зелень кріп (г)": 0.60
            },
            "Шашлик свинячий": {
                "Svyanyaj oshyik (g)": 0.70, "Marynovana cybulya (g)": 0.25, "Sous (g)": 0.40, 
                "Lavash (шт)": 12.00, "Kynza (g)": 0.80, "Perec (g)": 0.45
            },
            "Котлета по-київськи": {
                "Kuryache file (g)": 0.55, "Vershkove maslo (g)": 0.45, "Panirovka (g)": 0.15, 
                "Krip (g)": 0.60, "Pyure (g)": 0.15, "Goroshok (g)": 0.35
            }
        }
        
        self.global_ingredients_pool = [
            "Яловичина (г)", "Буряк (г)", "Капуста (г)", "Картопля (г)", "Сметана (г)", 
            "Пампушки (шт)", "Часник (част)", "Зелень (г)", "Сало (г)", "Цибуля зелена (г)", 
            "Квасоля (г)", "Перець чилі (шт)", "Рис (г)", "Телятина (г)", "Mорква (г)", 
            "Цибуля (г)", "Зіра (г)", "Барбарис (г)", "Часник головка (шт)", "Родзинки (г)", 
            "Гострий перець (шт)", "Куряче філе (г)", "Листя салату (г)", "Пармезан (г)", 
            "Сухарики (г)", "Соус Цезар (г)", "Томати чері (шт)", "Перепелині яйця (шт)", 
            "Бекон хрусткий (г)", "Мармурова яловичина (г)", "Вершкове масло (г)", 
            "Розмарин (гілочка)", "Соус Барбекю (г)", "Соус Грибний (г)", "Спаржа на грилі (г)"
        ]
        
        self.selected_category = "Страви"
        self.selected_dish = None
        self.current_dish_ingredients = [] 
        self.basket_dishes = []

        # АВТОКАЛІБРУВАННЯ
        for name, target_price in self.menu_data["Страви"].items():
            if name in self.dish_ingredients_matrix and name in self.dish_ingredients_price_matrix:
                current_sum = 0.0
                for ing_name, meta in self.dish_ingredients_matrix[name].items():
                    val_str, symbol = meta.split()
                    if symbol != '!' and ing_name in self.dish_ingredients_price_matrix[name]:
                        current_sum += int(val_str) * self.dish_ingredients_price_matrix[name][ing_name]
                
                if current_sum > 0:
                    start_k = target_price / current_sum
                    for ing_name in self.dish_ingredients_price_matrix[name]:
                        self.dish_ingredients_price_matrix[name][ing_name] = round(self.dish_ingredients_price_matrix[name][ing_name] * start_k, 4)

    def rename_dish_in_database(self, old_name, new_name):
        if not new_name.strip() or old_name == new_name:
            return
        for cat in self.menu_data:
            if old_name in self.menu_data[cat]:
                new_category_dict = {}
                for key, value in self.menu_data[cat].items():
                    if key == old_name:
                        new_category_dict[new_name] = value
                    else:
                        new_category_dict[key] = value
                self.menu_data[cat] = new_category_dict
        if old_name in self.dish_cooking_time:
            self.dish_cooking_time[new_name] = self.dish_cooking_time.pop(old_name)
        if old_name in self.descriptions:
            self.descriptions[new_name] = self.descriptions.pop(old_name)
        if old_name in self.dish_ingredients_matrix:
            self.dish_ingredients_matrix[new_name] = self.dish_ingredients_matrix.pop(old_name)
        if old_name in self.dish_ingredients_price_matrix:
            self.dish_ingredients_price_matrix[new_name] = self.dish_ingredients_price_matrix.pop(old_name)

        for order_id in self.my_orders_database:
            for snapshot in self.my_orders_database[order_id]["dishes"]:
                if snapshot["DISH_NAME"] == old_name:
                    snapshot["DISH_NAME"] = new_name

    def change_global_ingredient_price(self, dish, ing, amount):
        if dish in self.dish_ingredients_price_matrix and ing in self.dish_ingredients_price_matrix[dish]:
            self.dish_ingredients_price_matrix[dish][ing] = round(max(0.01, self.dish_ingredients_price_matrix[dish][ing] + amount), 2)

    def change_global_dish_base_price(self, category, dish, amount):
        if category in self.menu_data and dish in self.menu_data[category]:
            old_price = self.menu_data[category][dish]
            new_price = max(5, old_price + amount)
            self.menu_data[category][dish] = new_price
            
            k = new_price / old_price
            if dish in self.dish_ingredients_price_matrix:
                for ing in self.dish_ingredients_price_matrix[dish]:
                    self.dish_ingredients_price_matrix[dish][ing] = round(max(0.01, self.dish_ingredients_price_matrix[dish][ing] * k), 4)

    def change_global_cooking_time(self, dish, amount):
        if dish in self.dish_cooking_time:
            self.dish_cooking_time[dish] = max(1, self.dish_cooking_time[dish] + amount)

    def change_table_number(self, amount):
        self.current_table_num += amount
        if self.current_table_num < 1: self.current_table_num = 1
        if self.current_table_num > 20: self.current_table_num = 20

    def select_dish(self, dish_name):
        self.selected_dish = dish_name
        self.current_dish_ingredients = []
        if dish_name in self.dish_ingredients_matrix:
            for ing_name, meta in self.dish_ingredients_matrix[dish_name].items():
                val_str, symbol = meta.split()
                if symbol == '!': continue
                self.current_dish_ingredients.append({"name": ing_name, "count": int(val_str), "symbol": symbol})

    def load_dish_from_snapshot(self, snapshot):
        self.selected_dish = snapshot["DISH_NAME"]
        self.current_dish_ingredients = []
        if self.selected_dish in self.dish_ingredients_matrix:
            for ing_name, meta in self.dish_ingredients_matrix[self.selected_dish].items():
                val_str, symbol = meta.split()
                if ing_name in snapshot:
                    current_count = snapshot[ing_name]
                    if symbol in ['*', '!'] and current_count <= 0: continue
                    self.current_dish_ingredients.append({"name": ing_name, "count": current_count, "symbol": symbol})
                else:
                    if symbol in ['$', '&']:
                        self.current_dish_ingredients.append({"name": ing_name, "count": int(val_str), "symbol": symbol})

    def get_current_dish_price(self):
        if not self.selected_dish: return 0.0
        price_rules = self.dish_ingredients_price_matrix.get(self.selected_dish, {})
        total = 0.0
        for ing in self.current_dish_ingredients:
            name = ing["name"]
            count = ing["count"]
            if name in price_rules: total += count * price_rules[name]
        return total

    def save_current_dish_snapshot(self, index=None):
        if not self.selected_dish: return
        snapshot = {"DISH_NAME": self.selected_dish}
        for ing in self.current_dish_ingredients: snapshot[ing["name"]] = ing["count"]
        snapshot["FACT_PRICE"] = self.get_current_dish_price()
        if index is not None and 0 <= index < len(self.basket_dishes): self.basket_dishes[index] = snapshot
        else: self.basket_dishes.append(snapshot)

    def remove_dish_from_order(self, index):
        if 0 <= index < len(self.basket_dishes): self.basket_dishes.pop(index)

    def get_total_order_price(self):
        return sum(snapshot["FACT_PRICE"] for snapshot in self.basket_dishes)

    def load_order_for_editing(self, order_id):
        if order_id in self.my_orders_database:
            order_info = self.my_orders_database[order_id]
            self.current_table_num = order_info["table"]
            self.basket_dishes = copy.deepcopy(order_info["dishes"])
            return True
        return False

    def save_edited_order(self, order_id):
        if order_id in self.my_orders_database and self.basket_dishes:
            self.my_orders_database[order_id]["table"] = self.current_table_num
            self.my_orders_database[order_id]["dishes"] = self.basket_dishes
            self.basket_dishes = []
            return True
        return False

    def confirm_and_close_order(self):
        if self.basket_dishes:
            self.my_orders_database[self.next_order_id] = {"table": self.current_table_num, "dishes": self.basket_dishes}
            self.next_order_id += 1
            self.basket_dishes = []
            self.current_table_num = 7

    def delete_order_by_id(self, order_id):
        if order_id in self.my_orders_database: del self.my_orders_database[order_id]

    def get_order_keys(self):
        return sorted(list(self.my_orders_database.keys()))

    def get_available_ingredients(self):
        if not self.selected_dish or self.selected_dish not in self.dish_ingredients_matrix: 
            return []
        all_possible = set(self.dish_ingredients_matrix[self.selected_dish].keys())
        already_added = set(ing["name"] for ing in self.current_dish_ingredients)
        return sorted(list(all_possible - already_added))

    def add_ingredient_back(self, ing_name):
        if self.selected_dish and ing_name in self.dish_ingredients_matrix[self.selected_dish]:
            meta = self.dish_ingredients_matrix[self.selected_dish][ing_name]
            val_str, symbol = meta.split()
            self.current_dish_ingredients.append({"name": ing_name, "count": 1, "symbol": symbol})

    def change_ingredient_count(self, idx, amount):
        if 0 <= idx < len(self.current_dish_ingredients):
            ing = self.current_dish_ingredients[idx]
            if ing["symbol"] == "$": return
            new_count = ing["count"] + amount
            if ing["symbol"] == "&" and new_count < 1: new_count = 1
            if ing["symbol"] in ["*", "!"] and new_count <= 0:
                self.current_dish_ingredients.pop(idx)
                return
            ing["count"] = new_count

    def change_default_ingredient_amount(self, dish_name, ing_name, amount):
        if dish_name in self.dish_ingredients_matrix and ing_name in self.dish_ingredients_matrix[dish_name]:
            meta = self.dish_ingredients_matrix[dish_name][ing_name]
            val_str, symbol = meta.split()
            new_val = max(0, int(val_str) + amount)
            if new_val == 0 and symbol in ['*', '!']:
                self.dish_ingredients_matrix[dish_name][ing_name] = f"0 !"
            else:
                self.dish_ingredients_matrix[dish_name][ing_name] = f"{new_val} {symbol}"

    def remove_ingredient_from_default_dish(self, dish_name, ing_name):
        if dish_name in self.dish_ingredients_matrix and ing_name in self.dish_ingredients_matrix[dish_name]:
            meta = self.dish_ingredients_matrix[dish_name][ing_name]
            val_str, symbol = meta.split()
            if symbol in ['*', '!']:
                self.dish_ingredients_matrix[dish_name][ing_name] = f"0 !"

    def add_ingredient_to_default_dish(self, dish_name, ing_name):
        """Додавання інгредієнта до дефолтної рецептури із синхронним збільшенням ціни страви"""
        if dish_name in self.dish_ingredients_matrix:
            self.dish_ingredients_matrix[dish_name][ing_name] = f"50 *"
            if dish_name not in self.dish_ingredients_price_matrix:
                self.dish_ingredients_price_matrix[dish_name] = {}
            
            if ing_name not in self.dish_ingredients_price_matrix[dish_name]:
                self.dish_ingredients_price_matrix[dish_name][ing_name] = 0.50
            
            added_value = 50 * self.dish_ingredients_price_matrix[dish_name][ing_name]
            if "Страви" in self.menu_data and dish_name in self.menu_data["Страви"]:
                self.menu_data["Страви"][dish_name] = int(self.menu_data["Страви"][dish_name] + added_value)

    def add_new_ingredient_type(self, name):
        if name.strip() and name not in self.global_ingredients_pool:
            self.global_ingredients_pool.append(name)

    def add_new_dish_to_menu(self, name):
        if name.strip() and name not in self.menu_data["Страви"]:
            new_dishes_dict = {name: 100}
            for k, v in self.menu_data["Страви"].items():
                new_dishes_dict[k] = v
            self.menu_data["Страви"] = new_dishes_dict
            self.dish_cooking_time[name] = 20    
            self.descriptions[name] = ["Кастомна страва ресторану."]
            self.dish_ingredients_matrix[name] = {}
            self.dish_ingredients_price_matrix[name] = {}

    def delete_dish_from_menu_completely(self, name):
        for cat in self.menu_data:
            if name in self.menu_data[cat]:
                del self.menu_data[cat][name]
                break
        if name in self.dish_cooking_time: del self.dish_cooking_time[name]
        if name in self.descriptions: del self.descriptions[name]
        if name in self.dish_ingredients_matrix: del self.dish_ingredients_matrix[name]
        if name in self.dish_ingredients_price_matrix: del self.dish_ingredients_price_matrix[name]
        
        if self.selected_dish == name:
            self.selected_dish = None

    def get_filtered_order_keys(self, query):
        if not query.strip():
            return self.get_order_keys()
            
        filtered_keys = []
        q = query.lower().strip()
        
        for order_id, order_data in self.my_orders_database.items():
            if q == str(order_data["table"]):
                filtered_keys.append(order_id)
                continue
            for snapshot in order_data["dishes"]:
                if q in snapshot["DISH_NAME"].lower():
                    filtered_keys.append(order_id)
                    break
                    
        return sorted(filtered_keys)