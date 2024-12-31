import firebase_admin
from firebase_admin import credentials, firestore, auth
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
from pokerkit import NoLimitTexasHoldem, Automation, Mode, Hand
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()

# Firebase Configuration
cred = credentials.Certificate("cs447-team20-poker-firebase-adminsdk-7i9j4-4ee3cdbe68.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# JWT Secret Key
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)

# Global Variables
active_games = {}  # Temporary storage for games

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
        user_data = {"email": email, "password": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}
        if not bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            return jsonify({"error": "Invalid password."}), 401

        token = jwt.encode({'user_id': "mock_id", 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
        return jsonify({"user_id": "mock_id", "token": token, "message": "Login successful."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    try:
        token = request.json['token']
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({"user_id": decoded_token['user_id']})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token."}), 401


# Poker Game Class


from pokerkit import Automation, NoLimitTexasHoldem, Mode

from pokerkit import Automation, NoLimitTexasHoldem, Mode, Card

class PokerGame:
    def __init__(self, game_id, players):
        self.game_id = game_id
        self.players = players

        # Initialize the state
        self.state = NoLimitTexasHoldem.create_state(
            automations=(
                Automation.ANTE_POSTING,
                Automation.BET_COLLECTION,
                Automation.BLIND_OR_STRADDLE_POSTING,
                Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
                Automation.HAND_KILLING,
                Automation.CHIPS_PUSHING,
                Automation.CHIPS_PULLING,
            ),
            ante_trimming_status=False,
            raw_antes={-1: 0},  # No antes
            raw_blinds_or_straddles=(10, 20),  # Small blind, big blind
            min_bet=20,  # Minimum bet
            raw_starting_stacks=(1000,) * len(players),  # Initial stacks
            player_count=len(players),  # Number of players
            mode=Mode.TOURNAMENT,  # Tournament mode
        )

        # Initialize game variables
        self.hands = {}  # Store player hands
        self.current_turn = 0
        self.bets = {player: 0 for player in players}

        # Deal hands to players
        self.deal_hands()

    def deal_hands(self):
        """Deal 2 random cards to each player."""
        used_cards = set()  # Track used cards to avoid duplicates

        for i, player in enumerate(self.players):
            cards = []
            while len(cards) < 2:
                card = Card.random()
                if card not in used_cards:  # Ensure no duplicates
                    cards.append(card)
                    used_cards.add(card)
            self.hands[player] = self.state.deal_hole(cards)


# API Endpoints
@app.route('/api/game/start', methods=['POST'])
def start_game():
    try:
        data = request.json
        print(f"Received data: {data}")  # Log received data

        game_id = data['game_id']
        players = data['players']

        # Log game creation
        print(f"Initializing game with ID: {game_id} and players: {players}")

        # Create PokerGame instance
        game = PokerGame(game_id, players)
        game.deal_hands()
        active_games[game_id] = game

        return jsonify({"message": "Game started.", "game_id": game_id})

    except Exception as e:
        print(f"Error: {str(e)}")  # Log error details
        return jsonify({"error": str(e)}), 400


@app.route('/api/game/join', methods=['POST'])
def join_game():
    try:
        data = request.json
        game_id = data['game_id']
        player = data['player']
        if game_id in active_games:
            game = active_games[game_id]
            if player not in game.players:
                game.players.append(player)
                game.hands[player] = Hand(game.deck.draw(2))
                return jsonify({"message": "Player joined.", "game_id": game_id})
            else:
                return jsonify({"error": "Player already in the game."}), 400
        return jsonify({"error": "Game not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/game/state', methods=['GET'])
def fetch_game_state():
    try:
        game_id = request.args.get('game_id')
        if game_id in active_games:
            game = active_games[game_id]
            state = {
                "players": game.players,
                "pot": game.pot,
                "community_cards": [str(card) for card in game.community_cards],
                "bets": game.bets,
                "current_turn": game.players[game.current_turn]
            }
            return jsonify(state)
        return jsonify({"error": "Game not found."}), 404
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
        if player != game.players[game.current_turn]:
            return jsonify({"error": "Not your turn."}), 403

        if action == "bet":
            game.bets[player] += amount
            game.pot += amount
        elif action == "fold":
            game.players.remove(player)
            if len(game.players) == 1:
                result = game.distribute_pot()
                return jsonify({"message": f"{result['winner']} wins the pot of {result['winnings']} with score {result['score']}."})
        elif action == "call":
            max_bet = max(game.bets.values())
            game.bets[player] = max_bet
            game.pot += max_bet
        elif action == "raise":
            game.bets[player] += amount
            game.pot += amount
        else:
            return jsonify({"error": "Invalid action."}), 400

        # Move to the next turn
        game.next_turn()
        return jsonify({"message": "Action completed."})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
