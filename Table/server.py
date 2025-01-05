import socket
from _thread import start_new_thread
import pickle
from poker import PokerGame, Player

# Server configuration
server = "192.168.196.52"
port = 4334

# Create server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(5)  # Allow up to 5 connections
print("Waiting for connections...")

# Game data
games = {}  # game_id -> PokerGame
id_count = 0  # Track total player connections
MAX_PLAYERS = 5


def threaded_client(conn, player_id, game_id):
    global id_count

    try:
        conn.sendall(pickle.dumps({"status": "ok", "player_id": player_id}))

        while True:
            try:
                # Receive data from client
                data = pickle.loads(conn.recv(4096))
                if not data:
                    print(f"Player {player_id} disconnected.")
                    break

                # Process client request
                if game_id in games:
                    game = games[game_id]

                    if data["action"] == "get_state":
                        # Send game state
                        conn.sendall(pickle.dumps(game.gameStateJson()))

                    elif data["action"] == "player_action":
                        # Handle player actions
                        player = game.players[player_id]
                        action = data["move"]
                        amount = data.get("amount", 0)
                        game.player_action(player, game.Moves[action.upper()], amount)
                        game.next_stage()

                        # Send updated game state
                        conn.sendall(pickle.dumps(game.gameStateJson()))

                    else:
                        conn.sendall(pickle.dumps({"error": "Invalid request"}))
                else:
                    conn.sendall(pickle.dumps({"error": "Game not found"}))

            except Exception as e:
                print(f"Error with player {player_id}: {e}")
                break

    except Exception as e:
        print(f"Thread error: {e}")

    print(f"Player {player_id} disconnected.")
    id_count -= 1
    conn.close()


while True:
    # Accept new connections
    conn, addr = s.accept()
    print("Connected to:", addr)

    id_count += 1
    player_id = (id_count - 1) % MAX_PLAYERS  # Cycle through player IDs
    game_id = (id_count - 1) // MAX_PLAYERS  # Determine game ID based on player count

    # Create a new game if this is the first player
    if game_id not in games:
        players = [Player(f"Player {i+1}", 1000) for i in range(MAX_PLAYERS)]
        games[game_id] = PokerGame(players)
        print(f"Creating new game {game_id}...")
    else:
        print(f"Joining game {game_id}...")

    # Start client thread
    start_new_thread(threaded_client, (conn, player_id, game_id))
