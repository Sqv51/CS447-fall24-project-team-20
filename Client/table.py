import pygame
import pickle
import time
import socket

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(15)  # Set timeout before attempting to connect
        self.server = "192.168.196.52"
        self.port = 8888
        self.addr = (self.server, self.port)
        self.player_id = self.connect()
    def getPlayerID(self):
        return self.player_id

    def connect(self):
        try:
            self.client.connect(self.addr)
            print("Connected to server!")
            start_time = time.time()
            while True:
                if time.time() - start_time > 15:  # 15 seconds timeout
                    raise socket.timeout("Server did not respond in time.")
                try:
                    response = pickle.loads(self.client.recv(8192))  # Increased buffer size
                    if response.get("status") != "ok":
                        raise ConnectionError("Invalid server response")
                    return response.get("player_id")
                except BlockingIOError:
                    time.sleep(0.1)  # Wait a bit before retrying
        except socket.timeout:
            print("Server did not respond in time.")
            return None
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def send(self, data):
        try:
            self.client.sendall(data)
            return pickle.loads(self.client.recv(8192))  # Increased buffer size
        except socket.error as e:
            print(f"Socket error: {e}")
            return None

pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
POT = 0

class Player:
    def __init__(self, name, position, avatar_path, chips):
        self.name = name
        self.position = position
        try:
            self.avatar = pygame.image.load(avatar_path).convert_alpha()
            self.avatar = pygame.transform.scale(self.avatar, (80, 80))
        except FileNotFoundError:
            print(f"Avatar not found: {avatar_path}")
            self.avatar = pygame.Surface((80, 80))
            self.avatar.fill((200, 200, 200))
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


def fetch_game_state(network):
    try:
        response = network.send(pickle.dumps({"action": "get_state"}))
        if response:
            return response
    except Exception as e:
        print(f"Error fetching game state: {e}")
    return None


def sync_state(players, network):
    state = fetch_game_state(network)
    if state:
        global POT
        POT = state['pot']
        for idx, player in enumerate(players):
            player.chips = list(state['bets'].values())[idx]


def create_buttons(players, button_texts, button_color, button_actions):
    buttons = []
    x_start = players[-1].position[0] - 300
    y_start = players[-1].position[1] + 100
    for i, (text, action) in enumerate(zip(button_texts, button_actions)):
        button = Button(x_start + i * 65, y_start, 50, 20, text, button_color, action)
        buttons.append(button)
    return buttons


def draw_pot(screen, pot):
    font = pygame.font.Font(None, 36)
    pot_text = font.render(f"Pot: ${pot}", True, (255, 255, 255))
    pot_rect = pot_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(pot_text, pot_rect)


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Poker Game")
    try:
        table_image = pygame.image.load('images/poker_table.png').convert_alpha()
        table_image = pygame.transform.scale(table_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except FileNotFoundError:
        print("Table image not found!")
        pygame.quit()
        return

    player_positions = [(60, 200), (450, 30), (890, 200), (85, 500), (500, 650)]
    players = [Player(f"Player {i+1}", pos, f'images/player{i+1}_avatar.png', 1000) for i, pos in enumerate(player_positions)]

    button_texts = ["Call", "Raise", "Fold", "Check", "All-In"]
    button_actions = ["call", "raise", "fold", "check", "allin"]
    buttons = create_buttons(players, button_texts, (128, 128, 128), button_actions)

    '''
    network = Network()
    player_id = network.getPlayerID()
    if not player_id:
        print("Failed to connect to server.")
        return
    '''
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.is_clicked(event.pos):
                        pass
                        #network.send(pickle.dumps({"action": "player_action", "move": button.action, "amount": 0}))

        #sync_state(players, network)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
