import socket

SERVER_HOST = '0.0.0.0' 
SERVER_PORT = 5001       
BUFFER_SIZE = 1024       
OUTPUT_FILE = "received_example.jpg"  

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print(f"[*] Listening on {SERVER_HOST}:{SERVER_PORT}...")

    client_socket, client_address = server_socket.accept()
    print(f"[+] Accepted connection from {client_address}")

    with open(OUTPUT_FILE, "wb") as f:
        print("[*] Receiving file...")
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)

    print(f"[+] File received and saved as {OUTPUT_FILE}")

    client_socket.close()
    server_socket.close()
    print("[*] Connection closed.")

if __name__ == "__main__":
    start_server()
