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
        self.hands = {player: self.deck.draw(2) for player in players}
        self.community_cards = []
        self.turn = 0
        self.small_blind = 10
        self.big_blind = 20
        self.minimum_raise = 20
        self.pot = 0
        self.bets = {player: 0 for player in players}
        self.state = PokerGame.GameState.PRE_FLOP
        self.action_log = []  # Log for player actions
        self.post_blinds()

    def post_blinds(self):
        sb_player = self.players[self.turn % len(self.players)]
        bb_player = self.players[(self.turn + 1) % len(self.players)]
        self.place_bet(sb_player, self.small_blind)
        self.place_bet(bb_player, self.big_blind)
        self.action_log.append(f"{sb_player.name} posted small blind {self.small_blind}")
        self.action_log.append(f"{bb_player.name} posted big blind {self.big_blind}")

    def deal_community(self, count):
        self.community_cards.extend(self.deck.draw(count))

    def player_action(self, player, action, amount=0):
        if player.folded:
            return

        if action == PokerGame.Moves.BET:
            if amount < self.minimum_raise or amount > player.balance:
                raise ValueError("Invalid bet amount.")
            self.place_bet(player, amount)
            self.action_log.append(f"{player.name} bet {amount}")
        elif action == PokerGame.Moves.CALL:
            max_bet = max(self.bets.values())
            if self.bets[player] < max_bet:
                self.place_bet(player, max_bet - self.bets[player])
                self.action_log.append(f"{player.name} called {max_bet}")
            else:
                raise ValueError("Nothing to call.")
        elif action == PokerGame.Moves.RAISE:
            if amount < self.minimum_raise or amount > player.balance:
                raise ValueError("Invalid raise amount.")
            self.place_bet(player, amount)
            self.action_log.append(f"{player.name} raised to {amount}")
        elif action == PokerGame.Moves.FOLD:
            player.folded = True
            self.action_log.append(f"{player.name} folded")
        elif action == PokerGame.Moves.CHECK:
            max_bet = max(self.bets.values())
            if self.bets[player] < max_bet:
                raise ValueError("Cannot check, must call or fold.")
            self.action_log.append(f"{player.name} checked")
        else:
            raise ValueError("Invalid action.")

    def evaluate(self):
        evaluator = Evaluator()
        scores = {}
        for player, hand in self.hands.items():
            if not player.folded:
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
        if len([p for p in self.players if not p.folded]) == 1:
            return
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
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) == 1:
            winner = active_players[0]
            winner.balance += self.pot
            self.action_log.append(f"{winner.name} wins the pot of {self.pot} by default (all others folded)")
            self.pot = 0
            return winner

        scores = self.evaluate()
        winner = min(scores, key=scores.get)
        winning_hand = scores[winner]
        winner.balance += self.pot
        self.action_log.append(f"{winner.name} wins the pot of {self.pot} with a score of {winning_hand}")
        self.pot = 0
        return winner

    def get_player_decision(self, player):
        decision = [None]
        input_received = [False]

        def timer_thread():
            for i in range(60, 0, -1):
                if input_received[0]:
                    print("\r", end="")
                    return
                print(f"\rTime left: {i} seconds", end="")
                time.sleep(1)
            print("\n")

        def input_thread():
            try:
                print(f"Game State: {self.state.value}")
                print(f"Pot: {self.pot}")
                print(f"Blinds: Small Blind = {self.small_blind}, Big Blind = {self.big_blind}")
                print("Community Cards:", [Card.int_to_str(c) for c in self.community_cards])
                print(f"{player.name}'s balance: {player.balance}")
                print(f"{player.name}'s cards: ", [Card.int_to_str(c) for c in self.hands[player]])
                user_input = input(f"{player.name}, enter your action (bet, call, raise, fold, check): ").strip().lower()
                if user_input.startswith('bet') or user_input.startswith('raise'):
                    parts = user_input.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        decision[0] = (PokerGame.Moves[user_input.split()[0].upper()], int(parts[1]))
                    else:
                        decision[0] = (PokerGame.Moves.FOLD, 0)
                elif user_input in ['call', 'fold', 'check']:
                    decision[0] = (PokerGame.Moves[user_input.upper()], 0)
                else:
                    decision[0] = (PokerGame.Moves.FOLD, 0)
                input_received[0] = True
            except Exception:
                decision[0] = (PokerGame.Moves.FOLD, 0)

        timer = threading.Thread(target=timer_thread)
        input_t = threading.Thread(target=input_thread)
        timer.start()
        input_t.start()
        input_t.join(timeout=60)

        if not input_received[0]:
            print(f"{player.name} took too long. Default action: fold.")
            return PokerGame.Moves.FOLD, 0
        return decision[0]

    def play(self):
        while len([p for p in self.players if not p.folded]) > 1:
            player = self.players[self.turn % len(self.players)]
            if player.folded:
                self.turn += 1
                continue
            print(f"{player.name}'s turn.")
            action, amount = self.get_player_decision(player)
            try:
                self.player_action(player, action, amount)
            except ValueError as e:
                print(e)
            self.turn += 1
            if self.turn % len(self.players) == 0:
                self.next_stage()
        winner = self.get_winner()
        print("\nGame Summary:")
        for log in self.action_log:
            print(log)
        print(f"{winner.name} wins the pot of {self.pot}.")
        print(f"{winner.name}'s balance is now {winner.balance}.")
        print("Game Over.")


if __name__ == "__main__":
    players = [Player("Alice", 1000), Player("Bob", 1000), Player("Charlie", 1000)]
    game = PokerGame(players)
    game.play()
