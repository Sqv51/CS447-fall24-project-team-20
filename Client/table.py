import pygame
import pickle
import time
import socket

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(15)  # Set timeout before attempting to connect
        self.server = "192.168.196.52"
        #localhost
        #self.server = "127.0.0.1"
        self.port = 43513
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            # Attempt to connect
            self.client.connect(self.addr)
            print("Connected to server!")

            # Receive initial response
            response = pickle.loads(self.client.recv(2048))
            if response.get("status") != "ok":  # Check for valid server response
                raise ConnectionError("Invalid server response")

            return response.get("player_id")  # Return player ID
        except socket.timeout:
            print("Server did not respond in time.")
            return None
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def send(self, data):
        try:
            # Send data without encoding (already pickled)
            self.client.send(data)

            # Receive and return response
            return pickle.loads(self.client.recv(8192))  # Increased buffer size to 8192
        except socket.error as e:
            print(f"Socket error: {e}")
            return None

pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
POT = 0

# Classes
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

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


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


# Functions
def fetch_game_state(network):
    try:
        retries = 5
        while retries > 0:
            try:
                response = network.send(pickle.dumps({"action": "get_state"}), timeout=5)
                if response:
                    return response
            except Exception:
                retries -= 1
                time.sleep(2)
        return None
    except Exception as e:
        print(f"Error fetching game state: {e}")
        return None


def sync_state(players, network):
    state = fetch_game_state(network)
    if state:
        global POT
        POT = state['pot']
        for idx, player in enumerate(players):
            player.chips = state['bets'][player.name]


def create_buttons(players, button_texts, button_color, button_actions):
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
    return buttons


def draw_pot(screen, pot):
    font = pygame.font.Font(None, 36)
    pot_text = font.render(f"Pot: ${pot}", True, (255, 255, 255))
    pot_rect = pot_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(pot_text, pot_rect)


# Main function
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Poker Game")
    table_image = pygame.image.load('images/poker_table.png').convert_alpha()
    table_image = pygame.transform.scale(table_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Setup players
    player_positions = [
        (60, 200), (450, 30), (890, 200), (85, 500), (500, 650)
    ]
    players = [
        Player("Player 1", player_positions[0], 'images/player1_avatar.png', 1000),
        Player("Player 2", player_positions[1], 'images/player2_avatar.png', 1200),
        Player("Player 3", player_positions[2], 'images/player3_avatar.png', 1500),
        Player("Player 4", player_positions[3], 'images/player4_avatar.png', 1300),
        Player("Player 5", player_positions[4], 'images/player5_avatar.png', 2000),
    ]


    # Buttons
    button_texts = ["Call", "Raise", "Fold", "Check", "All-In"]
    button_color = (128, 128, 128)
    button_actions = ["call", "raise", "fold", "check", "allin"]
    buttons = create_buttons(players, button_texts, button_color, button_actions)


    network = Network()
    player_id = network.getP()
    if not player_id:
        print("Failed to connect to server.")
        return


    running = True
    while running:
        screen.fill((0, 0, 0))
        screen.blit(table_image, (0, 0))
        for player in players:
            player.draw(screen)
        draw_pot(screen, POT)
        for button in buttons:
            button.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        sync_state(players, network)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

