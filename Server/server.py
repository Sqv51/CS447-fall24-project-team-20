import firebase_admin
from firebase_admin import credentials, firestore, auth
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
import table
from flask import Flask, request, jsonify, render_template

# Load environment variables
load_dotenv()

# Firebase Configuration
cred = credentials.Certificate("Server/cs447-team20-poker-firebase-adminsdk-7i9j4-4ee3cdbe68.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# JWT Secret Key
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)



@app.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        user = auth.create_user(email=email, password=password)
        
        # Kullanıcı bilgilerini Firestore'a kaydet
        db.collection('users').document(user.uid).set({
            'email': email,
            'password': password  # Şifreyi hashleyerek saklamanız önerilir
        })
        
        return jsonify({"user_id": user.uid, "message": "User registered successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        user = auth.get_user_by_email(email)
        
        # Firebase Authentication'da şifre doğrulama işlemi yoktur, bu yüzden kendi doğrulama yöntemimizi kullanıyoruz
        user_data = db.collection('users').document(user.uid).get().to_dict()
        if user_data['password'] != password:
            return jsonify({"error": "Invalid password."}), 401

        token = jwt.encode({'user_id': user.uid, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                           SECRET_KEY, algorithm='HS256')
        return jsonify({"user_id": user.uid, "token": token, "message": "Login successful."})
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

        game = poker.PokerGame(game_id)
        game.deal_hands()
        active_tables[game_id] = game
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

        if game_id not in active_tables:
            return jsonify({"error": "Game not found."}), 404

        game = active_tables[game_id]
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
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/main_page')
def main_page():
    return render_template('main_page.html')


if __name__ == '__main__':
    #handle active tables and games one by one
    app.run(debug=True, port=8080)
