# gameClient.py

import treys
import pygame
import pickle
import time
import os

from treys import Card, Deck
from network import Network

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
POT = 0                # Global pot miktarı
FULL_DECK = []         # 52 kartlık deste (opsiyonel)
COMMUNITY_CARDS = []   # Topluluk (community) kartları
MY_CARDS = []          # Local oyuncunun elindeki kartlar

def get_emoji(card):
    suits = {'s': '♠️', 'h': '♥️', 'd': '♦️', 'c': '♣️'}
    values = {'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': '10'}
    values.update({str(i): str(i) for i in range(2, 10)})

    value = card[:-1]  # Extract value (e.g., 'J' in 'Jc')
    suit = card[-1]  # Extract suit (e.g., 'c' in 'Jc')

    return f"{values[value]}({suits[suit]})"

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
        # Avatar
        screen.blit(self.avatar, self.position)

        # İsim / fiş
        font = pygame.font.Font(None, 24)
        name_text = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_text, (self.position[0], self.position[1] - 20))

        chips_text = font.render(f"${self.chips}", True, (255, 255, 255))
        screen.blit(chips_text, (self.position[0], self.position[1] + 90))

        # Aksiyon balonu (örn. "Raised 50", "Folded" vb.)
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
        self.enabled = True  # Buton aktif/pasif

    def draw(self, screen):
        if self.enabled:
            bg_color = self.color
            text_color = (255, 255, 255)
        else:
            bg_color = (90, 90, 90)
            text_color = (150, 150, 150)

        pygame.draw.rect(screen, bg_color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


def get_user_input(screen, prompt="Enter amount:"):
    """
    Küçük bir pop-up input penceresi: Klavyeden sayı girer,
    Enter veya Esc ile çıkar. Dönen stringi handle_action'ta int'e çevirebilirsiniz.
    """
    font = pygame.font.Font(None, 32)
    input_box = pygame.Rect(350, 300, 300, 50)
    user_text = ""
    active = True

    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    user_text += event.unicode

        screen.fill((0, 0, 0))
        prompt_surf = font.render(prompt, True, (255, 255, 255))
        screen.blit(prompt_surf, (input_box.x, input_box.y - 40))

        txt_surf = font.render(user_text, True, (255, 255, 255))
        pygame.draw.rect(screen, (50, 50, 50), input_box, border_radius=5)
        screen.blit(txt_surf, (input_box.x + 5, input_box.y + 10))

        pygame.display.flip()

    return user_text


def fetch_game_state(network):
    """
    Sunucuya 'get_state' isteği gönderir ve cevabı döndürür.
    """
    try:
        request = {"action": "get_state"}
        response = network.send(pickle.dumps(request))
        return response
    except Exception as e:
        print(f"Error fetching game state: {e}")
    return None


def sync_state(players, buttons, network):
    """
    Sunucudan gelen state'e göre pot, valid_actions, community_cards, my_cards vb. günceller.
    """
    global POT, FULL_DECK, COMMUNITY_CARDS, MY_CARDS

    state = fetch_game_state(network)
    if state:
        POT = state.get('pot', 0)

        valid_actions = state.get('valid_actions', [])
        for btn in buttons:
            btn.enabled = (btn.action in valid_actions)

        # Oyuncu fiş güncellemeleri
        if 'other_players' in state:
            for p in players:
                if p.name == state.get('player_name'):
                    p.chips = state.get('player_balance')
                else:
                    for op in state['other_players']:
                        if op['name'] == p.name:
                            p.chips = op['balance']

        # 52 kartlık deste (opsiyonel)
        if 'full_deck' in state:
            FULL_DECK = state['full_deck']

        # Topluluk kartları
        if 'community_cards' in state:
            COMMUNITY_CARDS = state['community_cards']


        # Kendi kartlarımız
        if 'player_cards' in state:
            MY_CARDS = state['player_cards']
        else:
            MY_CARDS = []


def draw_board_info(screen):
    """
    Pot, community_cards, my_cards yazılarını ekrana çizer.
    Pot: ekranda ortanın biraz altında
    Community Cards: potun hemen altında
    Your Cards: Onun da altında
    """
    # 1) Pot
    pot_font = pygame.font.Font(None, 36)
    pot_text = pot_font.render(f"Pot: ${POT}", True, (255, 255, 255))
    # Ekranın merkezinden 50 px aşağı
    pot_rect = pot_text.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 50))
    screen.blit(pot_text, pot_rect)

    # 2) Community Cards
    comm_font = pygame.font.Font(None, 24)
    if COMMUNITY_CARDS:
        comm_str = "Community Cards: " + " ".join(COMMUNITY_CARDS)
    else:
        comm_str = "No community cards yet"
    comm_surf = comm_font.render(comm_str, True, (255, 255, 255))
    comm_rect = comm_surf.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 80))
    screen.blit(comm_surf, comm_rect)

    # 3) Your Cards
    my_font = pygame.font.Font(None, 24)
    if MY_CARDS:
        my_str = "Your Cards: " + " ".join(MY_CARDS)
    else:
        my_str = "You have no cards"
    my_surf = my_font.render(my_str, True, (255, 255, 255))
    my_rect = my_surf.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + 110))
    screen.blit(my_surf, my_rect)


