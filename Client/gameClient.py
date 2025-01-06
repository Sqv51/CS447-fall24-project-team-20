import pygame
import pickle
import time
import os

from network import Network  # network.py'deki Network sınıfını içe aktarın

# Ekran Boyutları
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# Global pot değeri (örnek)
POT = 0

class Player:
    def __init__(self, name, position, avatar_path, chips):
        self.name = name
        self.position = position
        self.chips = chips
        self.action_text = ""

        try:
            self.avatar = pygame.image.load(avatar_path).convert_alpha()
            self.avatar = pygame.transform.scale(self.avatar, (80, 80))
        except FileNotFoundError:
            print(f"Avatar not found: {avatar_path}")
            self.avatar = pygame.Surface((80, 80))
            self.avatar.fill((200, 200, 200))

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
            text_rect.x - 10, text_rect.y - 10,
            text_rect.width + 20, text_rect.height + 10
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
    """Sunucudan güncel oyun durumunu çeker."""
    try:
        request = {"action": "get_state"}
        response = network.send(pickle.dumps(request))
        return response
    except Exception as e:
        print(f"Error fetching game state: {e}")
    return None


def sync_state(players, network):
    """Sunucudan çekilen state ile oyuncu bilgilerini ve potu günceller."""
    global POT
    state = fetch_game_state(network)
    if state:
        POT = state.get('pot', 0)

        # Burada sunucunun döndürdüğü formata göre players'ı güncelleyin
        if 'other_players' in state:
            for p in players:
                if p.name == state['player_name']:
                    p.chips = state['player_balance']
                else:
                    for op in state['other_players']:
                        if op['name'] == p.name:
                            p.chips = op['balance']


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


def handle_action(action, network):
    """
    Buton tıklanınca sunucuya player_action isteği gönderir.
    raise/bet için sabit amount örneği konulabilir,
    istenirse kullanıcıdan girdi alarak da yapabilirsiniz.
    """
    try:
        amount = 0
        if action == "raise":
            amount = 50
        elif action == "allin":
            amount = 9999

        data_to_send = {
            "action": "player_action",
            "move": action,
            "amount": amount
        }
        response = network.send(pickle.dumps(data_to_send))
        if response:
            print("Action response:", response)
            # Gerekirse burada sync_state(players, network) çağırabilirsiniz.

    except Exception as e:
        print(f"Error sending action: {e}")


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Poker Game")

    # Network nesnesi oluşturup sunucuya bağlanıyoruz
    network = Network()
    if network.getP() is None:
        print("Sunucuya bağlanılamadı. Program sonlandırılıyor.")
        return
    else:
        print("Sunucuya bağlandınız, player_id:", network.getP())

    # Arkaplan masa görüntüsünü yükleme
    try:
        table_image = pygame.image.load('images/poker_table.png').convert_alpha()
        table_image = pygame.transform.scale(table_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except FileNotFoundError:
        print("Table image not found! Exiting...")
        pygame.quit()
        return

    # Örnek pozisyonlar
    player_positions = [
        (60, 200),
        (450, 30),
        (890, 200),
        (85, 500),
        (500, 650)
    ]
    # Örnek 5 oyuncu
    players = [
        Player(f"Player {i+1}", pos, f'images/player{i+1}_avatar.png', 1000)
        for i, pos in enumerate(player_positions)
    ]

    # Butonlar
    button_texts = ["Call", "Raise", "Fold", "Check", "All-In"]
    button_actions = ["call", "raise", "fold", "check", "allin"]
    buttons = create_buttons(players, button_texts, (128, 128, 128), button_actions)

    clock = pygame.time.Clock()
    running = True
    last_sync_time = pygame.time.get_ticks()

    while running:
        screen.fill((0, 0, 0))
        screen.blit(table_image, (0, 0))

        # 2 saniyede bir sunucudan durumu güncelle
        current_time = pygame.time.get_ticks()
        if current_time - last_sync_time > 2000:
            sync_state(players, network)
            last_sync_time = current_time

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
                        handle_action(button.action, network)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()