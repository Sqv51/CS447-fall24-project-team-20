import pygame
from player import Player
from table import Table
from button import Button

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Poker Table")
        self.table = Table((400, 300), 200, 5)
        self.running = True
        self.pot = 0
        self.active_player = None
        self.buttons = []
        self.create_players()

    def create_players(self):
        player_data = [
            ("Player 1", "player1.png", 1000),
            ("Player 2", "player2.png", 1500),
            ("Player 3", "player3.png", 2000),
            ("Player 4", "player4.png", 1200),
            ("You", "player5.png", 1800),
        ]
        for i, (name, image, chips) in enumerate(player_data):
            position = self.table.positions[i]
            player = Player(name, position, image, chips)
            self.table.add_player(player)

    def create_buttons(self, x, y):
        """Create buttons near the clicked player."""
        button_texts = ["Call", "Check", "Raise", "Fold", "All-In"]
        button_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (128, 128, 128), (255, 255, 0)]
        button_actions = ["call", "check", "raise", "fold", "allin"]
        self.buttons = []  
        for i, (text, color, action) in enumerate(zip(button_texts, button_colors, button_actions)):
            button = Button(x + i * 110, y, 100, 40, text, color, action)
            self.buttons.append(button)

    def run(self):
        while self.running:
            self.screen.fill((34, 139, 34))
            self.table.draw(self.screen)

            
            if self.active_player:
                for button in self.buttons:
                    button.draw(self.screen)

         
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                
                    for player in self.table.players:
                        if player.is_clicked(pos):
                            self.active_player = player
                            self.create_buttons(player.position[0], player.position[1] + 80)
                            break
              
                    for button in self.buttons:
                        if button.is_clicked(pos):
                            print(f"{button.text} clicked for {self.active_player.name}")
                            break

            pygame.display.flip()

        pygame.quit()