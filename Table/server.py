import socket
from _thread import start_new_thread
import pickle
from poker import PokerGame, Player

# Server configuration
server = "192.168.196.52"
port = 23345

# Create server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(2)  # Allow up to 2
print("Waiting for connections...")

# Game data
games = {}  # game_id -> PokerGame
id_count = 0  # Track total player connections
MAX_PLAYERS = 2


def threaded_client(conn, player_id, game_id):
    global id_count

    try:
        conn.sendall(pickle.dumps({"status": "ok", "player_id": player_id}))

        while True:
            try:
                data = pickle.loads(conn.recv(4096))
                if not data:
                    print(f"Player {player_id} disconnected.")
                    break

                if game_id in games:
                    game = games[game_id]

                    if data["action"] == "get_state":
                        player_state = game.get_player_state(player_id)
                        conn.sendall(pickle.dumps(player_state))

                    elif data["action"] == "player_action":
                        if game.current_player == player_id:
                            player = game.players[player_id]
                            action = data["move"]
                            amount = data.get("amount", 0)

                            # Process the action
                            action_successful = game.player_action(player, game.Moves[action.upper()], amount)

                            # Check if we should move to next stage
                            if action_successful and game.round_complete:
                                game.next_stage()

                            # Check for showdown
                            if game.state == game.GameState.SHOWDOWN:
                                game.get_winner()
                                # Start new hand here if desired

                        # Send updated state
                        player_state = game.get_player_state(player_id)
                        conn.sendall(pickle.dumps(player_state))

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
