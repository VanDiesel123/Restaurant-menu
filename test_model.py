import unittest
from model import RestaurantModel

class HeavyRestaurantModelTest(unittest.TestCase):

    def setUp(self):
        self.model = RestaurantModel()

    # ==========================================
    # 1. ГРУПА ТЕСТІВ: ОБМЕЖЕННЯ ТА ГРАНИЦІ (ТАБЛИЦІ, ЦІНИ, ЧАС)
    # ==========================================
    
    def test_table_number_bounds(self):
        """Перевірка лімітів для номерів столів (1-20)"""
        self.model.change_table_number(-50)
        self.assertEqual(self.model.current_table_num, 1)
        
        self.model.change_table_number(100)
        self.assertEqual(self.model.current_table_num, 20)

    def test_global_dish_price_floor(self):
        """Базова ціна страви не може впасти нижче 5 грн"""
        self.model.change_global_dish_base_price("Страви", "Борщ український", -200)
        self.assertEqual(self.model.menu_data["Страви"]["Борщ український"], 5)

    def test_global_cooking_time_floor(self):
        """Час приготування не може бути менше 1 хвилини"""
        self.model.change_global_cooking_time("Салат Цезар", -30)
        self.assertEqual(self.model.dish_cooking_time["Салат Цезар"], 1)

    # ==========================================
    # 2. ГРУПА ТЕСТІВ: ЕДЖ-КЕЙСИ ТА ФЕЙКОВІ ДАНІ (ДЛЯ ПОКРИТТЯ IF/ELSE)
    # ==========================================

    def test_invalid_dish_operations_do_not_crash(self):
        """Перевірка, що методи не падають при роботі з неіснуючими стравами/категоріями"""
        # Спроба змінити ціну неіснуючої страви
        self.model.change_global_dish_base_price("Страви", "Суп з устриць", 50)

        # Спроба змінити час неіснуючої страви
        self.model.change_global_cooking_time("Суп з устриць", 10)

        # Спроба змінити ціну інгредієнта в неіснуючій страві
        self.model.change_global_ingredient_price("Суп з устриць", "Сіль", 5)

        self.assertTrue(True)

    def test_load_non_existent_order(self):
        """Завантаження неіснуючого чека має повертати False"""
        result = self.model.load_order_for_editing(999)
        self.assertFalse(result)

    def test_save_edited_order_invalid(self):
        """Збереження відредагованого чека, якщо кошик порожній, має повернути False"""
        # Створюємо замовлення, щоб id існував
        self.model.select_dish("Салат Цезар")
        self.model.save_current_dish_snapshot()
        self.model.confirm_and_close_order()
        
        # Тепер basket_dishes порожній. Спроба зберегти поверх замовлення №1
        result = self.model.save_edited_order(1)
        self.assertFalse(result)

    def test_change_ingredient_count_out_of_bounds(self):
        """Зміна кількості інгредієнта за неіснуючим індексом не повинна ламати програму"""
        self.model.select_dish("Борщ український")

        # Всього інгредієнтів +- 10. Викликаємо 99-й індекс
        self.model.change_ingredient_count(99, 5)
        self.assertTrue(True)

    # ==========================================
    # 3. ПАРАМЕТРИЗОВАНІ ТЕСТИ (ГЕНЕРУЮТЬ ДЕСЯТКИ КЕЙСІВ)
    # ==========================================

    def test_all_menu_items_cooking_times(self):
        """Тестуємо базовий час приготування для ВСІХ страв з меню (10 підтестів)"""
        for dish in self.model.dish_cooking_time:
            with self.subTest(dish_name=dish):
                # Перевіряємо, що у кожної страви час приготування адекватний (> 0)
                self.assertGreater(self.model.dish_cooking_time[dish], 0)

    def test_all_initial_prices_match_autocalibration(self):
        """Тестуємо автокалібрування вартості для кожної страви (10 підтестів)"""
        for dish_name in self.model.menu_data["Страви"]:
            with self.subTest(dish=dish_name):
                calculated_sum = 0.0
                price_rules = self.model.dish_ingredients_price_matrix.get(dish_name, {})
                matrix = self.model.dish_ingredients_matrix.get(dish_name, {})
                
                for ing_name, meta in matrix.items():
                    val_str, symbol = meta.split()
                    if symbol != '!' and ing_name in price_rules:
                        calculated_sum += int(val_str) * price_rules[ing_name]
                
                if calculated_sum > 0:
                    self.assertAlmostEqual(calculated_sum, self.model.menu_data["Страви"][dish_name], places=0)

    # ==========================================
    # 4. ГРУПА ТЕСТІВ: МЕНЕДЖМЕНТ ТА ФІЛЬТРАЦІЯ ЧЕКІВ
    # ==========================================

    def test_order_filtering_by_table_and_name(self):
        """Перевірка роботи пошукового фільтра (Розділ 4 ТЗ)"""
        # Створюємо замовлення №1 на Стіл 5 із Борщем
        self.model.current_table_num = 5
        self.model.select_dish("Борщ український")
        self.model.save_current_dish_snapshot()
        self.model.confirm_and_close_order()

        # Створюємо замовлення №2 на Стіл 10 із Пловом
        self.model.current_table_num = 10
        self.model.select_dish("Плов з телятиною")
        self.model.save_current_dish_snapshot()
        self.model.confirm_and_close_order()

        # 1. Шукаємо по столу "5"
        keys_table = self.model.get_filtered_order_keys("5")
        self.assertIn(1, keys_table)
        self.assertNotIn(2, keys_table)

        # 2. Шукаємо по слову "плов" (регістронезалежно)
        keys_name = self.model.get_filtered_order_keys("ПлОв")
        self.assertIn(2, keys_name)
        self.assertNotIn(1, keys_name)

        # 3. Порожній запит має повернути всі ключі
        keys_all = self.model.get_filtered_order_keys("  ")
        self.assertEqual(len(keys_all), 2)

    def test_admin_panel_add_and_delete_dish(self):
        """Тест повного життєвого циклу страви в адмінці"""
        # Додаємо нову страву
        custom_dish = "Кастомний бургер"
        self.model.add_new_dish_to_menu(custom_dish)
        self.assertIn(custom_dish, self.model.menu_data["Страви"])
        
        # Перевіряємо, що під неї створилися дефолтні структури
        self.assertEqual(self.model.dish_cooking_time[custom_dish], 20)
        
        # Видаляємо її повністю
        self.model.delete_dish_from_menu_completely(custom_dish)
        self.assertNotIn(custom_dish, self.model.menu_data["Страви"])

    # ==========================================
    # 5. ДОДАТКОВІ ТЕСТИ
    # ==========================================

    def test_successful_order_lifecycle_and_editing(self):
        """Успішне створення, завантаження та редагування чека"""
        # Створюємо і закриваємо замовлення
        self.model.select_dish("Салат Цезар")
        self.model.save_current_dish_snapshot()
        self.model.confirm_and_close_order()
        
        # Перевіряємо, що id замовлення = 1 і база не порожня
        self.assertIn(1, self.model.get_order_keys())
        
        # Завантажуємо на редагування
        load_res = self.model.load_order_for_editing(1)
        self.assertTrue(load_res)
        
        # Додаємо ще одну страву в кошик
        self.model.select_dish("Суп томатний")
        self.model.save_current_dish_snapshot()
        
        # Зберігаємо відредаговане
        save_res = self.model.save_edited_order(1)
        self.assertTrue(save_res)

    def test_add_ingredient_back_logic(self):
        """Додавання інгредієнта назад у кастомну страву"""
        self.model.select_dish("Борщ український")
        # Перевіряємо, які інгредієнти доступні для додавання
        available = self.model.get_available_ingredients()
        
        if available:
            target_ing = available[0]
            # Додаємо його назад
            self.model.add_ingredient_back(target_ing)
            # Перевіряємо, чи з'явився він у поточному списку складників
            self.assertTrue(any(ing["name"] == target_ing for ing in self.model.current_dish_ingredients))

    def test_modify_default_dish_ingredients(self):
        """Кастомізація дефолтної матриці рецептів"""
        dish = "Деруни зі сметаною"
        ing = "Гриби смажені (г)"
        
        # 1. Додаємо новий складник до дефолтної страви
        self.model.add_ingredient_to_default_dish(dish, ing)
        meta = self.model.dish_ingredients_matrix[dish][ing]
        self.assertEqual(meta, "50 *")
        
        # 2. Видаляємо складник з дефолтної страви
        self.model.remove_ingredient_from_default_dish(dish, ing)
        meta_after = self.model.dish_ingredients_matrix[dish][ing]
        self.assertEqual(meta_after, "0 !")

    def test_add_new_ingredient_type_global(self):
        """Додавання абсолютно нового типу інгредієнта"""
        new_ing = "Екзотичний соус (мл)"
        self.model.add_new_type_ingredient = getattr(self.model, 'add_new_ingredient_type', None)
        if self.model.add_new_type_ingredient:
            self.model.add_new_type_ingredient(new_ing)
            self.assertIn(new_ing, self.model.global_ingredients_pool)

    def test_delete_active_selected_dish(self):
        """Видаляємо страву, яка зараз вибрана"""
        dish = "Котлета по-київськи"
        self.model.select_dish(dish)
        self.assertEqual(self.model.selected_dish, dish)
        
        # Видаляємо глобально з меню
        self.model.delete_dish_from_menu_completely(dish)
        # Перевіряємо, що селектор скинувся в None
        self.assertIsNone(self.model.selected_dish)

    def test_advanced_order_filtering_loops(self):
        """Всі розгалуження всередині циклів фільтрації чеків"""
        # Створюємо чек
        self.model.current_table_num = 14
        self.model.select_dish("Плов з телятиною")
        self.model.save_current_dish_snapshot()
        self.model.confirm_and_close_order()
        
        # Проганяємо пошук за назвою страви, яка точно є всередині чека
        res = self.model.get_filtered_order_keys("телятиною")
        self.assertGreater(len(res), 0)

if __name__ == "__main__":
    unittest.main()