#!/usr/bin/env python3

import socket
import pickle
import sys
import time
import threading
import os

SERVER_IP = "192.168.196.52"
SERVER_PORT = 23345


class PokerClient:
    def __init__(self):
        self.socket = None
        self.player_id = None
        self.current_state = None
        self.running = True
        self.last_display_time = 0
        self.auto_refresh = True
        self.refresh_interval = 5  # Increased to 5 seconds
        self.input_mode = False    # Flag to prevent refresh during input

    def auto_refresh_thread(self):
        while self.running:
            if self.auto_refresh and not self.input_mode:
                current_time = time.time()
                if current_time - self.last_display_time >= self.refresh_interval:
                    if self.refresh_state():
                        self.display_state()
                        self.last_display_time = current_time
            time.sleep(1)  # Reduced CPU usage


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

        # Display player's information with emoji
        print("\n👤 Your Information:")
        print(f"Name: {state['player_name']}")
        print(f"Balance: ${state['player_balance']}")
        print(f"Your Cards: {' '.join(state['player_cards'])}")
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
        self.input_mode = True  # Prevent refresh during play

        if not self.current_state['is_turn']:
            print("⚠️  It's not your turn!")
            print(f"Current turn: {self.current_state.get('current_player', 'Unknown')}")
            self.input_mode = False
            return

        valid_actions = self.current_state['valid_actions']
        print(f"Valid actions: {', '.join(valid_actions)}")
        action = input("Action: ").strip().lower()

        if action not in valid_actions:
            print("❌ Invalid action!")
            self.input_mode = False
            return

        amount = 0
        if action in ["raise", "bet"]:
            try:
                amount = int(input("Amount: $").strip())
            except ValueError:
                print("❌ Invalid amount!")
                self.input_mode = False
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

        self.input_mode = False  # Re-enable refresh after play

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
                    self.input_mode = True  # Prevent refresh during command input
                    command = input().strip().lower()
                    self.input_mode = False  # Re-enable refresh after command

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
      i           - Increase refresh interval (+1s)
      d           - Decrease refresh interval (-1s)
    """.format("ON" if self.auto_refresh else "OFF"))

                    elif command in ['r', 'refresh']:
                        if self.refresh_state():
                            self.display_state()

                    elif command in ['p', 'play']:
                        self.handle_play()

                    elif command == 'a':
                        self.auto_refresh = not self.auto_refresh
                        print(f"Auto-refresh: {'ON' if self.auto_refresh else 'OFF'}")

                    elif command == 'i':
                        self.refresh_interval += 1
                        print(f"Refresh interval: {self.refresh_interval}s")

                    elif command == 'd':
                        if self.refresh_interval > 1:
                            self.refresh_interval -= 1
                            print(f"Refresh interval: {self.refresh_interval}s")

                    else:
                        print("Unknown command. Type 'h' for help.")

                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break

                except Exception as e:
                    print(f"Error: {e}")
                    self.input_mode = False

            self.running = False
            self.socket.close()

    def display_state(self):
        if not self.current_state or self.input_mode:
            return


if __name__ == "__main__":
    client = PokerClient()
    client.run()