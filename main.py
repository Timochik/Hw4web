import http.server
import socketserver
import threading
import json
from datetime import datetime
import socket
import logging

PORT = 3000
SOCKET_PORT = 5000

# Ініціалізуємо логування
logging.basicConfig(filename='error.html', level=logging.ERROR)

class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()

        # Process the data
        try:
            data = json.loads(post_data)
            # Перевірка на потенційно шкідливий код
            if 'username' in data and 'message' in data:
                # Збереження даних
                self.send_data_to_socket_server(data)
            else:
                raise ValueError("Missing username or message in data")
        except Exception as e:
            # Логування помилок
            logging.error(f"Error processing data: {e}")
            self.send_error(500, "Internal Server Error")

    def send_data_to_socket_server(self, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(json.dumps(data).encode(), ('localhost', SOCKET_PORT))
        except Exception as e:
            logging.error(f"Error sending data to socket server: {e}")

class SocketServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('localhost', SOCKET_PORT))
            print("Socket server is running on port", SOCKET_PORT)
            while True:
                data, addr = s.recvfrom(1024)
                try:
                    decoded_data = json.loads(data.decode())
                    self.handle_data(decoded_data)
                except Exception as e:
                    logging.error(f"Error handling data from socket: {e}")

    def handle_data(self, data):
        try:
            with open('storage/data.json', 'r+') as f:
                file_data = json.load(f)
                file_data[data['timestamp']] = {'username': data['username'], 'message': data['message']}
                f.seek(0)
                json.dump(file_data, f, indent=4)
                f.truncate()
                print("Data saved to storage/data.json")
        except Exception as e:
            logging.error(f"Error saving data to file: {e}")

def start_http_server():
    with socketserver.TCPServer(("", PORT), HTTPRequestHandler) as httpd:
        print("HTTP server is running on port", PORT)
        httpd.serve_forever()

if __name__ == "__main__":
    socket_server_thread = SocketServerThread()
    socket_server_thread.daemon = True
    socket_server_thread.start()

    http_server_thread = threading.Thread(target=start_http_server)
    http_server_thread.daemon = True
    http_server_thread.start()

    # Keep the main thread running
    while True:
        pass
