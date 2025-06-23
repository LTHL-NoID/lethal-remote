import socket
from pynput.keyboard import Controller, Key

DEFAULT_PORT = 13376

def resolve_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
            temp_socket.connect(("8.8.8.8", 80))
            return temp_socket.getsockname()[0]
    except Exception as e:
        print(f"Error: Unable to determine local IP address: {e}")
        return None
    
# Resolve and validate local IP
LOCAL_IP = resolve_address()
if LOCAL_IP is None:
    exit(1)
print(f"Listening on {LOCAL_IP}:{DEFAULT_PORT}\n")

# Setup server socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow quick restarts
    s.bind((LOCAL_IP, DEFAULT_PORT))
    s.listen(1)

    while True:
        print("Waiting for connection...\n")
        conn, addr = s.accept()
        print(f"Recieved from: {addr[0]}:{addr[1]}")

        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"MSG> {data.decode(errors='ignore')}")  # Clean console output
                keyboard = Controller()
                keyboard.press(Key.f9) # key binds for press and release
                keyboard.release(Key.f9) # key binds for press and release

        print("Connection closed.\n")
