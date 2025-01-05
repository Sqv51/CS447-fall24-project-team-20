import pygame

class Player:
    def __init__(self, name, position, image_path, chips):
        self.name = name
        self.position = position
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (60, 60))
        self.chips = chips
        self.rect = pygame.Rect(self.position[0], self.position[1], 60, 60)

    def draw(self, screen):
        screen.blit(self.image, self.position)
        font = pygame.font.Font(None, 24)
        name_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_text, (self.position[0], self.position[1] - 20))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)