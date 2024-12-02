import socket
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
BUFFER_SIZE = 1024
CLIENT_DIRECTORY = './open_clientfd'

def start_client():
    os.makedirs(CLIENT_DIRECTORY, exist_ok=True)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")
    
    file_list = client_socket.recv(BUFFER_SIZE).decode()
    print("Available files:\n" + file_list)
    
    while True:
        requested_file = input("Enter the file name to download (or 'exit' to quit): ").strip()
        client_socket.send(requested_file.encode())
        if requested_file.lower() == 'exit':
            print("Exiting...")
            break
        
        response = client_socket.recv(BUFFER_SIZE).decode()
        if response == "OK":
            file_path = os.path.join(CLIENT_DIRECTORY, requested_file)
            with open(file_path, 'wb') as f:
                print(f"Downloading '{requested_file}'...")
                while chunk := client_socket.recv(BUFFER_SIZE):
                    f.write(chunk)
                    if len(chunk) < BUFFER_SIZE: 
                        break
            print(f"File '{requested_file}' downloaded successfully.")
        else:
            print(response) 
    
    client_socket.close()

if __name__ == "__main__":
    start_client()
