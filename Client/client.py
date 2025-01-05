import pygame
import pickle
from network import Network

pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Poker Game")

# Load Table Image
table_image = pygame.image.load("images/poker_table.png").convert_alpha()
table_image = pygame.transform.scale(table_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Network Setup
network = Network()

class Player:
    def __init__(self, name, position, avatar_path, chips):
        self.name = name
        self.position = position
        self.avatar = pygame.image.load(avatar_path).convert_alpha()
        self.avatar = pygame.transform.scale(self.avatar, (80, 80))
        self.chips = chips
        self.action_text = ""
        self.rect = pygame.Rect(self.position[0], self.position[1], 80, 80)

    def draw(self, screen):
        screen.blit(self.avatar, self.position)
        font = pygame.font.Font(None, 24)
        name_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_text, (self.position[0], self.position[1] - 20))

        chips_text = font.render(f"${self.chips}", True, (255, 255, 255))
        screen.blit(chips_text, (self.position[0], self.position[1] + 90))

        if self.action_text:
            self.draw_action_bubble(screen)

    def draw_action_bubble(self, screen):
        bubble_color = (255, 255, 255)
        text_color = (0, 0, 0)
        font = pygame.font.Font(None, 28)
        text_surf = font.render(self.action_text, True, text_color)
        text_rect = text_surf.get_rect(center=(self.position[0] + 70, self.position[1] - 5))
        bubble_rect = pygame.Rect(
            text_rect.x - 10, text_rect.y - 10, text_rect.width + 20, text_rect.height + 10
        )
        pygame.draw.rect(screen, bubble_color, bubble_rect, border_radius=10)
        screen.blit(text_surf, text_rect)

class Button:
    def __init__(self, x, y, width, height, text, color, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.action = action
        self.font = pygame.font.Font(None, 22)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

player_positions = [
    (60, 200),
    (450, 30),
    (890, 200),
    (85, 500),
    (500, 650),
]

players = [
    Player("Player 1", player_positions[0], "images/player1_avatar.png", 1000),
    Player("Player 2", player_positions[1], "images/player2_avatar.png", 1200),
    Player("Player 3", player_positions[2], "images/player3_avatar.png", 1500),
    Player("Player 4", player_positions[3], "images/player4_avatar.png", 1300),
    Player("YOU", player_positions[4], "images/player5_avatar.png", 2000),
]

button_texts = ["Call", "Raise", "Fold", "Check", "All-In"]
button_actions = ["call", "raise", "fold", "check", "allin"]
buttons = []
pot = 0
show_buttons = False

# Create buttons
def create_buttons():
    global buttons
    buttons = []
    x_start = 400
    y_start = 700
    button_width = 80
    button_height = 40
    padding = 20

    for i, (text, action) in enumerate(zip(button_texts, button_actions)):
        button_x = x_start + i * (button_width + padding)
        buttons.append(Button(button_x, y_start, button_width, button_height, text, (128, 128, 128), action))

# Draw pot value
def draw_pot(screen, pot):
    font = pygame.font.Font(None, 36)
    pot_text = font.render(f"Pot: ${pot}", True, (255, 255, 255))
    pot_rect = pot_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(pot_text, pot_rect)

# Main game loop
def main():
    run = True
    clock = pygame.time.Clock()
    create_buttons()

    while run:
        screen.fill((0, 0, 0))
        screen.blit(table_image, (0, 0))

        try:
            game_state = network.send(pickle.dumps({"action": "get_state"}))
            game_state = pickle.loads(game_state)
        except Exception as e:
            print("Failed to fetch game state:", e)
            break

        draw_pot(screen, game_state['pot'])
        for button in buttons:
            button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for button in buttons:
                    if button.is_clicked(pos):
                        action = button.action
                        amount = 100 if action in ["raise", "allin"] else 0
                        try:
                            response = network.send(pickle.dumps({"action": "player_action", "move": action, "amount": amount}))
                            print("Server Response:", pickle.loads(response))
                        except Exception as e:
                            print("Failed to send action:", e)

        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    main()
