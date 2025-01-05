import socket
from _thread import start_new_thread
import pickle
from poker import PokerGame, Player  # Import PokerGame and Player classes

server = "192.168.196.52"
port = 4351

# Create server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(5) #up to 5 connections can be queued
print("Waiting for connections...")

games = {}  # Dictionary to store games (game_id -> PokerGame)
id_count = 0  # Unique game ID counter


def threaded_client(conn, player_id, game_id):
    global id_count
    conn.sendall(pickle.dumps({"status": "ok", "player_id": player_id}))


    while True:
        try:
            # Receive data from client
            data = pickle.loads(conn.recv(4096))

            # If client disconnects
            if not data:
                print("Disconnected")
                break

            # Process client request
            if game_id in games:
                game = games[game_id]

                if data["action"] == "get_state":
                    # Send the current state of the game
                    conn.sendall(pickle.dumps(game.gameStateJson()))

                elif data["action"] == "player_action":
                    # Perform the requested action
                    player = game.players[player_id]
                    action = data["move"]
                    amount = data.get("amount", 0)  # Default 0 if not provided
                    game.player_action(player, game.Moves[action.upper()], amount)

                    # Advance the game stage if needed
                    game.next_stage()

                    # Send updated game state
                    conn.sendall(pickle.dumps(game.gameStateJson()))

                else:
                    # Invalid request
                    conn.sendall(pickle.dumps({"error": "Invalid request"}))
            else:
                conn.sendall(pickle.dumps({"error": "Game not found"}))

        except Exception as e:
            print(e)
            break

    print("Lost connection")
    try:
        if len(game.players) == 1:
            print("Player disconnected, waiting for reconnection...")


    except KeyError:
        pass
    id_count -= 1
    conn.close()


while True:
    # Accept new connections
    conn, addr = s.accept()
    print("Connected to:", addr)

    id_count += 1
    player_id = len(games[game_id].players)


    # Create a new game if the first player connects
    if id_count % 2 == 1:
        game_id = (id_count - 1) // 2
        players = [Player("Player 1", 1000), Player("Player 2", 1000)]
        games[game_id] = PokerGame(players)
        print(f"Creating new game {game_id}...")

    else:
        game_id = (id_count - 1) // 2
        print(f"Joining game {game_id}...")

    # Start a new thread for the client
    start_new_thread(threaded_client, (conn, player_id, game_id))
