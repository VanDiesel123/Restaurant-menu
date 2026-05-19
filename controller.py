import pygame
import sys
import model
# import model_ref as model
import view
from view import TEXT, BUTTON, WIDTH, HEIGHT, BLACK, WHITE, VIOLET, TEXTES
import asyncio

class RestaurantController:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Формування замовлень у ресторані")
        
        self.model = model.RestaurantModel()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.model.connect_db())
        self.clock = pygame.time.Clock()
        self.FPS = 60
        
        self.running = True
        self.tab = "MENU"
        self.menu_scroll_idx = 0
        self.click_state = False
        
        self.desc_scroll_idx = 0
        self.ing_scroll_idx = 0
        self.right_ing_scroll_idx = 0
        
        # Індекси скролу
        self.order_scroll_idx = 0    
        self.receipt_scroll_idx = 0  
        self.basket_scroll_idx = 0   
        self.settings_ing_scroll = 0  
        self.settings_dish_scroll = 0 
        
        # Змінні для подвійного кліку та введення тексту
        self.last_click_time = 0
        self.last_clicked_dish = None
        self.editing_text_dish_name = None  
        self.text_input_buffer = ""         
        
        # ЛОГІКА РЕЖИМУ РЕДАГУВАННЯ ЗАМОВЛЕННЯ (Пункт 3.3 ТЗ)
        self.edit_mode = False
        self.editing_order_id = None
        
        # БУФЕРИ ДЛЯ ПОШУКУ (Розділ 4 ТЗ)
        self.ing_search_query = ""    
        self.order_search_query = ""  
        
        # Створення абсолютно нових сутностей
        self.creation_mode_type = None # "ING" або "DISH"
        self.creation_text_buffer = ""
        
        self.selected_settings_dish = None
        self.settings_add_ing_mode = False
        
        self.adding_ingredient_mode = False
        self.editing_dish_index = None
        
        self.my_orders_keys = []
        self.len_my_orders = 0
        self.order_text_cache = []
        self.selected_management_order_idx = None

        self.categories = list(self.model.menu_data.keys())
        self.current_cat_idx = 0
        self.model.selected_category = self.categories[self.current_cat_idx]
        self.menu_items_buttons = []
        
        self.center_ings_buttons = []
        self.right_ings_buttons = []
        self.my_order_items_cache = []
        self.my_order_remove_buttons = []
        
        self.settings_ing_buttons = []
        self.settings_dish_buttons = []

        self.init_ui_elements()
        self.update_menu_items_cache()

    def init_ui_elements(self):
        self.BUTTONS = {
            "MENU": {
                "management": BUTTON([500, 80], [WIDTH//2, HEIGHT//2], "Управління замовленнями", "Pacifico-Regular.ttf", lambda: self.change_tab("MANAGEMENT")),
                "settings": BUTTON([500, 80], [WIDTH//2, HEIGHT//2+HEIGHT//8], "Налаштування", "Pacifico-Regular.ttf", lambda: self.change_tab("SETTINGS")),
                "exit": BUTTON([500, 80], [WIDTH//2, HEIGHT//2+HEIGHT//4], "Вихід", "Pacifico-Regular.ttf", self.exit_app)
            },
            "SETTINGS": {
                "menu": BUTTON([300, 80], [WIDTH//10, HEIGHT//20], "Меню", "Pacifico-Regular.ttf", lambda: self.change_tab("MENU")),
                "add_ing_to_dish": BUTTON([240, 45], [180, 675], "+ Додати складник", "Pacifico-Regular.ttf", lambda: self.toggle_settings_ing_add_mode()),
                "create_new_ing": BUTTON([240, 45], [480, 675], "+ Створити інгредієнт", "Pacifico-Regular.ttf", lambda: self.start_creation_mode("ING")),
                "add_dish": BUTTON([260, 45], [1050, 675], "+ Створити страву", "Pacifico-Regular.ttf", lambda: self.start_creation_mode("DISH"))
            },
            "MANAGEMENT": {
                "menu": BUTTON([300, 80], [WIDTH//10, HEIGHT//20], "Меню", "Pacifico-Regular.ttf", lambda: self.change_tab("MENU")),
                "create": BUTTON([500, 80], [WIDTH//2, HEIGHT//3 - 40], "Створити замовлення", "Pacifico-Regular.ttf", lambda: self.change_tab("CREATE")),
                "delete_order": BUTTON([300, 50], [1160, 690], "Видалити замовлення", "Pacifico-Regular.ttf", self.delete_selected_order),
                "edit_order": BUTTON([300, 50], [890, 690], "Редагувати замовлення", "Pacifico-Regular.ttf", self.start_order_editing)
            },
            "CREATE": {
                "management": BUTTON([300, 80], [WIDTH//10, HEIGHT//20], "Управління", "Pacifico-Regular.ttf", lambda: self.change_tab("MANAGEMENT")),
                "cat_prev": BUTTON([70, 70], [50, 145], "<-", "Pacifico-Regular.ttf", lambda: self.switch_category(-1)),
                "cat_next": BUTTON([70, 70], [280, 145], "->", "Pacifico-Regular.ttf", lambda: self.switch_category(1)),
                "close_add_mode": BUTTON([45, 45], [1320, 110], "X", "Pacifico-Regular.ttf", lambda: self.set_add_mode(False)),
                "order_confirm": BUTTON([300, 60], [1191, 728], "Оформити", "Pacifico-Regular.ttf", self.submit_entire_order),
                "table_prev": BUTTON([40, 40], [1250, 38], "-", "Pacifico-Regular.ttf", lambda: self.model.change_table_number(-1)),
                "table_next": BUTTON([40, 40], [1330, 38], "+", "Pacifico-Regular.ttf", lambda: self.model.change_table_number(1))
            }
        }
        self.add_to_order_btn = BUTTON([60, 60], [860, 728], "+", "Pacifico-Regular.ttf", self.add_current_dish_to_order)

    def start_creation_mode(self, mode_type):
        self.creation_mode_type = mode_type
        self.creation_text_buffer = ""

    def toggle_settings_ing_add_mode(self):
        if self.selected_settings_dish:
            self.settings_add_ing_mode = not self.settings_add_ing_mode
            self.settings_ing_scroll = 0
            self.ing_search_query = "" 
            self.update_settings_admin_cache()

    def exit_app(self):
        self.running = False

    def start_order_editing(self):
        if self.selected_management_order_idx is not None and self.selected_management_order_idx < len(self.my_orders_keys):
            real_id = self.my_orders_keys[self.selected_management_order_idx]
            if self.model.load_order_for_editing(real_id):
                self.edit_mode = True
                self.editing_order_id = real_id
                
                self.tab = "CREATE"
                self.menu_scroll_idx = 0
                self.desc_scroll_idx = 0
                self.ing_scroll_idx = 0
                self.basket_scroll_idx = 0  
                self.adding_ingredient_mode = False
                self.editing_dish_index = None
                self.update_menu_items_cache()
                self.update_center_ingredients_cache()
                self.update_my_order_panel_cache()

    def add_current_dish_to_order(self):
        if self.model.selected_dish:
            self.model.save_current_dish_snapshot(self.editing_dish_index)
            self.set_add_mode(False)
            self.editing_dish_index = None
            self.update_my_order_panel_cache()

    def submit_entire_order(self):
        if self.edit_mode:
            # Функцію редагування ми ще не писали, тому поки залишимо заглушку
            # self.model.save_edited_order(self.editing_order_id)
            self.edit_mode = False
            self.editing_order_id = None
        elif self.model.basket_dishes:
            # МАГІЯ ТУТ: Змушуємо синхронний Pygame дочекатися асинхронної бази
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.model.confirm_and_close_order())
            
        self.editing_dish_index = None
        self.change_tab("MANAGEMENT")

    def delete_selected_order(self):
        if self.selected_management_order_idx is not None and self.selected_management_order_idx < len(self.my_orders_keys):
            real_id = self.my_orders_keys[self.selected_management_order_idx]
            self.model.delete_order_by_id(real_id)
            self.selected_management_order_idx = None
            self.change_tab("MANAGEMENT")

    def set_add_mode(self, state):
        self.adding_ingredient_mode = state
        self.right_ing_scroll_idx = 0
        self.update_right_ingredients_cache()

    def change_tab(self, new_tab):
        self.tab = new_tab
        if new_tab != "CREATE":
            self.edit_mode = False
            self.editing_order_id = None
            
        if new_tab == "MANAGEMENT":
            self.order_search_query = "" 
            self.my_orders_keys = self.model.get_filtered_order_keys(self.order_search_query)
            self.len_my_orders = len(self.my_orders_keys)
            self.order_scroll_idx = 0
            self.receipt_scroll_idx = 0
            self.selected_management_order_idx = None
            self.update_order_cache()
        if new_tab == "SETTINGS":
            self.settings_ing_scroll = 0
            self.settings_dish_scroll = 0
            self.editing_text_dish_name = None
            self.creation_mode_type = None
            self.selected_settings_dish = None
            self.settings_add_ing_mode = False
            self.ing_search_query = ""
            self.update_settings_admin_cache()
        if new_tab == "CREATE":
            self.menu_scroll_idx = 0
            self.desc_scroll_idx = 0
            self.ing_scroll_idx = 0
            self.basket_scroll_idx = 0  
            self.adding_ingredient_mode = False
            self.editing_dish_index = None
            self.update_menu_items_cache()
            self.update_center_ingredients_cache()
            self.update_my_order_panel_cache()

    def handle_settings_dish_click(self, d_name):
        current_time = pygame.time.get_ticks()
        self.selected_settings_dish = d_name
        self.settings_add_ing_mode = False
        self.settings_ing_scroll = 0
        self.ing_search_query = ""
        
        if self.last_clicked_dish == d_name and (current_time - self.last_click_time) < 300:
            self.editing_text_dish_name = d_name
            self.text_input_buffer = d_name
        else:
            self.last_clicked_dish = d_name
        self.last_click_time = current_time
        self.update_settings_admin_cache()

    def switch_category(self, direction):
        self.current_cat_idx = (self.current_cat_idx + direction) % len(self.categories)
        self.model.selected_category = self.categories[self.current_cat_idx]
        self.menu_scroll_idx = 0
        self.update_menu_items_cache()

    def update_menu_items_cache(self):
        self.menu_items_buttons = []
        current_menu = self.model.menu_data[self.model.selected_category]
        menu_keys = list(current_menu.keys())
        
        self.cat_title_btn = BUTTON([200, 70], [165, 145], self.model.selected_category, "Pacifico-Regular.ttf", lambda: None)
        
        for i in range(0, 6):
            idx = i + self.menu_scroll_idx
            if idx < len(menu_keys):
                item_name = menu_keys[idx]
                btn = BUTTON([300, 65], [165, 240 + i * 80], item_name, "Pacifico-Regular.ttf", lambda name=item_name: self.select_dish(name))
                self.menu_items_buttons.append(btn)

    def select_dish(self, dish_name):
     loop = asyncio.get_event_loop()
     loop.run_until_complete(self.model.select_dish(dish_name))

     self.desc_scroll_idx = 0
     self.ing_scroll_idx = 0
     self.adding_ingredient_mode = False
     self.editing_dish_index = None
     self.update_center_ingredients_cache()

    def select_dish_for_editing(self, index):
        snapshot = self.model.basket_dishes[index]
        self.model.load_dish_from_snapshot(snapshot)
        self.editing_dish_index = index
        self.desc_scroll_idx = 0
        self.ing_scroll_idx = 0
        self.adding_ingredient_mode = False
        self.update_center_ingredients_cache()

    def remove_dish_from_basket(self, index):
        self.model.remove_dish_from_order(index)
        if self.editing_dish_index == index:
            self.editing_dish_index = None
            self.model.selected_dish = None
            self.center_ings_buttons = []
        elif self.editing_dish_index is not None and self.editing_dish_index > index:
            self.editing_dish_index -= 1
            
        if self.basket_scroll_idx > 0 and (self.basket_scroll_idx + 6) > len(self.model.basket_dishes):
            self.basket_scroll_idx = max(0, len(self.model.basket_dishes) - 6)
            
        self.update_my_order_panel_cache()

    def update_settings_admin_cache(self):
        self.settings_ing_buttons = []
        self.settings_dish_buttons = []
        
        if self.selected_settings_dish and self.selected_settings_dish in self.model.dish_ingredients_matrix:
            if self.settings_add_ing_mode:
                current_ings = self.model.dish_ingredients_matrix[self.selected_settings_dish]
                available_to_add = [ing for ing in self.model.global_ingredients_pool if ing not in current_ings or current_ings[ing].split()[1] == '!']
                
                if self.ing_search_query.strip():
                    available_to_add = [ing for ing in available_to_add if self.ing_search_query.lower() in ing.lower()]
                
                for i in range(0, 9):
                    idx = i + self.settings_ing_scroll
                    if idx < len(available_to_add):
                        ing_name = available_to_add[idx]
                        y_pos = 165 + i * 50
                        # ОНОВЛЕНО: Тепер примусово оновлюється весь кеш для негайного виведення нової ціни
                        btn_add = BUTTON([40, 30], [590, y_pos + 15], "+", "Pacifico-Regular.ttf", lambda name=ing_name: [self.model.add_ingredient_to_default_dish(self.selected_settings_dish, name), self.update_settings_admin_cache(), self.toggle_settings_ing_add_mode()])
                        self.settings_ing_buttons.append(btn_add)
            else:
                dish_ings_dict = self.model.dish_ingredients_matrix[self.selected_settings_dish]
                active_ings = []
                for name, meta in dish_ings_dict.items():
                    val_str, symbol = meta.split()
                    if symbol != '!': active_ings.append((name, val_str, symbol))
                
                for i in range(0, 9):
                    idx = i + self.settings_ing_scroll
                    if idx < len(active_ings):
                        ing_name, count, symbol = active_ings[idx]
                        y_pos = 165 + i * 50
                        
                        btn_p = BUTTON([30, 30], [500, y_pos + 15], "+", "Pacifico-Regular.ttf", lambda ing=ing_name: [self.model.change_default_ingredient_amount(self.selected_settings_dish, ing, 10), self.update_settings_admin_cache()])
                        btn_m = BUTTON([30, 30], [540, y_pos + 15], "-", "Pacifico-Regular.ttf", lambda ing=ing_name: [self.model.change_default_ingredient_amount(self.selected_settings_dish, ing, -10), self.update_settings_admin_cache()])
                        self.settings_ing_buttons.extend([btn_p, btn_m])
                        
                        if symbol in ['*', '!']:
                            btn_x = BUTTON([30, 30], [590, y_pos + 15], "X", "Pacifico-Regular.ttf", lambda ing=ing_name: [self.model.remove_ingredient_from_default_dish(self.selected_settings_dish, ing), self.update_settings_admin_cache()])
                            self.settings_ing_buttons.append(btn_x)

        all_dishes_list = list(self.model.menu_data["Страви"].keys())
        for i in range(0, 5):
            idx = i + self.settings_dish_scroll
            if idx < len(all_dishes_list):
                d_name = all_dishes_list[idx]
                y_pos = 165 + i * 90
                btn_dp = BUTTON([35, 35], [1160, y_pos + 12], "+", "Pacifico-Regular.ttf", lambda dish=d_name: [self.model.change_global_dish_base_price("Страви", dish, 5), self.update_settings_admin_cache()])
                btn_dm = BUTTON([35, 35], [1210, y_pos + 12], "-", "Pacifico-Regular.ttf", lambda dish=d_name: [self.model.change_global_dish_base_price("Страви", dish, -5), self.update_settings_admin_cache()])
                btn_tp = BUTTON([35, 35], [1160, y_pos + 52], "+", "Pacifico-Regular.ttf", lambda dish=d_name: [self.model.change_global_cooking_time(dish, 1), self.update_settings_admin_cache()])
                btn_tm = BUTTON([35, 35], [1210, y_pos + 52], "-", "Pacifico-Regular.ttf", lambda dish=d_name: [self.model.change_global_cooking_time(dish, -1), self.update_settings_admin_cache()])
                btn_del_dish = BUTTON([35, 35], [1260, y_pos + 32], "X", "Pacifico-Regular.ttf", lambda dish=d_name: [self.model.delete_dish_from_menu_completely(dish), self.update_settings_admin_cache()])
                self.settings_dish_buttons.extend([btn_dp, btn_dm, btn_tp, btn_tm, btn_del_dish])

    def update_center_ingredients_cache(self):
        self.center_ings_buttons = []
        if not self.model.selected_dish:
            return
            
        ings = self.model.current_dish_ingredients
        for i in range(0, 3):
            idx = i + self.ing_scroll_idx
            y_pos = 440 + i * 70
            
            if idx < len(ings):
                ing = ings[idx]
                if ing['symbol'] in ['&', '*', '!']:
                    btn_plus = BUTTON([40, 40], [800, y_pos + 15], "+", "Pacifico-Regular.ttf", lambda index=idx: [self.model.change_ingredient_count(index, 1), self.update_center_ingredients_cache(), self.update_right_ingredients_cache()])
                    btn_minus = BUTTON([40, 40], [860, y_pos + 15], "-", "Pacifico-Regular.ttf", lambda index=idx: [self.model.change_ingredient_count(index, -1), self.update_center_ingredients_cache(), self.update_right_ingredients_cache()])
                    self.center_ings_buttons.extend([btn_plus, btn_minus])
                    
                if ing['symbol'] in ['*', '!']:
                    btn_remove = BUTTON([40, 40], [940, y_pos + 15], "X", "Pacifico-Regular.ttf", lambda index=idx: [self.model.change_ingredient_count(index, -self.model.current_dish_ingredients[index]['count']), self.update_center_ingredients_cache(), self.update_right_ingredients_cache()])
                    self.center_ings_buttons.append(btn_remove)
                    
            elif idx == len(ings):
                btn_add_trigger = BUTTON([40, 40], [390, y_pos + 15], "+", "Pacifico-Regular.ttf", lambda: self.set_add_mode(True))
                self.center_ings_buttons.append(btn_add_trigger)

    def update_right_ingredients_cache(self):
        self.right_ings_buttons = []
        if not self.adding_ingredient_mode:
            return
            
        available_ings = self.model.get_available_ingredients()
        for i in range(0, 7):
            idx = i + self.right_ing_scroll_idx
            if idx < len(available_ings):
                ing_name = available_ings[idx]
                y_pos_right = 160 + i * 65
                
                btn_add_ing = BUTTON([35, 35], [1320, y_pos_right + 12], "+", "Pacifico-Regular.ttf", lambda name=ing_name: [self.model.add_ingredient_back(name), self.update_center_ingredients_cache(), self.update_right_ingredients_cache()])
                self.right_ings_buttons.append(btn_add_ing)

    def update_my_order_panel_cache(self):
        self.my_order_items_cache = []
        self.my_order_remove_buttons = []
        current_order_content = self.model.basket_dishes
        
        for i in range(0, 7):
            idx = i + self.basket_scroll_idx
            if idx < len(current_order_content):
                snapshot = current_order_content[idx]
                y_pos_right = 160 + i * 65
                
                dish_name = snapshot["DISH_NAME"]
                fact_price = snapshot["FACT_PRICE"]
                text_line = f"{dish_name}: {fact_price:.2f}"
                
                item_obj = view.ORDER_ITEM(text_line, 18, "Pacifico-Regular.ttf", [1158, y_pos_right + 15])
                item_obj.basket_real_index = idx
                self.my_order_items_cache.append(item_obj)
                
                btn_del = BUTTON([35, 35], [1335, y_pos_right + 15], "X", "Pacifico-Regular.ttf", lambda index=idx: self.remove_dish_from_basket(index))
                self.my_order_remove_buttons.append(btn_del)

    def update_order_cache(self):
        self.order_text_cache = []
        # ОНОВЛЕНО: Тепер локальний індекс тексту чітко збігається з індексом у списку ключів!
        for i in range(0, 4):
            idx = i + self.order_scroll_idx
            if idx < self.len_my_orders:
                order_item_obj = view.ORDER_ITEM(f"Замовлення № {self.my_orders_keys[idx]}", 22, "Pacifico-Regular.ttf", [375, int(HEIGHT*0.42 + 80*(i+1))])
                order_item_obj.order_index = idx  
                self.order_text_cache.append(order_item_obj)

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if self.editing_text_dish_name is not None:
                        if event.key == pygame.K_RETURN:
                            self.model.rename_dish_in_database(self.editing_text_dish_name, self.text_input_buffer)
                            self.editing_text_dish_name = None
                            self.update_settings_admin_cache()
                        elif event.key == pygame.K_ESCAPE:
                            self.editing_text_dish_name = None
                        elif event.key == pygame.K_BACKSPACE:
                            self.text_input_buffer = self.text_input_buffer[:-1]
                        else:
                            self.text_input_buffer += event.unicode
                            
                    elif self.creation_mode_type is not None:
                        if event.key == pygame.K_RETURN:
                            if self.creation_mode_type == "ING":
                                self.model.add_new_ingredient_type(self.creation_text_buffer)
                            elif self.creation_mode_type == "DISH":
                                self.model.add_new_dish_to_menu(self.creation_text_buffer)
                            self.creation_mode_type = None
                            self.update_settings_admin_cache()
                        elif event.key == pygame.K_ESCAPE:
                            self.creation_mode_type = None
                        elif event.key == pygame.K_BACKSPACE:
                            self.creation_text_buffer = self.creation_text_buffer[:-1]
                        else:
                            self.creation_text_buffer += event.unicode
                    
                    else:
                        if self.tab == "SETTINGS" and self.settings_add_ing_mode:
                            if event.key == pygame.K_ESCAPE:
                                self.ing_search_query = ""
                            elif event.key == pygame.K_BACKSPACE:
                                self.ing_search_query = self.ing_search_query[:-1]
                            elif event.key != pygame.K_RETURN:
                                self.ing_search_query += event.unicode
                            self.settings_ing_scroll = 0
                            self.update_settings_admin_cache()
                            
                        elif self.tab == "MANAGEMENT":
                            if event.key == pygame.K_ESCAPE:
                                self.order_search_query = ""
                            elif event.key == pygame.K_BACKSPACE:
                                self.order_search_query = self.order_search_query[:-1]
                            elif event.key != pygame.K_RETURN:
                                self.order_search_query += event.unicode
                            
                            self.order_scroll_idx = 0
                            self.selected_management_order_idx = None 
                            self.my_orders_keys = self.model.get_filtered_order_keys(self.order_search_query)
                            self.len_my_orders = len(self.my_orders_keys)
                            self.update_order_cache()

                if event.type == pygame.MOUSEWHEEL:
                    if self.tab == "MANAGEMENT":
                        if 50 <= mouse_pos[0] <= 700 and 368 <= mouse_pos[1] <= 728:
                            if event.y > 0: self.order_scroll_idx = max(0, self.order_scroll_idx - 1)
                            elif event.y < 0:
                                if (self.order_scroll_idx + 4) < self.len_my_orders: self.order_scroll_idx += 1
                            self.update_order_cache()
                        
                        elif 740 <= mouse_pos[0] <= 1310 and 368 <= mouse_pos[1] <= 728:
                            if self.selected_management_order_idx is not None and self.selected_management_order_idx < len(self.my_orders_keys):
                                real_id = self.my_orders_keys[self.selected_management_order_idx]
                                order_content = self.model.my_orders_database[real_id]["dishes"]
                                if event.y > 0: self.receipt_scroll_idx = max(0, self.receipt_scroll_idx - 1)
                                elif event.y < 0:
                                    if (self.receipt_scroll_idx + 6) < len(order_content): self.receipt_scroll_idx += 1
                                    
                    elif self.tab == "SETTINGS":
                        if mouse_pos[0] < 680:
                            if self.selected_settings_dish and self.selected_settings_dish in self.model.dish_ingredients_matrix:
                                if self.settings_add_ing_mode:
                                    current_ings = self.model.dish_ingredients_matrix[self.selected_settings_dish]
                                    available_to_add = [ing for ing in self.model.global_ingredients_pool if ing not in current_ings or current_ings[ing].split()[1] == '!']
                                    if self.ing_search_query.strip():
                                        available_to_add = [ing for ing in available_to_add if self.ing_search_query.lower() in ing.lower()]
                                    total_items = len(available_to_add)
                                else:
                                    total_items = len([k for k, v in self.model.dish_ingredients_matrix[self.selected_settings_dish].items() if v.split()[1] != '!'])
                                
                                if event.y > 0: self.settings_ing_scroll = max(0, self.settings_ing_scroll - 1)
                                elif event.y < 0:
                                    if (self.settings_ing_scroll + 9) < total_items: self.settings_ing_scroll += 1
                                self.update_settings_admin_cache()
                        else:
                            all_dishes_count = len(self.model.menu_data["Страви"])
                            if event.y > 0: self.settings_dish_scroll = max(0, self.settings_dish_scroll - 1)
                            elif event.y < 0:
                                if (self.settings_dish_scroll + 5) < all_dishes_count: self.settings_dish_scroll += 1
                            self.update_settings_admin_cache()
                            
                    elif self.tab == "CREATE":
                        if mouse_pos[0] < 330 and 195 < mouse_pos[1] < 688:
                            old_scroll = self.menu_scroll_idx
                            total_items = len(self.model.menu_data[self.model.selected_category])
                            if event.y > 0: self.menu_scroll_idx = self.menu_scroll_idx - 1 if self.menu_scroll_idx else self.menu_scroll_idx
                            elif event.y < 0: self.menu_scroll_idx = self.menu_scroll_idx + 1 if (self.menu_scroll_idx + 7) < total_items else self.menu_scroll_idx
                            if old_scroll != self.menu_scroll_idx: self.update_menu_items_cache()
                                
                        elif 330 <= mouse_pos[0] < 1016 and 80 <= mouse_pos[1] < 350:
                            if self.model.selected_dish:
                                desc_lines = self.model.descriptions.get(self.model.selected_dish, [])
                                if event.y > 0: self.desc_scroll_idx = max(0, self.desc_scroll_idx - 1)
                                elif event.y < 0:
                                    if (self.desc_scroll_idx + 3) < len(desc_lines): self.desc_scroll_idx += 1
                                        
                        elif 330 <= mouse_pos[0] < 1016 and 350 <= mouse_pos[1] < 688:
                            if self.model.selected_dish:
                                old_ing_scroll = self.ing_scroll_idx
                                total_ings = len(self.model.current_dish_ingredients) + 1
                                if event.y > 0: self.ing_scroll_idx = max(0, self.ing_scroll_idx - 1)
                                elif event.y < 0:
                                    if (self.ing_scroll_idx + 3) < total_ings: self.ing_scroll_idx += 1
                                if old_ing_scroll != self.ing_scroll_idx: self.update_center_ingredients_cache()
                                    
                        elif mouse_pos[0] >= 1016 and 140 <= mouse_pos[1] < 600:
                            if not self.adding_ingredient_mode:
                                total_basket_dishes = len(self.model.basket_dishes)
                                if event.y > 0: self.basket_scroll_idx = max(0, self.basket_scroll_idx - 1)
                                elif event.y < 0:
                                    if (self.basket_scroll_idx + 7) < total_basket_dishes: self.basket_scroll_idx += 1
                                self.update_my_order_panel_cache()

            self.screen.fill(BLACK)
            pre_click = True if mouse_pressed[0] and not self.click_state else False
            self.click_state = True if mouse_pressed[0] else False

            if self.tab in TEXTES:
                for text_key, text_obj in TEXTES[self.tab].items():
                    if text_key == "add_panel_title" and not self.adding_ingredient_mode: continue
                    if text_key == "create" and self.edit_mode: continue
                    text_obj.visible(self.screen)

            if self.tab in self.BUTTONS:
                for btn_key, btn_obj in self.BUTTONS[self.tab].items():
                    if btn_key == "close_add_mode" and not self.adding_ingredient_mode: continue
                    if btn_key == "delete_order" and self.selected_management_order_idx is None: continue
                    if btn_key == "edit_order" and self.selected_management_order_idx is None: continue
                    if btn_key == "add_ing_to_dish" and self.selected_settings_dish is None: continue
                    btn_obj.visible(self.screen)
                    btn_obj.collision(mouse_pos)
                    btn_obj.click(pre_click)

            if self.tab == "SETTINGS":
                pygame.draw.rect(self.screen, VIOLET, (50, 150, 600, 500), 2)
                pygame.draw.rect(self.screen, VIOLET, (710, 150, 600, 500), 2)
                
                font_item = pygame.font.Font("Pacifico-Regular.ttf", 18)
                
                if self.creation_mode_type == "ING":
                    surf_c = font_item.render(f"Новий інгредієнт: {self.creation_text_buffer} |", True, WHITE)
                    self.screen.blit(surf_c, (70, 610))
                elif self.creation_mode_type == "DISH":
                    surf_c = font_item.render(f"Назва страви: {self.creation_text_buffer} |", True, WHITE)
                    self.screen.blit(surf_c, (730, 610))
                elif self.settings_add_ing_mode:
                    surf_s = font_item.render(f"Пошук: {self.ing_search_query} |", True, (255, 215, 0))
                    self.screen.blit(surf_s, (70, 610))

                if not self.selected_settings_dish:
                    surf_empty = font_item.render("Оберіть страву праворуч для зміни складу", True, WHITE)
                    self.screen.blit(surf_empty, (110, 380))
                else:
                    if self.settings_add_ing_mode:
                        current_ings = self.model.dish_ingredients_matrix[self.selected_settings_dish]
                        available_to_add = [ing for ing in self.model.global_ingredients_pool if ing not in current_ings or current_ings[ing].split()[1] == '!']
                        if self.ing_search_query.strip():
                            available_to_add = [ing for ing in available_to_add if self.ing_search_query.lower() in ing.lower()]
                        
                        for i in range(0, 9):
                            idx = i + self.settings_ing_scroll
                            if idx < len(available_to_add):
                                ing_name = available_to_add[idx]
                                y_pos = 160 + i * 50
                                surf = font_item.render(f"Додати: {ing_name}", True, WHITE)
                                self.screen.blit(surf, (70, y_pos))
                                pygame.draw.line(self.screen, VIOLET, [75, y_pos + 45], [625, y_pos + 45], 1)
                    else:
                        dish_ings_dict = self.model.dish_ingredients_matrix[self.selected_settings_dish]
                        active_ings = []
                        for name, meta in dish_ings_dict.items():
                            val_str, symbol = meta.split()
                            if symbol != '!': active_ings.append((name, val_str, symbol))
                            
                        for i in range(0, 9):
                            idx = i + self.settings_ing_scroll
                            if idx < len(active_ings):
                                ing_name, val_str, symbol = active_ings[idx]
                                y_pos = 160 + i * 50
                                clean_name = ing_name.split()[0]
                                txt = f"{clean_name}: {val_str}"
                                
                                surf = font_item.render(txt, True, WHITE)
                                self.screen.blit(surf, (70, y_pos))
                                pygame.draw.line(self.screen, VIOLET, [75, y_pos + 45], [625, y_pos + 45], 1)
                                
                for b in self.settings_ing_buttons:
                    b.collision(mouse_pos)
                    b.visible(self.screen)
                    b.click(pre_click)

                all_dishes_list = list(self.model.menu_data["Страви"].keys())
                for i in range(0, 5):
                    idx = i + self.settings_dish_scroll
                    if idx < len(all_dishes_list):
                        d_name = all_dishes_list[idx]
                        base_p = self.model.menu_data["Страви"][d_name]
                        c_time = self.model.dish_cooking_time.get(d_name, 20)
                        y_pos = 160 + i * 90
                        
                        if self.selected_settings_dish == d_name:
                            pygame.draw.rect(self.screen, VIOLET, (720, y_pos - 5, 430, 85), 1)
                        
                        if self.editing_text_dish_name == d_name:
                            txt_price = f"{idx+1}. {self.text_input_buffer} |"
                        else:
                            txt_price = f"{idx+1}. {d_name} — Базова: {base_p} грн."
                            
                        txt_time = f"   Час приготування: {c_time} хв."
                        
                        surf_p = font_item.render(txt_price, True, WHITE)
                        surf_t = font_item.render(txt_time, True, WHITE)
                        
                        dish_rect = pygame.Rect(730, y_pos, 420, 80)
                        if pre_click and dish_rect.collidepoint(mouse_pos):
                            self.handle_settings_dish_click(d_name)
                            
                        self.screen.blit(surf_p, (730, y_pos))
                        self.screen.blit(surf_t, (730, y_pos + 40))
                        pygame.draw.line(self.screen, VIOLET, [735, y_pos + 85], [1285, y_pos + 85], 1)
                        
                for b in self.settings_dish_buttons:
                    b.collision(mouse_pos)
                    b.visible(self.screen)
                    b.click(pre_click)

            if self.tab == "MANAGEMENT":
                pygame.draw.rect(self.screen, VIOLET, (50, 368, 650, 360), 2)
                
                if self.order_search_query.strip():
                    surf_sq = font_item.render(f"Фільтр чеків: {self.order_search_query} |", True, (255, 215, 0))
                    self.screen.blit(surf_sq, (65, 335))

                for i, order_obj in enumerate(self.order_text_cache):
                    order_obj.collision(mouse_pos) 

                    if order_obj.order_index == self.selected_management_order_idx:
                        pygame.draw.rect(self.screen, (50, 50, 50), order_obj.highlight_rect)
                        
                    order_obj.visible(self.screen)
                    
                    if pre_click and order_obj.highlight_rect.collidepoint(mouse_pos):
                        self.selected_management_order_idx = order_obj.order_index
                        self.receipt_scroll_idx = 0
                        
                    y = int(HEIGHT*0.42 + 80*(i+1.5))
                    pygame.draw.line(self.screen, VIOLET, [75, y], [675, y], 1)

                pygame.draw.rect(self.screen, VIOLET, (740, 368, 570, 360), 2)
                font_title_m = pygame.font.Font("Pacifico-Regular.ttf", 26)
                font_body_m = pygame.font.Font("Pacifico-Regular.ttf", 18)

                if self.selected_management_order_idx is not None and self.selected_management_order_idx < len(self.my_orders_keys):
                    real_id = self.my_orders_keys[self.selected_management_order_idx]
                    order_pack = self.model.my_orders_database[real_id]
                    table_num = order_pack["table"]
                    order_content = order_pack["dishes"]
                    
                    t_surf = font_title_m.render(f"Чек № {real_id} (Стіл № {table_num})", True, WHITE)
                    self.screen.blit(t_surf, (760, 385))
                    pygame.draw.line(self.screen, VIOLET, [765, 435], [1285, 435], 1)
                    pygame.draw.line(self.screen, VIOLET, [765, 630], [1285, 630], 1)
                    
                    total_sum = 0
                    y_offset = 440
                    for idx, snapshot in enumerate(order_content):
                        total_sum += snapshot["FACT_PRICE"]
                        display_idx = idx - self.receipt_scroll_idx
                        if 0 <= display_idx < 6:
                            d_name = snapshot["DISH_NAME"]
                            f_price = snapshot["FACT_PRICE"]
                            dish_line = f"{idx+1}. {d_name} — {f_price:.2f} грн."
                            d_surf = font_body_m.render(dish_line, True, WHITE)
                            self.screen.blit(d_surf, (760, y_offset + display_idx * 30))
                    
                    sum_line = f"Загальна сума: {total_sum:.2f} грн."
                    sum_surf = font_title_m.render(sum_line, True, WHITE)
                    self.screen.blit(sum_surf, (760, 625))
                else:
                    t_surf = font_title_m.render("Оберіть замовлення для перегляду", True, WHITE)
                    self.screen.blit(t_surf, (800, 520))

            if self.tab == "CREATE":
                pygame.draw.line(self.screen, VIOLET, [0, 80], [1366, 80], 2)
                pygame.draw.line(self.screen, VIOLET, [0, 688], [1366, 688], 2)
                pygame.draw.line(self.screen, VIOLET, [330, 80], [330, 768], 2)
                pygame.draw.line(self.screen, VIOLET, [1016, 80], [1016, 768], 2)
                pygame.draw.line(self.screen, VIOLET, [25, 195], [305, 195], 1)
                pygame.draw.line(self.screen, VIOLET, [355, 140], [996, 140], 1)
                pygame.draw.line(self.screen, VIOLET, [330, 350], [1016, 350], 2)
                pygame.draw.line(self.screen, VIOLET, [355, 410], [996, 410], 1)
                pygame.draw.line(self.screen, VIOLET, [1016, 600], [1366, 600], 2)
                pygame.draw.line(self.screen, VIOLET, [1041, 140], [1341, 140], 1)

                if self.edit_mode:
                    font_title = pygame.font.Font("Pacifico-Regular.ttf", 45)
                    edit_surf = font_title.render(f"Редагування замовлення №{self.editing_order_id}", True, WHITE)
                    self.screen.blit(edit_surf, (WIDTH // 2 - edit_surf.get_width() // 2, HEIGHT // 20 - edit_surf.get_height() // 2))
                    self.BUTTONS["CREATE"]["order_confirm"].text = "Зберегти"
                else:
                    TEXTES["CREATE"]["create"].visible(self.screen)
                    self.BUTTONS["CREATE"]["order_confirm"].text = "Оформити"
                
                font_btn = pygame.font.Font("Pacifico-Regular.ttf", self.BUTTONS["CREATE"]["order_confirm"].size[1]//3)
                self.BUTTONS["CREATE"]["order_confirm"].surface = font_btn.render(self.BUTTONS["CREATE"]["order_confirm"].text, True, WHITE)
                self.BUTTONS["CREATE"]["order_confirm"].rect = self.BUTTONS["CREATE"]["order_confirm"].surface.get_rect(center=self.BUTTONS["CREATE"]["order_confirm"].x_y_center)

                font_table = pygame.font.Font("Pacifico-Regular.ttf", 24)
                table_surf = font_table.render(f"Столик №           {self.model.current_table_num}", True, WHITE)
                self.screen.blit(table_surf, (1100, 15))

                self.cat_title_btn.visible(self.screen)
                for btn in self.menu_items_buttons:
                    btn.visible(self.screen)
                    btn.collision(mouse_pos)
                    btn.click(pre_click)

                if self.adding_ingredient_mode:
                    available_ings = self.model.get_available_ingredients()
                    font_right = pygame.font.Font("Pacifico-Regular.ttf", 18)
                    for i in range(0, 7):
                        idx = i + self.right_ing_scroll_idx
                        if idx < len(available_ings):
                            ing_name = available_ings[idx]
                            y_pos_right = 160 + i * 65
                            surf_right = font_right.render(ing_name, True, WHITE)
                            self.screen.blit(surf_right, (1040, y_pos_right))
                    for b in self.right_ings_buttons:
                        b.collision(mouse_pos)
                        b.click(pre_click)
                        b.visible(self.screen)
                else:
                    font_title = pygame.font.Font("Pacifico-Regular.ttf", 30)
                    title_surf = font_title.render("Моє замовлення", True, WHITE)
                    self.screen.blit(title_surf, (1090, 85))
                    for item_obj in self.my_order_items_cache:
                        item_obj.collision(mouse_pos)
                        item_obj.visible(self.screen)
                        if pre_click and item_obj.highlight_rect.collidepoint(mouse_pos):
                            self.select_dish_for_editing(item_obj.basket_real_index)
                    for btn_del in self.my_order_remove_buttons:
                        btn_del.collision(mouse_pos)
                        btn_del.visible(self.screen)
                        btn_del.click(pre_click)

                if self.model.selected_dish:
                    desc_lines = self.model.descriptions.get(self.model.selected_dish, ["Опис відсутній для цієї страви."])
                    font_desc = pygame.font.Font("Pacifico-Regular.ttf", 20)
                    for i in range(0, 3):
                        idx = i + self.desc_scroll_idx
                        if idx < len(desc_lines):
                            surf = font_desc.render(desc_lines[idx], True, WHITE)
                            self.screen.blit(surf, (370, 160 + i * 50))

                    ings = self.model.current_dish_ingredients
                    font_ing = pygame.font.Font("Pacifico-Regular.ttf", 22)
                    for i in range(0, 3):
                        idx = i + self.ing_scroll_idx
                        y_pos = 440 + i * 70
                        if idx < len(ings):
                            ing = ings[idx]
                            surf = font_ing.render(f"{ing['name']}: {ing['count']}", True, WHITE)
                            self.screen.blit(surf, (370, y_pos))
                    for b in self.center_ings_buttons:
                        b.collision(mouse_pos)
                        b.click(pre_click)
                        b.visible(self.screen)

                current_price = self.model.get_current_dish_price()
                font_price = pygame.font.Font("Pacifico-Regular.ttf", 32)
                price_text = f"Ціна: {current_price:.2f} грн."
                price_surf = font_price.render(price_text, True, WHITE)
                price_rect = price_surf.get_rect(center=[610, 728])
                self.screen.blit(price_surf, price_rect)

                self.add_to_order_btn.visible(self.screen)
                self.add_to_order_btn.collision(mouse_pos)
                self.add_to_order_btn.click(pre_click)

                total_order_price = self.model.get_total_order_price()
                font_total = pygame.font.Font("Pacifico-Regular.ttf", 26)
                total_text = f"Сума: {total_order_price:.2f} грн."
                total_surf = font_total.render(total_text, True, WHITE)
                total_rect = total_surf.get_rect(center=[1191, 642])
                self.screen.blit(total_surf, total_rect)

            pygame.display.flip()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = RestaurantController()
    app.run()