def handle_action(action, network, screen=None):
    """
    'bet' veya 'raise' -> kullanıcıdan miktar al, sunucuya gönder.
    'call', 'fold', 'check', 'allin' vb. -> direkt gönder.
    """
    try:
        amount = 0
        if action == "raise":
            if screen is not None:
                input_str = get_user_input(screen, "Raise amount:")
                if input_str is None:
                    print("Raise canceled.")
                    return
                try:
                    amount = int(input_str)
                except ValueError:
                    amount = 0
                    print("Invalid input, defaulting to 0")

        elif action == "bet":
            if screen is not None:
                input_str = get_user_input(screen, "Bet amount:")
                if input_str is None:
                    print("Bet canceled.")
                    return
                try:
                    amount = int(input_str)
                except ValueError:
                    amount = 0
                    print("Invalid input, defaulting to 0")

        elif action == "allin":
            amount = 9999  # Örnek sabit

        data_to_send = {
            "action": "player_action",
            "move": action,
            "amount": amount
        }
        response = network.send(pickle.dumps(data_to_send))
        if response:
            print("Action response:", response)

    except Exception as e:
        print(f"Error sending action: {e}")


def create_buttons(players):
    """
    6 aksiyon: Call, Bet, Raise, Fold, Check, All-In
    """
    texts = ["Call", "Bet", "Raise", "Fold", "Check", "All-In"]
    actions = ["call", "bet", "raise", "fold", "check", "allin"]

    buttons = []
    x_start = players[-1].position[0] - 300
    y_start = players[-1].position[1] + 100
    for i, (txt, act) in enumerate(zip(texts, actions)):
        btn = Button(x_start + i * 65, y_start, 50, 20, txt, (128, 128, 128), act)
        buttons.append(btn)
    return buttons


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Poker Game - Show Your Cards & Community Cards")

    network = Network()
    if network.getP() is None:
        print("Sunucuya bağlanılamadı. Program sonlandırılıyor.")
        return
    else:
        print("Sunucuya bağlanıldı, player_id:", network.getP())

    # Masa resmi
    try:
        table_image = pygame.image.load(os.path.join("images", "poker_table.png")).convert_alpha()
        table_image = pygame.transform.scale(table_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except FileNotFoundError:
        table_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        table_image.fill((0, 100, 0))

    # Oyuncular
    player_positions = [
        (60, 200),
        (450, 30),
        (890, 200),
        (85, 500),
        (500, 650)
    ]
    players = [
        Player(f"Player {i+1}", pos, f'images/player{i+1}_avatar.png', 1000)
        for i, pos in enumerate(player_positions)
    ]

    # Butonları yarat
    buttons = create_buttons(players)

    clock = pygame.time.Clock()
    running = True
    last_sync_time = pygame.time.get_ticks()

    while running:
        screen.blit(table_image, (0, 0))

        # Belirli aralıklarla senkronizasyon
        current_time = pygame.time.get_ticks()
        if current_time - last_sync_time > 2000:
            sync_state(players, buttons, network)
            last_sync_time = current_time

        # Oyuncuları çiz
        for p in players:
            p.draw(screen)

        # Pot + community + your cards:
        draw_board_info(screen)

        # Butonları çiz
        for btn in buttons:
            btn.draw(screen)

        # Event döngüsü
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                for btn in buttons:
                    if btn.is_clicked(mouse_pos):
                        handle_action(btn.action, network, screen=screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()