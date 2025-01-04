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

# Enum server state for the game
class ServerState(Enum):
    WAITING = 'waiting'
    RUNNING = 'running'
    FINISHED = 'finished'

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

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# WebSocket Events
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'msg': f"{data['username']} has joined the room."}, room=room)

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

# Run the WebSocket Server
if __name__ == '__main__':
    socketio.run(app, debug=True)
