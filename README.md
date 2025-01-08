# Texas Hold'em Poker Game

## Overview
This project implements a multiplayer Texas Hold'em Poker game using Python. The system includes a server-client architecture where players can connect, play, and interact in real time.

## Features
- Multiplayer support for 2 players.
- Real-time gameplay using socket programming.
- Poker game logic including betting rounds, community cards, and winner evaluation.
- Text-based and graphical user interfaces.
- Auto-refreshing game state and synchronized updates.
- Support for common poker actions such as check, bet, raise, call, fold, and all-in.
- Evaluates hands using the `treys` library for ranking poker hands.

## Project Structure
```
.
├── server.py           # Handles server-side game logic and client connections.
├── textClient.py      # Command-line interface client for connecting to the server.
├── gameClient.py      # Graphical user interface client built with Pygame.
├── poker.py           # Core poker game logic, including player actions and hand evaluation.
├── network.py         # Networking utility to handle client-server communication.
```

### server.py
- Manages incoming connections and assigns players to games.
- Handles client requests and synchronizes game states.
- Implements multi-threading to support simultaneous client interactions.

### textClient.py
- Command-line interface client for users to join and play the game.
- Displays game information and allows players to make moves via text commands.

### gameClient.py
- Graphical user interface using Pygame.
- Displays poker table, community cards, and player avatars.
- Provides buttons for actions like bet, raise, fold, etc.

### poker.py
- Core game logic for poker rounds, player actions, and evaluating hand strengths.
- Implements rules for betting rounds (pre-flop, flop, turn, river) and showdown.

### network.py
- Simplifies client-server communication with sockets.
- Handles sending and receiving serialized data.

## Requirements
- Python 3.8 or later
- Libraries:
  - `pygame`
  - `treys`

Install dependencies using pip:
```
pip install pygame treys
```

## Setup and Usage
1. **Start the Server:**
   ```
   python server.py
   ```

2. **Run the Client:**
   Text-based client:
   ```
   python textClient.py
   ```

   Graphical client:
   ```
   python gameClient.py
   ```

3. **Gameplay:**
   - Players can join the server until 2 players are connected.
   - The game automatically starts once both players are ready.
   - Players take turns based on the rules of Texas Hold'em.

## Controls (Text Client)
- `p`: Play an action (bet, raise, call, etc.).
- `r`: Refresh the game state.
- `h`: Display help.
- `q`: Quit the game.

## Controls (Graphical Client)
- Use on-screen buttons to perform actions like bet, raise, fold, etc.
- Automatically updates game state.

## Game Rules
The game follows standard Texas Hold'em rules:
1. Players are dealt 2 hole cards each.
2. Community cards are revealed in stages (Flop, Turn, River).
3. Players take turns betting, calling, raising, or folding.
4. The winner is determined based on the best 5-card hand.

## Network Configuration
- Default server IP: `192.168.196.52`
- Default port: `23345`
- Modify `server` and `port` variables in `server.py` and `network.py` if needed.

## Notes
- This project is intended for educational purposes.
- The server supports only 2 players at a time by default, but this can be adjusted in the code by modifying the `MAX_PLAYERS` variable in `server.py`.
- Ensure network settings allow connections to the specified IP and port.

## Authors
- Course Project Team

## License
MIT License.

