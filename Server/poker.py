import random
import time
from enum import Enum
from treys import Card, Deck, Evaluator  # pip install treys for this to work
from flask import jsonify


class Player:

    class PlayerState(Enum):
        CONNECTING = 'connecting'
        CONNECTED = 'connected'
        READY = 'ready'
        BANKRUPT = 'bankrupt'


    def __init__(self, name, balance):
        self.name = name
        self.balance = balance
        self.bankrupt = False
        self.folded = False




class PokerGame:

    class GameState(Enum):
        PRE_FLOP = 'pre-flop'
        FLOP = 'flop'
        TURN = 'turn'
        RIVER = 'river'
        SHOWDOWN = 'showdown'

    class Moves(Enum):
        BET = 'bet'
        CALL = 'call'
        RAISE = 'raise'
        FOLD = 'fold'
        CHECK = 'check'
        ALLIN = 'all-in'

    def __init__(self, players):
        self.players = players
        self.deck = Deck()
        self.community_cards = []
        self.turn = 0
        self.small_blind = 10
        self.big_blind = 20
        self.minimum_raise = 20
        self.pot = 0
        self.state = PokerGame.GameState.PRE_FLOP
        self.action_log = []

        while len([player for player in self.players if not player.bankrupt]) > 1:
            self.play_round()

    def play_round(self):
        # Reset round variables
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.bets = {player: 0 for player in self.players}
        self.state = PokerGame.GameState.PRE_FLOP

        # Deal hands to players
        self.hands = {player: self.deck.draw(2) for player in self.players}
        self.post_blinds()

        # Play betting rounds
        while self.state != PokerGame.GameState.SHOWDOWN:
            self.handle_round()

        # Evaluate winner and distribute pot
        self.distribute_pot()

    def post_blinds(self):
        sb_player = self.players[self.turn % len(self.players)]
        bb_player = self.players[(self.turn + 1) % len(self.players)]
        self.place_bet(sb_player, self.small_blind)
        self.place_bet(bb_player, self.big_blind)

    def deal_community(self, count):
        self.community_cards.extend(self.deck.draw(count))
        self.action_log.append(f"Dealt {count} community cards: {[Card.int_to_str(c) for c in self.community_cards]}")

    def player_action(self, player, action, amount=0):
        if player.folded:
            return

        if action == PokerGame.Moves.BET:
            if amount < self.minimum_raise or amount > player.balance:
                raise ValueError("Invalid bet amount.")
            self.place_bet(player, amount)
        elif action == PokerGame.Moves.FOLD:
            player.folded = True

    # Broadcast state after each action
    socketio.emit('game_update', self.send_game_info())


    # Broadcast state after each action
    socketio.emit('game_update', self.send_game_info())

    def distribute_pot(self):
        active_players = [p for p in self.players if not p.folded]
        winner = active_players[0]  # Simplified winner selection
        winner.balance += self.pot
        self.pot = 0

    def handle_round(self):
        if self.state == PokerGame.GameState.PRE_FLOP:
            self.deal_community(3)
            self.state = PokerGame.GameState.FLOP
        elif self.state == PokerGame.GameState.FLOP:
            self.deal_community(1)
            self.state = PokerGame.GameState.TURN
        elif self.state == PokerGame.GameState.TURN:
            self.deal_community(1)
            self.state = PokerGame.GameState.RIVER
        elif self.state == PokerGame.GameState.RIVER:
            self.state = PokerGame.GameState.SHOWDOWN

    def send_game_info(self):
        return jsonify({
            "pot": self.pot,
            "bets": {p.name: 0 for p in self.players},
            "community_cards": [Card.int_to_str(c) for c in self.community_cards],
            "state": self.state.value
        })

if __name__ == "__main__":
    players = [Player("Alice", 1000), Player("Bob", 1000)]
    game = PokerGame(players)

    print(game.action_log)
