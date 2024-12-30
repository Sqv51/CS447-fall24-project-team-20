import requests
import json

BASE_URL = 'http://127.0.0.1:5000/api'


def register_user(email, password):
    response = requests.post(f'{BASE_URL}/auth/register', json={
        'email': email,
        'password': password
    })
    return response.json()


def login_user(email, password):
    response = requests.post(f'{BASE_URL}/auth/login', json={
        'email': email,
        'password': password
    })
    return response.json()


def start_game(game_id, players):
    response = requests.post(f'{BASE_URL}/game/start', json={
        'game_id': game_id,
        'players': players
    })
    return response.json()


def join_game(game_id, player):
    response = requests.post(f'{BASE_URL}/game/join', json={
        'game_id': game_id,
        'player': player
    })
    return response.json()


def fetch_game_state(game_id):
    response = requests.get(f'{BASE_URL}/game/state', params={
        'game_id': game_id
    })
    return response.json()


def player_action(game_id, player, action, amount=0):
    response = requests.post(f'{BASE_URL}/game/action', json={
        'game_id': game_id,
        'player': player,
        'action': action,
        'amount': amount
    })
    return response.json()


if __name__ == '__main__':
    print("Testing Poker Game API...")

    # Register and login
    email = 'test@example.com'
    password = 'password123'
    print("Register:", register_user(email, password))
    login_response = login_user(email, password)
    print("Login:", login_response)

    # Start a game
    game_id = 'game1'
    players = ['Alice', 'Bob']
    print("Start Game:", start_game(game_id, players))

    # Join a game
    print("Join Game:", join_game(game_id, 'Charlie'))

    # Fetch game state
    print("Game State:", fetch_game_state(game_id))

    # Perform actions
    print("Action (Bet):", player_action(game_id, 'Alice', 'bet', 50))
    print("Action (Call):", player_action(game_id, 'Bob', 'call'))
    print("Action (Fold):", player_action(game_id, 'Charlie', 'fold'))

    # Fetch final state
    print("Final State:", fetch_game_state(game_id))
