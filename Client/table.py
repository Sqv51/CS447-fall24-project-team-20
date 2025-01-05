import pygame
from network import Network
import pickle
import time

pygame.init()

network = Network()

print("getting player id")
player_id = network.getP()
print(f"Player ID: {player_id}")

if not player_id:  # Connection failure
    print("Failed to connect to server. Exiting...")
    pygame.quit()
    exit()


def sync_state():
    global pot
    state = fetch_game_state()
    if state:
        # Update the pot and other UI elements
        pot = state['pot']
        for idx, player in enumerate(players):
            player.chips = state['bets'][player.name]  # Update player chips

def fetch_game_state():
    try:
        retries = 3
        while retries > 0:
            try:
                response = network.send(pickle.dumps({"action": "get_state"}))
                if response:
                    return response
            except Exception as e:
                retries -= 1
                time.sleep(1)
        return None

        return response  # Returns the server's response
    except Exception as e:
        print(f"Error fetching game state: {e}")
        return None


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Poker Game")


table_image = pygame.image.load("images/poker_table.png").convert_alpha()
table_image = pygame.transform.scale(table_image, (SCREEN_WIDTH, SCREEN_HEIGHT))


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
        """Draw a comment bubble above the player."""
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

    def is_clicked(self, pos):
        """Check if the player avatar is clicked."""
        return self.rect.collidepoint(pos)

# Button class
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
        """Check if the button is clicked."""
        return self.rect.collidepoint(pos)

player_positions = [
    (60, 200),  # Player 1 (top-left)
    (450, 30),  # Player 2 (top-center)
    (890, 200),  # Player 3 (top-right)
    (85, 500),  # Player 4 (bottom-left)
    (500, 650),  # You (bottom-center)
]

# Setup players
players = [
    Player("Player 1", player_positions[0], "images/player1_avatar.png", 1000),
    Player("Player 2", player_positions[1], "images/player2_avatar.png", 1200),
    Player("Player 3", player_positions[2], "images/player3_avatar.png", 1500),
    Player("Player 4", player_positions[3], "images/player4_avatar.png", 1300),
    Player("YOU", player_positions[4], "images/player5_avatar.png", 2000),  # client
]

# (initially hidden buttons, will be visible when clicked on) 
buttons = []
button_texts = ["Call", "Raise", "Fold", "Check", "All-In"]
button_color = (128, 128, 128)  
button_actions = ["call", "raise", "fold", "check", "allin"]


pot = 0


show_buttons = False

def create_buttons():
    """Buttons below the client player (YOU)."""
    global buttons
    buttons = []
    x_start = players[-1].position[0] - 300  
    y_start = players[-1].position[1] + 100 
    button_width = 50  
    button_height = 20  
    padding = 15  

    for i, (text, action) in enumerate(zip(button_texts, button_actions)):
        button_x = x_start + i * (button_width + padding)  
        button = Button(button_x, y_start, button_width, button_height, text, button_color, action)
        buttons.append(button)

def draw_pot(screen, pot):
    """Pot value in the center of the table."""
    font = pygame.font.Font(None, 36)
    pot_text = font.render(f"Pot: ${pot}", True, (255, 255, 255))
    pot_rect = pot_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(pot_text, pot_rect)


running = True
while running:
    screen.fill((0, 0, 0))  
    screen.blit(table_image, (0, 0))  

    for player in players:
        player.draw(screen)

   
    draw_pot(screen, pot)

    if show_buttons:
        for button in buttons:
            button.draw(screen)

    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if players[-1].is_clicked(pos):
                    show_buttons = True
                    create_buttons()

                for button in buttons:
                    if button.is_clicked(pos) and show_buttons:
                        players[-1].action_text = button.text
                        print(f"Button '{button.text}' clicked! Action: {button.action}")

                        # Send action to server
                        try:
                            action_data = {
                                "action": "player_action",
                                "move": button.action,
                                "amount": 100 if button.action in ["raise", "allin"] else 0
                            }
                            response = network.send(pickle.dumps(action_data))
                            pot = response["pot"]  # Update pot
                        except Exception as e:
                            print(f"Action failed: {e}")
    except Exception as e:
        print(f"Error in event loop: {e}")

    print("Syncing state...")
    sync_state()
    print("State synced.")
    pygame.display.flip()

pygame.quit()