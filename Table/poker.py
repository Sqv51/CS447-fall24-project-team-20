import random
import time
from network import Network
import pickle
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
        self.hands = {}  # Initialize empty hands dict
        self.community_cards = []
        self.turn = 0  # Dealer position
        self.current_player = None  # Don't set this yet
        self.small_blind = 10
        self.big_blind = 20
        self.minimum_raise = 20
        self.pot = 0
        self.bets = {player: 0 for player in players}
        self.last_raiser = None
        self.state = PokerGame.GameState.PRE_FLOP
        self.action_log = []
        self.round_complete = False

        # Only deal cards and post blinds if we have enough players
        if len(players) >= 2:
            self.deal_initial_cards()
            self.post_blinds()
            # Set current_player after blinds are posted
            self.current_player = (self.turn + 2) % len(self.players)  # Start with player after big blind

    def deal_initial_cards(self):
        """Deal initial cards to all players."""
        for player in self.players:
            self.hands[player] = self.deck.draw(2)

    def get_player_state(self, player_id):
        """Returns game state specific to the given player."""
        # Validate player_id is within bounds
        if player_id < 0 or player_id >= len(self.players):
            raise ValueError(f"Invalid player_id: {player_id}")

        player = self.players[player_id]
        other_players = [p for p in self.players if p != player]

        # Check if game has enough players to start
        if len(self.players) < 2:
            return {
                'player_name': player.name,
                'player_balance': player.balance,
                'player_cards': [],
                'community_cards': [],
                'other_players': [],
                'pot': 0,
                'current_bet': 0,
                'min_raise': self.minimum_raise,
                'player_bet': 0,
                'game_stage': 'waiting_for_players',
                'valid_actions': [],
                'action_log': ['Waiting for more players to join...'],
                'is_turn': False,
                'current_player': None
            }

        # Ensure player has cards
        player_cards = self.hands.get(player, [])

        # Fix turn checking logic
        is_players_turn = (self.current_player is not None and
                           player == self.players[self.current_player] and
                           not player.folded and
                           self.state != PokerGame.GameState.SHOWDOWN)

        return {
            'player_name': player.name,
            'player_balance': player.balance,
            'player_cards': [Card.int_to_str(c) for c in player_cards],
            'community_cards': [Card.int_to_str(c) for c in self.community_cards],
            'other_players': [{
                'name': p.name,
                'balance': p.balance,
                'bet': self.bets[p],
                'folded': p.folded,
                'cards': ['??', '??'] if not p.folded else None
            } for p in other_players],
            'pot': self.pot,
            'current_bet': max(self.bets.values()),
            'min_raise': self.minimum_raise,
            'player_bet': self.bets[player],
            'game_stage': self.state.value,
            'valid_actions': self.get_valid_actions(player) if is_players_turn else [],
            'action_log': self.action_log[-5:],
            'is_turn': is_players_turn,
            'current_player': self.players[self.current_player].name if self.current_player is not None else None
        }

    def gameStateJson(self):
        return {
            'players': [player.name for player in self.players],
            'hands': {player.name: [Card.int_to_str(c) for c in self.hands[player]] for player in self.players},
            'community_cards': [Card.int_to_str(c) for c in self.community_cards],
            'turn': self.turn,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'minimum_raise': self.minimum_raise,
            'pot': self.pot,
            'bets': {player.name: self.bets[player] for player in self.players},
            'state': self.state.value,
            'action_log': self.action_log
        }

    def playerCardsJson(self):
        return {player.name: [Card.int_to_str(c) for c in self.hands[player]] for player in self.players}

    def post_blinds(self):
        # Post small blind
        sb_player = self.players[(self.turn + 1) % len(self.players)]
        self.place_bet(sb_player, self.small_blind)
        self.action_log.append(f"{sb_player.name} posted small blind {self.small_blind}")

        # Post big blind
        bb_player = self.players[(self.turn + 2) % len(self.players)]
        self.place_bet(bb_player, self.big_blind)
        self.action_log.append(f"{bb_player.name} posted big blind {self.big_blind}")

        # Last raiser is the big blind
        self.last_raiser = bb_player
    def deal_community(self, count):
        self.community_cards.extend(self.deck.draw(count))

    def player_action(self, player, action, amount=0):
        # Verify it's actually this player's turn
        if self.players[self.current_player] != player:
            return False

        if player.folded:
            return False

        max_bet = max(self.bets.values())
        current_bet = self.bets[player]

        try:
            if action == PokerGame.Moves.FOLD:
                player.folded = True
                self.action_log.append(f"{player.name} folded")
                self.next_player()
                return True

            elif action == PokerGame.Moves.CHECK:
                if max_bet > current_bet:
                    raise ValueError("Cannot check when there are outstanding bets")
                self.action_log.append(f"{player.name} checked")
                self.next_player()
                return True

            elif action == PokerGame.Moves.CALL:
                call_amount = max_bet - current_bet
                if call_amount > 0:
                    self.place_bet(player, call_amount)
                    self.action_log.append(f"{player.name} called {call_amount}")
                else:
                    self.action_log.append(f"{player.name} checked")
                self.next_player()
                return True

            elif action == PokerGame.Moves.RAISE:
                if amount < max_bet + self.minimum_raise:
                    raise ValueError(f"Raise must be at least {max_bet + self.minimum_raise}")
                self.place_bet(player, amount - current_bet)
                self.action_log.append(f"{player.name} raised to {amount}")
                self.last_raiser = player
                self.round_complete = False
                self.next_player()
                return True

            elif action == PokerGame.Moves.BET:
                if max_bet > 0:
                    raise ValueError("Cannot bet when there are outstanding bets. Use raise instead.")
                if amount < self.minimum_raise:
                    raise ValueError(f"Bet must be at least {self.minimum_raise}")
                self.place_bet(player, amount)
                self.action_log.append(f"{player.name} bet {amount}")
                self.last_raiser = player
                self.round_complete = False
                self.next_player()
                return True

            return False

        except ValueError as e:
            self.action_log.append(f"Invalid action by {player.name}: {str(e)}")
            return False

    def sync_with_server(self):
        try:
            # Send request to get updated state
            updated_state = self.network.send(pickle.dumps({"action": "get_state"}))
            # Update game state locally
            server_state = pickle.loads(updated_state)
            self.pot = server_state['pot']
            self.bets = server_state['bets']
            self.community_cards = server_state['community_cards']
            self.state = PokerGame.GameState(server_state['state'])
        except Exception as e:
            print(f"Failed to sync with server: {e}")

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

    def next_player(self):
        """Move to the next player who hasn't folded."""
        active_players = [p for p in self.players if not p.folded]
        if len(active_players) <= 1:
            self.round_complete = True
            return False

        original_player = self.current_player
        while True:
            self.current_player = (self.current_player + 1) % len(self.players)
            if not self.players[self.current_player].folded:
                break
            # If we've gone all the way around
            if self.current_player == original_player:
                self.round_complete = True
                break

        # Check if round is complete (we've reached the last raiser)
        if self.last_raiser and self.players[self.current_player] == self.last_raiser:
            self.round_complete = True

        return True

    def next_stage(self):
        """Progress to the next stage of the game if round is complete."""
        if not self.round_complete:
            return False

        active_players = [p for p in self.players if not p.folded]
        if len(active_players) <= 1:
            self.state = PokerGame.GameState.SHOWDOWN
            return True

        # Reset betting round
        self.last_raiser = None
        self.round_complete = False
        for player in self.players:
            self.bets[player] = 0

        # Move to next stage
        if self.state == PokerGame.GameState.PRE_FLOP:
            self.deal_community(3)  # Flop
            self.state = PokerGame.GameState.FLOP
        elif self.state == PokerGame.GameState.FLOP:
            self.deal_community(1)  # Turn
            self.state = PokerGame.GameState.TURN
        elif self.state == PokerGame.GameState.TURN:
            self.deal_community(1)  # River
            self.state = PokerGame.GameState.RIVER
        elif self.state == PokerGame.GameState.RIVER:
            self.state = PokerGame.GameState.SHOWDOWN

        # Reset current player to first active player after dealer
        self.current_player = (self.turn + 1) % len(self.players)
        while self.players[self.current_player].folded:
            self.current_player = (self.current_player + 1) % len(self.players)

        return True

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
        # display other players hands and scores who did not fold
        for player, score in scores.items():
            if player != winner:
                self.action_log.append(f"{player.name} had a score of {score} and folded.")

        self.pot = 0
        return winner

    def get_valid_actions(self, player):
        max_bet = max(self.bets.values())
        if self.bets[player] < max_bet:
            return ['call', 'raise', 'fold']
        else:
            return ['check', 'bet', 'fold']

    def get_player_decision(self, player):
        decision = [None]
        print(f"{player.name}, you have 60 seconds to decide.")
        try:
            print(f"Game State: {self.state.value}")
            print(f"Pot: {self.pot}")
            print(f"Blinds: Small Blind = {self.small_blind}, Big Blind = {self.big_blind}")
            print("Community Cards:", [Card.int_to_str(c) for c in self.community_cards])
            print(f"{player.name}'s balance: {player.balance}")
            print(f"{player.name}'s cards: ", [Card.int_to_str(c) for c in self.hands[player]])

            valid_actions = self.get_valid_actions(player)
            print(f"Valid actions: {', '.join(valid_actions)}")

            while True:
                user_input = input(f"{player.name}, enter your action ({', '.join(valid_actions)}): ").strip().lower()
                if user_input in valid_actions or any(user_input.startswith(v) for v in ['bet', 'raise']):
                    break
                print("Invalid input. Try again.")
            if user_input.startswith('bet') or user_input.startswith('raise'):
                parts = user_input.split()
                decision = (PokerGame.Moves[parts[0].upper()], int(parts[1])) if len(parts) == 2 and parts[
                    1].isdigit() else (PokerGame.Moves.FOLD, 0)
            else:
                decision = (PokerGame.Moves[user_input.upper()], 0)
        except Exception:
            decision = (PokerGame.Moves.FOLD, 0)
        return decision

    def play(self):
        while len([p for p in self.players if not p.folded]) > 1:
            player = self.players[self.turn % len(self.players)]
            if player.folded:
                self.turn += 1
                continue
            print(f"{player.name}'s turn.")
            # Send the current game state to the server and wait for the player's action
            game_state = self.gameStateJson()
            self.network.send(pickle.dumps(game_state))  # Send state to server

            # Get response from server
            response = pickle.loads(self.network.client.recv(4096))  # Receive player's action
            action, amount = response['action'], response['amount']  # Extract action and amount

            try:
                self.player_action(player, action, amount)
            except ValueError as e:
                print(e)
            self.turn += 1
            if self.turn % len(self.players) == 0:
                self.next_stage()
            if self.state == PokerGame.GameState.SHOWDOWN:
                break
            self.sync_with_server()

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
