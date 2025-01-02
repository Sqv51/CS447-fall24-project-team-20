import firebase_admin
from firebase_admin import credentials, firestore, auth
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
import poker
from flask import Flask, request, jsonify, render_template

# Load environment variables
load_dotenv()

# Firebase Configuration
cred = credentials.Certificate("/Users/tugan_basaran/Desktop/Lessons/CS.447/Project/Server/cs447-team20-poker-firebase-adminsdk-7i9j4-4ee3cdbe68.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# JWT Secret Key
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)

# Global Variables
active_tables = {}



class Table:
    def __init__(self, table_id, players):
        self.table_id = table_id
        self.players = players
        self.game = None

    def start_game(self):
        self.game = poker.PokerGame(self.table_id, self.players, 1000)





# User Authentication Endpoints
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return jsonify({"user_id": "mock_id", "message": "User registered successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        user_data = {"email": email,
                     "password": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}
        if not bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            return jsonify({"error": "Invalid password."}), 401

        token = jwt.encode({'user_id': "mock_id", 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                           SECRET_KEY, algorithm='HS256')
        return jsonify({"user_id": "mock_id", "token": token, "message": "Login successful."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400





# API Endpoints

#Api endpoint to get info and current tables(games)
@app.route('/api/tables', methods=['GET'])
def get_tables():
    try:
        tables = db.collection('tables').get()
        tables_data = []
        for table in tables:
            tables_data.append(table.to_dict())
        return jsonify(tables_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400




@app.route('/api/game/start', methods=['POST'])
def start_game():
    try:
        data = request.json
        game_id = data['game_id']
        players = data['players']
        starting_chips = 1000  # Tournament-style chips
        if len(players) < 2 or len(players) > 9:
            return jsonify({"error": "Invalid number of players."}), 400

        game = poker.PokerGame(game_id, players, starting_chips)
        game.deal_hands()
        active_games[game_id] = game
        return jsonify({"message": "Game started.", "game_id": game_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/game/action', methods=['POST'])
def player_action():
    try:
        data = request.json
        game_id = data['game_id']
        player = data['player']
        action = data['action']
        amount = data.get('amount', 0)

        if game_id not in active_games:
            return jsonify({"error": "Game not found."}), 404

        game = active_games[game_id]
        if player not in game.players:
            return jsonify({"error": "Player not in game."}), 403

        if action == "bet":
            if amount < game.blind_level:
                return jsonify({"error": "Bet below blind level."}), 400
            game.bets[player] += amount
            game.pot += amount
        elif action == "fold":
            del game.players[player]
            if len(game.players) == 1:
                result = game.distribute_pot()
                return jsonify({
                                   "message": f"{result['winner']} wins the pot of {result['winnings']} with score {result['score']}."})
        elif action == "call":
            max_bet = max(game.bets.values())
            game.bets[player] = max_bet
            game.pot += max_bet
        elif action == "raise":
            game.bets[player] += amount
            game.pot += amount
        else:
            return jsonify({"error": "Invalid action."}), 400

        game.increment_blinds()  # Increment blinds after each round
        return jsonify({"message": "Action completed."})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)