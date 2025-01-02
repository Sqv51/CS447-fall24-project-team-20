import random
import threading
import time
from enum import Enum
from treys import Card, Deck, Evaluator  # pip install treys for this to work


class Player:
    def __init__(self, name, balance):
        self.name = name
        self.balance = balance
        self.bankrupt = False


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
        self.hands = {player: self.deck.draw(2) for player in players}
        self.community_cards = []
        self.turn = 0
        self.small_blind = 10
        self.big_blind = 20
        self.minimum_raise = 20
        self.pot = 0
        self.bets = {player: 0 for player in players}
        self.state = PokerGame.GameState.PRE_FLOP
        self.post_blinds()

    def post_blinds(self):
        # Assign small and big blinds
        sb_player = self.players[self.turn % len(self.players)]
        bb_player = self.players[(self.turn + 1) % len(self.players)]
        self.place_bet(sb_player, self.small_blind)
        self.place_bet(bb_player, self.big_blind)

    def deal_community(self, count):
        self.community_cards.extend(self.deck.draw(count))

    def player_action(self, player, action, amount=0):
        if action == PokerGame.Moves.BET:
            if amount < self.minimum_raise or amount > player.balance:
                raise ValueError("Invalid bet amount.")
            self.place_bet(player, amount)
        elif action == PokerGame.Moves.CALL:
            max_bet = max(self.bets.values())
            self.place_bet(player, max_bet - self.bets[player])
        elif action == PokerGame.Moves.RAISE:
            if amount < self.minimum_raise or amount > player.balance:
                raise ValueError("Invalid raise amount.")
            self.place_bet(player, amount)
        elif action == PokerGame.Moves.FOLD:
            self.players.remove(player)
        elif action == PokerGame.Moves.CHECK:
            pass
        else:
            raise ValueError("Invalid action.")

    def evaluate(self):
        evaluator = Evaluator()
        scores = {}
        for player, hand in self.hands.items():
            score = evaluator.evaluate(hand, self.community_cards)
            scores[player] = score
        return scores

    def place_bet(self, player, amount):
        if player.balance < amount:
            raise ValueError("Insufficient balance to place bet.")
        player.balance -= amount
        self.bets[player] += amount
        self.pot += amount

    def next_stage(self):
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

    def get_winner(self):
        scores = self.evaluate()
        winner = min(scores, key=scores.get)
        winner.balance += self.pot
        self.pot = 0
        return winner

    def get_player_decision(self, player):
        decision = [None]

        def input_thread():
            try:
                while decision[0] is None:
                    print(f"Game State: {self.state.value}")
                    print(f"Pot: {self.pot}")
                    print(f"Blinds: Small Blind = {self.small_blind}, Big Blind = {self.big_blind}")
                    print("Community Cards:", [Card.int_to_str(c) for c in self.community_cards])
                    print(f"{player.name}'s balance: {player.balance}")
                    print("Other Players:")
                    for p in self.players:
                        if p != player:
                            print(f"{p.name} - Bet: {self.bets[p]}, Balance: {p.balance}")
                    print(f"{player.name}'s cards: ", [Card.int_to_str(c) for c in self.hands[player]])

                    # Countdown timer
                    for i in range(10, 0, -1):
                        print(f"Time left: {i} seconds", end='\r')
                        time.sleep(1)

                    user_input = input(f"{player.name}, enter your action (bet, call, raise, fold, check): ").strip().lower()
                    if user_input.startswith('bet') or user_input.startswith('raise'):
                        parts = user_input.split()
                        if len(parts) == 2 and parts[1].isdigit():
                            decision[0] = (PokerGame.Moves[user_input.split()[0].upper()], int(parts[1]))
                        else:
                            print("Invalid input. Try again.")
                    elif user_input in ['call', 'fold', 'check']:
                        decision[0] = (PokerGame.Moves[user_input.upper()], 0)
                    else:
                        print("Invalid input. Try again.")
            except Exception:
                decision[0] = (PokerGame.Moves.FOLD, 0)

        thread = threading.Thread(target=input_thread)
        thread.start()
        thread.join(timeout=60)

        if decision[0] is None:
            print(f"{player.name} took too long. Default action: fold.")
            return PokerGame.Moves.FOLD, 0
        return decision[0]

    def play(self):
        while len(self.players) > 1:
            player = self.players[self.turn % len(self.players)]
            print(f"{player.name}'s turn.")
            action, amount = self.get_player_decision(player)
            try:
                self.player_action(player, action, amount)
            except ValueError as e:
                print(e)
            self.turn += 1
            if self.turn % len(self.players) == 0:
                self.next_stage()
        self.next_stage()
        winner = self.get_winner()
        print(f"{winner.name} wins the pot of {self.pot}.")
        print(f"{winner.name}'s balance is now {winner.balance}.")
        print("Game Over.")


# Example Game Setup
if __name__ == "__main__":
    players = [Player("Alice", 1000), Player("Bob", 1000), Player("Charlie", 1000)]
    game = PokerGame(players)
    game.play()
