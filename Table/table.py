#!/usr/bin/env python3

import socket
import pickle
import sys

SERVER_IP = "192.168.196.52"  # Change if different
SERVER_PORT = 4334

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

    # Main CLI loop
    while True:
        command = input("Enter command: ").strip().lower()

        if command == "exit":
            print("Exiting...")
            break

        if command == "help":
            print("""
Available commands:
  get_state
    - Retrieve the current game state from the server.
  player_action
    - Make a move. You will be prompted for the action and amount (if applicable).
  help
    - Show this help message.
  exit
    - Close the connection and exit.
""")
            continue

        if command == "get_state":
            # Create and send a request for the current game state
            msg = {
                "action": "get_state",
            }
            _send_data(client_socket, msg)
            _receive_and_print(client_socket)
            continue

        if command == "player_action":
            action = input("Action to perform (call, fold, raise, check, bet): ").strip().lower()
            amount = 0

            # For actions that require an amount, ask for it
            if action in ["raise", "bet"]:
                try:
                    amount = int(input("Enter amount: ").strip())
                except ValueError:
                    print("Invalid amount. Defaulting to 0.")
                    amount = 0

            # Create and send the player_action request
            msg = {
                "action": "player_action",
                "move": action,
                "amount": amount
            }
            _send_data(client_socket, msg)
            _receive_and_print(client_socket)
            continue

        # If none of the above commands
        print("Unknown command. Type 'help' for a list of commands.")

    # Close the connection
    client_socket.close()


def _send_data(sock, data):
    """Pickle and send data to the server."""
    try:
        sock.sendall(pickle.dumps(data))
    except Exception as e:
        print(f"Error sending data to server: {e}")


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
