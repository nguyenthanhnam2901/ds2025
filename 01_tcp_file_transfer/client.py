import socket

SERVER_HOST = '127.0.0.1'  
SERVER_PORT = 5001       
BUFFER_SIZE = 1024        
INPUT_FILE = "example.jpg" 

def send_file():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"[*] Connected to {SERVER_HOST}:{SERVER_PORT}")

    with open(INPUT_FILE, "rb") as f:
        print(f"[*] Sending {INPUT_FILE}...")
        while (data := f.read(BUFFER_SIZE)):
            client_socket.sendall(data)

    print("[+] File sent successfully.")

    client_socket.close()
    print("[*] Connection closed.")

if __name__ == "__main__":
    send_file()
