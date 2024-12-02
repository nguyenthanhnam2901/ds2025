import socket
import os
import threading

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
BUFFER_SIZE = 1024
SERVER_DIRECTORY = './open_listenfd'  

def handle_client(client_socket, client_address):
    print(f"Client {client_address} connected.")
    
    files = os.listdir(SERVER_DIRECTORY)
    file_list = "\n".join(files)
    client_socket.send(file_list.encode())
    
    while True:
        requested_file = client_socket.recv(BUFFER_SIZE).decode().strip()
        if requested_file.lower() == 'exit':
            print(f"Client {client_address} disconnected.")
            break
        
        file_path = os.path.join(SERVER_DIRECTORY, requested_file)
        if os.path.exists(file_path):
            client_socket.send("OK".encode())
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(BUFFER_SIZE):
                    client_socket.send(chunk)
            print(f"File '{requested_file}' sent to {client_address}.")
        else:
            client_socket.send("ERROR: File not found.".encode())
    
    client_socket.close()

def start_server():
    os.makedirs(SERVER_DIRECTORY, exist_ok=True)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")
    
    while True:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

if __name__ == "__main__":
    start_server()
