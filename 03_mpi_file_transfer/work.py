from mpi4py import MPI
import base64
import os

SERVER_DIRECTORY = "./open_listenfd"
CLIENT_DIRECTORY = "./open_clientfd"

def send_file(filename, comm, dest_rank):
    try:
        file_path = os.path.join(SERVER_DIRECTORY, filename)
        if not os.path.exists(file_path):
            print(f"File '{filename}' does not exist in the server directory.")
            comm.send("ERROR: File not found.", dest=dest_rank, tag=0)
            return False

        with open(file_path, "rb") as f:
            file_data = f.read()
            encoded_data = base64.b64encode(file_data).decode('utf-8')

        # Notify the client the file is available
        comm.send("OK", dest=dest_rank, tag=0)

        # Send filename first, then the data
        comm.send(filename, dest=dest_rank, tag=1)
        comm.send(encoded_data, dest=dest_rank, tag=2)
        print(f"File '{filename}' sent successfully.")
        return True
    except Exception as e:
        print(f"Error sending file: {e}")
        return False

def receive_file(comm, source_rank):
    try:
        # Check if file is available
        response = comm.recv(source=source_rank, tag=0)
        if response != "OK":
            print(response)
            return False

        # Receive filename and data
        filename = comm.recv(source=source_rank, tag=1)
        encoded_data = comm.recv(source=source_rank, tag=2)

        # Create client directory if it doesn't exist
        os.makedirs(CLIENT_DIRECTORY, exist_ok=True)
        save_path = os.path.join(CLIENT_DIRECTORY, filename)

        with open(save_path, "wb") as f:
            f.write(base64.b64decode(encoded_data))
        print(f"File '{filename}' received successfully and saved to '{CLIENT_DIRECTORY}'.")
        return True
    except Exception as e:
        print(f"Error receiving file: {e}")
        return False

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 2:
        print("This program requires at least 2 MPI processes")
        return

    if rank == 0:  # Sender process
        os.makedirs(SERVER_DIRECTORY, exist_ok=True)
        files = os.listdir(SERVER_DIRECTORY)
        if not files:
            print("No files available in the server directory.")
            return

        print("Available files in the server directory:")
        for i, file in enumerate(files, 1):
            print(f"[{i}] {file}")

        try:
            choice = int(input("Enter the number of the file to send: "))
            if choice < 1 or choice > len(files):
                print("Invalid choice.")
                return

            filename = files[choice - 1]
            print(f"Process {rank}: Attempting to send '{filename}'...")

            if send_file(filename, comm, dest_rank=1):
                print(f"Process {rank}: File sent successfully.")
            else:
                print(f"Process {rank}: Failed to send file.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    elif rank == 1:  # Receiver process
        os.makedirs(CLIENT_DIRECTORY, exist_ok=True)
        print(f"Process {rank}: Waiting to receive file...")

        if receive_file(comm, source_rank=0):
            print(f"Process {rank}: File received successfully.")
        else:
            print(f"Process {rank}: Failed to receive file.")

if __name__ == "__main__":
    main()
