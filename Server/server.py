import firebase_admin
from firebase_admin import credentials, firestore, auth
import bcrypt
import jwt
import datetime
from pokerkit import Deck, Hand, calculate_hand_strength
from flask import Flask, request, jsonify

# Firebase Bağlantısı (Yapılandırma Sonraya Atlandı)
cred = credentials.Certificate("cs447-team20-poker-firebase-adminsdk-7i9j4-4ee3cdbe68.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# JWT Secret Key
SECRET_KEY = 'your_secret_key'

app = Flask(__name__)

# Kullanıcı Kaydı
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

# Kullanıcı Girişi
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

# JWT Token Doğrulama
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

# Oyun Mantığı
class PokerGame:
    def __init__(self, players):
        self.deck = Deck()
        self.players = players
        self.pot = 0
        self.community_cards = []
        self.hands = {}
        self.current_turn = 0

    def deal_hands(self):
        self.deck.shuffle()
        for player in self.players:
            self.hands[player] = Hand(self.deck.draw(2))
        return self.hands

    def deal_community_cards(self, count):
        for _ in range(count):
            self.community_cards.append(self.deck.draw(1)[0])
        return self.community_cards

    def evaluate_hands(self):
        scores = {}
        for player, hand in self.hands.items():
            # Combine hole cards and community cards
            combined_cards = hand.cards + self.community_cards
            # Calculate hand strength
            scores[player] = calculate_hand_strength(combined_cards)
        return scores


    def next_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.players)
        return self.players[self.current_turn]

if __name__ == '__main__':
    app.run(debug=True)
