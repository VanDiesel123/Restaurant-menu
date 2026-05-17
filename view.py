import pygame

pygame.init()

WIDTH, HEIGHT = 1366, 768
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
VIOLET = (100, 70, 130)

imgs = {
    "inactive_button": pygame.image.load("img/buttons/11.png"),
    "active_button": pygame.image.load("img/buttons/23.png"),
    "order_highlight": pygame.image.load("img/buttons/23.png") 
}

class TEXT():
    def __init__(self, text, size, font_type, x_y_center):
        self.x_y_center = x_y_center
        font = pygame.font.Font(font_type, size)
        self.surface = font.render(text, True, WHITE)
        self.rect = self.surface.get_rect(center=x_y_center)

    def text_set(self):
        ...

    def visible(self, screen):
        screen.blit(self.surface, self.rect)

class BUTTON():
    def __init__(self, size, x_y_center, text, font_type, funk):
        self.size, self.x_y_center, self.text = size, x_y_center, text
        self.funk = funk
        
        self.inac_img = pygame.transform.scale(imgs["inactive_button"], size).convert_alpha()
        self.ac_img = pygame.transform.scale(imgs["active_button"], [int(size[0]//1.1), int(size[1]//2)]).convert_alpha()
        
        self.is_hovered = False
        self.img_state = 0
        self.alpha = 0

        font = pygame.font.Font(font_type, size[1]//3)
        self.surface = font.render(text, True, WHITE)
        self.rect = self.surface.get_rect(center=x_y_center)

    def but_set(self):
        ...

    def collision(self, mouse_pos):
        if self.x_y_center[0] - self.size[0]//2 < mouse_pos[0] < self.x_y_center[0] + self.size[0]//2:
            if self.x_y_center[1] - self.size[1]//2 < mouse_pos[1] < self.x_y_center[1] + self.size[1]//2:
                self.is_hovered = True
            else: 
                self.is_hovered = False
        else: 
            self.is_hovered = False

        if self.is_hovered:
            self.alpha = min(255, self.alpha + 25)
        else:
            self.alpha = max(0, self.alpha - 12)

        self.img_state = 1 if self.is_hovered else 0

    def click(self, pre_click):
        if pre_click and self.is_hovered:
            self.funk()

    def visible(self, screen):
        if self.img_state is not None:
            screen.blit(self.inac_img, [self.x_y_center[0] - self.size[0]//2, self.x_y_center[1] - self.size[1]//2])
            if self.img_state or self.alpha != 0:
                self.ac_img.set_alpha(int(self.alpha))
                screen.blit(self.ac_img, [self.x_y_center[0] - int(self.size[0]//2.2), self.x_y_center[1] - int(self.size[1]//4)])

        screen.blit(self.surface, self.rect)

class ORDER_ITEM():
    def __init__(self, text, size, font_type, x_y_center):
        self.x_y_center = x_y_center
        self.size = size
        
        self.font = pygame.font.Font(font_type, size)
        self.surface = self.font.render(text, True, WHITE)
        self.rect = self.surface.get_rect(center=x_y_center)
        
        if x_y_center[0] < WIDTH // 2:
            highlight_size = [600, int(self.rect.height * 1.5)]
            self.highlight_img = pygame.transform.scale(imgs["order_highlight"], highlight_size).convert_alpha()
            self.highlight_rect = self.highlight_img.get_rect(center=[375, x_y_center[1]])
        else:
            highlight_size = [284, int(self.rect.height * 1.5)]
            self.highlight_img = pygame.transform.scale(imgs["order_highlight"], highlight_size).convert_alpha()
            self.highlight_rect = self.highlight_img.get_rect(center=[1158, x_y_center[1]])
        
        self.is_hovered = False
        self.alpha = 0

    def collision(self, mouse_pos):
        if self.highlight_rect.collidepoint(mouse_pos):
            self.is_hovered = True
        else:
            self.is_hovered = False
            
        if self.is_hovered:
            self.alpha = min(255, self.alpha + 25)
        else:
            self.alpha = max(0, self.alpha - 12)

    def visible(self, screen):
        if self.alpha != 0:
            temp_highlight = self.highlight_img.copy()
            temp_highlight.set_alpha(int(self.alpha))
            screen.blit(temp_highlight, self.highlight_rect)
            
        screen.blit(self.surface, self.rect)

TEXTES = {
    "MENU":{
        "menu": TEXT("ГОЛОВНЕ МЕНЮ", 45, "Pacifico-Regular.ttf", [WIDTH//2, HEIGHT//6]),
        "title": TEXT("Формування замовлень", 35, "Pacifico-Regular.ttf", [WIDTH//2, HEIGHT//6+80])
    },
    "SETTINGS":{
        "settings": TEXT("НАЛАШТУВАННЯ БАЗИ ДАНИХ", 45, "Pacifico-Regular.ttf", [WIDTH//2, HEIGHT//20]),
        "ing_title": TEXT("База Інгредієнтів", 30, "Pacifico-Regular.ttf", [375, 120]),
        "dish_title": TEXT("База Страв Меню", 30, "Pacifico-Regular.ttf", [1010, 120])
    },
    "MANAGEMENT":{
        "management": TEXT("УПРАВЛІННЯ ЗАМОВЛЕННЯМИ", 45, "Pacifico-Regular.ttf", [WIDTH//2, HEIGHT//6]),
        "my_orders": TEXT("Мої замовлення", 35, "Pacifico-Regular.ttf", [WIDTH//2, HEIGHT//2.5])
    },
    "CREATE": {
        "create": TEXT("СТВОРИТИ ЗАМОВЛЕННЯ", 45, "Pacifico-Regular.ttf", [WIDTH//2, HEIGHT//20]),
        "description": TEXT("Опис", 35, "Pacifico-Regular.ttf", [673, 110]),
        "ingredients": TEXT("Інгредієнти", 35, "Pacifico-Regular.ttf", [673, 380]),
        "add_panel_title": TEXT("Додати складник", 30, "Pacifico-Regular.ttf", [1191, 110])
    }
}