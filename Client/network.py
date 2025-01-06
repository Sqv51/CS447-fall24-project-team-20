import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(15)  # Bağlantı öncesi zaman aşımı
        self.server = "192.168.196.52"  # Sunucu IP
        # Örneğin localhost:
        # self.server = "127.0.0.1"
        self.port = 23345
        self.addr = (self.server, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        try:
            self.client.connect(self.addr)
            print("Connected to server!")

            # Sunucudan ilk yanıt
            response = pickle.loads(self.client.recv(2048))
            if response.get("status") != "ok":
                raise ConnectionError("Invalid server response")

            return response.get("player_id")
        except socket.timeout:
            print("Server did not respond in time.")
            return None
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def send(self, data):
        """Pickle’lanmış veriyi sunucuya gönderir ve yanıtı döndürür."""
        try:
            self.client.send(data)
            return pickle.loads(self.client.recv(8192))
        except socket.error as e:
            print(f"Socket error: {e}")
            return None