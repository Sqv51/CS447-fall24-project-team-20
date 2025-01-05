import socket
import pickle


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(15)  # Set timeout before attempting to connect
        self.server = "192.168.196.52"
        #localhost
        #self.server = "127.0.0.1"
        self.port = 43513
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            # Attempt to connect
            self.client.connect(self.addr)
            print("Connected to server!")

            # Receive initial response
            response = pickle.loads(self.client.recv(2048))
            if response.get("status") != "ok":  # Check for valid server response
                raise ConnectionError("Invalid server response")

            return response.get("player_id")  # Return player ID
        except socket.timeout:
            print("Server did not respond in time.")
            return None
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def send(self, data):
        try:
            # Send data without encoding (already pickled)
            self.client.send(data)

            # Receive and return response
            return pickle.loads(self.client.recv(8192))  # Increased buffer size to 8192
        except socket.error as e:
            print(f"Socket error: {e}")
            return None
