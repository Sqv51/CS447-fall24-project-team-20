import poker


# Global Variables
active_tables = {}
max_tables = 10



class Table:

    


    maxplayers = 9
    maxpsec = 3

    enum = {
    "waiting for players": 0,
    "game in progress": 1,
    "game over": 2
    }


    players = []
    spectators = []
    starting_chips = 10000
    def __init__(self, table_id, initial_player):
        self.table_id = table_id
        self.add_player(initial_player)
        self.spectators = []
        self.game = None
        self.status = Table.enum["waiting for players"]


    def get_table_info(self):
        return {"table_id": self.table_id, "players": self.players}

    def add_player(self, player):
        if len(self.players) < Table.maxplayers:
            self.players.append(player)
        else:
            raise ValueError("Table is full.")

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
        else:
            raise ValueError("Player not found.")

    def add_spec(self, spec):
        if len(self.spectators) < Table.maxplayers:
            self.spectators.append(spec)

    def remove_spec(self, spec):
        if spec in self.spectators:
            self.spectators.remove(spec)
        else:
            raise ValueError("Spectator not found.")

    def set_starting_chips(self, chips):
        self.starting_chips = chips

    def start_game(self):
        self.game = poker.PokerGame(self.table_id)



