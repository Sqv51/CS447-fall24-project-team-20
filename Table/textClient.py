#!/usr/bin/env python3

import socket
import pickle
import sys
import time
import threading
import os
import treys

SERVER_IP = "192.168.196.52"
SERVER_PORT = 23345


def calculateHandStrength(player_cards, community_cards):
    evaluator = treys.Evaluator()
    if len(player_cards) + len(community_cards) >= 5:
        score = evaluator.evaluate(player_cards, community_cards)
        strength = evaluator.get_rank_class(score)
        return strength
    else:
        return "Not enough cards to evaluate"


class PokerClient:
    def __init__(self):
        self.socket = None
        self.player_id = None
        self.current_state = None
        self.running = True
        self.last_display_time = 0
        self.auto_refresh = True

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((SERVER_IP, SERVER_PORT))
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}\n")

            # Get initial response with player_id
            response = self._receive_data()
            if response and "player_id" in response:
                self.player_id = response["player_id"]
                print(f"You are Player {self.player_id + 1}")
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False

    def handle_disconnect(self):
        print("Lost connection to server")
        self.running = False
        self.socket.close()
    def _send_data(self, data):
        try:
            self.socket.sendall(pickle.dumps(data))
        except Exception as e:
            print(f"Error sending data: {e}")
            self.running = False

    def _receive_data(self):
        try:
            response_data = self.socket.recv(4096)
            if not response_data:
                print("Server connection closed.")
                self.running = False
                return None
            return pickle.loads(response_data)
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.running = False
            return None

    def refresh_state(self):
        self._send_data({"action": "get_state"})
        state = self._receive_data()
        if state:
            self.current_state = state
            return True
        return False

    def auto_refresh_thread(self):
        while self.running:
            if self.auto_refresh:
                current_time = time.time()
                if current_time - self.last_display_time >= 2:  # Refresh every 2 seconds
                    if self.refresh_state():
                        self.display_state()
                        self.last_display_time = current_time
            time.sleep(0.5)

    def display_state(self):
        if not self.current_state:
            return

        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')

        state = self.current_state

        # Display header
        print("=" * 60)
        print(f"{'Poker Game - Player ' + str(self.player_id + 1):^60}")
        print(f"{'Stage: ' + state['game_stage']:^60}")
        print("=" * 60)

        # Display community cards
        print("\n🎴 Community Cards:")
        if state['community_cards']:
            print(" ".join(state['community_cards']))
        else:
            print("No community cards yet")

        # Display pot and current bet
        print(f"\n💰 Pot: ${state['pot']}  Current Bet: ${state['current_bet']}")


        print("\n👤 Your Information:")
        print(f"Name: {state['player_name']}")
        print(f"Balance: ${state['player_balance']}")
        print(f"Your Cards: {' '.join(state['player_cards'])}")
        #use treys to get hand strength
        handStrength = calculateHandStrength(state['player_cards'], state['community_cards'])
        print(f"Your Hand Strength: {handStrength}")
        print(f"Your Current Bet: ${state['player_bet']}")

        # Display other players
        print("\n👥 Other Players:")
        for player in state['other_players']:
            status = "🚫 Folded" if player['folded'] else "✅ Active"
            cards = "Folded" if player['folded'] else "🂠 🂠"
            print(f"{player['name']}: ${player['balance']} (Bet: ${player['bet']}) - {status} {cards}")

        # Display action log
        print("\n📜 Recent Actions:")
        for action in state['action_log']:
            print(f"• {action}")

        # Display valid actions if it's player's turn
        if state['is_turn']:
            print("\n🎮 It's your turn!")
            print("Valid actions:", ", ".join(state['valid_actions']))
        else:
            print("\n⏳ Waiting for other players...")

        print("\nCommands: [p]lay, [r]efresh, [h]elp, [q]uit")
        print("=" * 60)

    def handle_play(self):
        if not self.current_state['is_turn']:
            print("⚠️  It's not your turn!")
            return

        valid_actions = self.current_state['valid_actions']
        print(f"Valid actions: {', '.join(valid_actions)}")
        action = input("Action: ").strip().lower()

        if action not in valid_actions:
            print("❌ Invalid action!")
            return

        amount = 0
        if action in ["raise", "bet"]:
            try:
                amount = int(input("Amount: $").strip())
            except ValueError:
                print("❌ Invalid amount!")
                return

        self._send_data({
            "action": "player_action",
            "move": action,
            "amount": amount
        })

        state = self._receive_data()
        if state:
            self.current_state = state
            self.display_state()

    def run(self):
        if not self.connect():
            return

        # Start auto-refresh thread
        refresh_thread = threading.Thread(target=self.auto_refresh_thread)
        refresh_thread.daemon = True
        refresh_thread.start()

        print("\nType 'h' for help\n")

        while self.running:
            try:
                command = input().strip().lower()

                if command in ['q', 'quit', 'exit']:
                    print("👋 Goodbye!")
                    break

                elif command in ['h', 'help']:
                    print("""
Commands:
  p, play     - Make a move (when it's your turn)
  r, refresh  - Manually refresh the game state
  h, help     - Show this help message
  q, quit     - Exit the game
  a           - Toggle auto-refresh (currently: {})
""".format("ON" if self.auto_refresh else "OFF"))

                elif command in ['r', 'refresh']:
                    if self.refresh_state():
                        self.display_state()

                elif command in ['p', 'play']:
                    self.handle_play()

                elif command == 'a':
                    self.auto_refresh = not self.auto_refresh
                    print(f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'}")

                else:
                    print("Unknown command. Type 'h' for help.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

            except Exception as e:
                print(f"Error: {e}")

        self.running = False
        self.socket.close()


if __name__ == "__main__":
    client = PokerClient()
    client.run()