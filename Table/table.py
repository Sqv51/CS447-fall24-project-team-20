#!/usr/bin/env python3

import socket
import pickle
import sys

SERVER_IP = "192.168.196.52"  # Change if different
SERVER_PORT = 23345


# In table.py - Modify the display logic
def display_game_state(state):
    """Pretty print the game state."""
    # Clear screen (works on both Windows and Unix-like systems)
    print("\033[H\033[J", end="")

    # Display header with game stage and pot
    print("=" * 60)
    print(f"{'Poker Game':^60}")
    print(f"{'Stage: ' + state['game_stage']:^60}")
    print("=" * 60)

    # Display community cards
    print("\nCommunity Cards:")
    if state['community_cards']:
        print(" ".join(state['community_cards']))
    else:
        print("No community cards yet")

    # Display pot and current bet
    print(f"\nPot: ${state['pot']}  Current Bet: ${state['current_bet']}")

    # Display player's information
    print("\nYour Information:")
    print(f"Name: {state['player_name']}")
    print(f"Balance: ${state['player_balance']}")
    print(f"Your Cards: {' '.join(state['player_cards'])}")
    print(f"Your Current Bet: ${state['player_bet']}")

    # Display other players
    print("\nOther Players:")
    for player in state['other_players']:
        status = "Folded" if player['folded'] else "Active"
        cards = "Folded" if player['folded'] else "🂠 🂠"
        print(f"{player['name']}: ${player['balance']} (Bet: ${player['bet']}) - {status} {cards}")

    # Display action log
    print("\nRecent Actions:")
    for action in state['action_log']:
        print(f"• {action}")

    # Display valid actions if it's player's turn
    if state['is_turn']:
        print("\nIt's your turn!")
        print("Valid actions:", ", ".join(state['valid_actions']))
    else:
        print("\nWaiting for other players...")

    print("\n" + "=" * 60)

def main():
    # Create a client socket and connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}\n")
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        sys.exit(1)

    # Initial server response (should contain {"status": "ok", "player_id": ...})
    try:
        response_data = client_socket.recv(4096)
        if response_data:
            response = pickle.loads(response_data)
            print("Server response:", response)
        else:
            print("No response received from server.")
            sys.exit(1)
    except Exception as e:
        print(f"Error receiving initial data from server: {e}")
        sys.exit(1)

    print("\nType 'help' for a list of commands.")
    print("Type 'exit' to disconnect.\n")

    while True:
        command = input("Enter command: ").strip().lower()

        if command == "exit":
            print("Exiting...")
            break

        if command == "help":
            print("""
    Available commands:
      get_state   - Refresh the game state
      play        - Make a move (when it's your turn)
      help        - Show this help message
      exit        - Close the connection and exit
    """)
            continue

        if command in ["get_state", "refresh", "r"]:
            msg = {"action": "get_state"}
            _send_data(client_socket, msg)
            state = _receive_data(client_socket)
            if state:
                display_game_state(state)
            continue

        if command in ["play", "p"]:
            msg = {"action": "get_state"}
            _send_data(client_socket, msg)
            state = _receive_data(client_socket)

            if not state['is_turn']:
                print("It's not your turn!")
                continue

            valid_actions = state['valid_actions']
            action = input(f"Action to perform ({', '.join(valid_actions)}): ").strip().lower()

            if action not in valid_actions:
                print("Invalid action. Please try again.")
                continue

            amount = 0
            if action in ["raise", "bet"]:
                try:
                    amount = int(input("Enter amount: ").strip())
                except ValueError:
                    print("Invalid amount. Please try again.")
                    continue

            msg = {
                "action": "player_action",
                "move": action,
                "amount": amount
            }
            _send_data(client_socket, msg)
            state = _receive_data(client_socket)
            if state:
                display_game_state(state)
            continue

        print("Unknown command. Type 'help' for a list of commands.")

    # Close the connection
    client_socket.close()


def _send_data(sock, data):
    """Pickle and send data to the server."""
    try:
        sock.sendall(pickle.dumps(data))
    except Exception as e:
        print(f"Error sending data to server: {e}")

def _receive_data(sock):
    """Receive data from the server and unpickle."""
    try:
        response_data = sock.recv(4096)
        if not response_data:
            print("No data received (connection may have closed).")
            return None
        return pickle.loads(response_data)
    except Exception as e:
        print(f"Error receiving/unpickling data: {e}")
        return None

def _receive_and_print(sock):
    """Receive data from the server, unpickle, and print."""
    try:
        response_data = sock.recv(4096)
        if not response_data:
            print("No data received (connection may have closed).")
            return

        response = pickle.loads(response_data)
        print("Server response:", response)
    except Exception as e:
        print(f"Error receiving/unpickling data: {e}")


if __name__ == "__main__":
    main()
