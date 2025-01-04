import firebase_admin
from firebase_admin import credentials, firestore, auth
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from enum import Enum
import threading
import time

# Load environment variables
load_dotenv()

# Firebase Configuration
cred = credentials.Certificate("Server/cs447-team20-poker-firebase-adminsdk-7i9j4-4ee3cdbe68.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# JWT Secret Key
SECRET_KEY = os.getenv('SECRET_KEY')

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Player slots list of player objects and their state
player_slots = []
ready_players = []

# Countdown function
def start_countdown(room):
    countdown = 120  # 120 seconds countdown
    while countdown > 0:
        socketio.emit('message', {'msg': f"Game starting in {countdown} seconds."}, room=room)
        time.sleep(1)
        countdown -= 1
    start_poker_game(room)

# Start poker game function
def start_poker_game(room):
    global ready_players
    players = [Player(player['username'], 1000) for player in ready_players if player['room'] == room]
    game = PokerGame(players)
    socketio.emit('game_update', {'msg': 'Game started!', 'action_log': game.action_log}, room=room)
    ready_players = [player for player in ready_players if player['room'] != room]

@socketio.on('ready')
def handle_ready(data):
    room = data['room']
    username = data['username']
    ready_players.append({'username': username, 'room': room})
    emit('message', {'msg': f"{username} is ready."}, room=room)

    if len([player for player in ready_players if player['room'] == room]) >= 2:
        threading.Thread(target=start_countdown, args=(room,)).start()

# Enum server state for the game
class ServerState(Enum):
    WAITING = 'waiting'
    RUNNING = 'running'
    FINISHED = 'finished'

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        email = data['email']
        password = data['password']
        user = auth.create_user(email=email, password=password)
        
        # Save user info to Firestore
        db.collection('users').document(user.uid).set({
            'email': email,
            'password': password  # It's recommended to hash the password
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

# WebSocket Events
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'msg': f"{data['username']} has joined the room."}, room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    emit('message', {'msg': f"{data['username']} has left the room."}, room=room)

@socketio.on('action')
def handle_action(data):
    room = data['room']
    action = data['action']
    amount = data.get('amount', 0)

    # Broadcast action to all clients in the room
    emit('game_update', {'action': action, 'amount': amount}, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    emit('message', {'msg': 'A player has disconnected.'}, broadcast=True)

# Game Actions Endpoint (Fallback for HTTP)
@app.route('/api/game/action', methods=['POST'])
def game_action():
    try:
        data = request.json
        game_id = data['game_id']
        player = data['player']
        action = data['action']
        amount = data.get('amount', 0)

        # Example: Update actions in the database
        if action == "bet":
            if amount < 10:  # Replace 10 with your blind level logic
                return jsonify({"error": "Bet below blind level."}), 400
        elif action == "fold":
            # Handle fold logic
            pass

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
    socketio.run(app, host='192.168.196.52', port=5000, debug=True)
