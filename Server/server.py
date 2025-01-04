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


# Countdown function
def start_countdown(room):
    countdown = 120  # 120 seconds countdown
    while countdown > 0:
        socketio.emit('message', {'msg': f"Game starting in {countdown} seconds."}, room=room)
        time.sleep(1)
        print(countdown)
        countdown -= 1
    start_poker_game(room)


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
    username = data['username']
    join_room(room)

    # Initialize player status if not already present
    if username not in player_status:
        player_status[username] = {'room': room, 'ready': False}

    # Notify about join event and send player statuses
    emit('message', {'msg': f"{username} has joined the room."}, room=room)
    emit('player_status', player_status, room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    emit('message', {'msg': f"{data['username']} has left the room."}, room=room)



@socketio.on('disconnect')
def handle_disconnect():
    emit('message', {'msg': 'A player has disconnected.'}, broadcast=True)


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
