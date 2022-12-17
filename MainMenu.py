import pygame

class MainMenu:
    def __init__(self, screen):
        self.font = pygame.font.SysFont('Arial', 80)
        self.title = self.font.render("Maze Solver AI", True, (255, 255, 255))
        self.title_position = (10, 10)
        self.gameplay_scene = None

        self.text_color = (255,255,255)
        self.button_color = pygame.Color(0,0,170)
        self.button_over_color = pygame.Color(255,50,50)

        self.button_width = 100
        self.button_height = 50
        self.button_rect = pygame.Rect(screen.get_width()/2 - self.button_width/2, screen.get_height()/2-self.button_height/2, self.button_width, self.button_height)
        self.button_font = pygame.font.SysFont('Arial', 20)
        self.button_text = self.button_font.render('Play', True, self.text_color)

        self.x_pos = 0
        self.y_pos = 0

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return self.gameplay_scene
            if event.type == pygame.MOUSEMOTION:
                self.x_pos, self.y_pos = event.pos
            if event.type == pygame.MOUSEBUTTONDOWN:
                x,y = event.pos
                # self.x_pos = x
                # self.y_pos = y
                if (x >= self.button_rect.x and x <= self.button_rect.x + self.button_rect.width 
                    and y >= self.button_rect.y and y <= self.button_rect.y + self.button_rect.height):
                    return self.gameplay_scene
        return self

    def draw(self, screen):
        screen.blit(self.title, self.title_position)
        x,y = self.x_pos, self.y_pos
        if (x >= self.button_rect.x and x <= self.button_rect.x + self.button_rect.width 
                and y >= self.button_rect.y and y <= self.button_rect.y + self.button_rect.height):
            pygame.draw.rect(screen, self.button_over_color, self.button_rect)
        else:
            pygame.draw.rect(screen, self.button_color, self.button_rect)
        screen.blit(self.button_text,(self.button_rect[0] + (self.button_width/2 -  self.button_text.get_width()/2), 
                        self.button_rect[1] + (self.button_height/2 - self.button_text.get_height()/2)))