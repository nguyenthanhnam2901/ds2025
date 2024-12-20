import os
import shutil
import subprocess
from mpi4py import MPI

def server_process(comm, size):
    """Server process that handles multiple client commands"""
    print(f"\n[Server] Started on rank 0")
    print(f"[Server] Managing {size-1} clients")
    
    active_clients = set(range(1, size))
    selected_client = None
    
    # Server folder where files are located
    server_folder = "server_folder"
    if not os.path.exists(server_folder):
        os.makedirs(server_folder)
    
    while active_clients:
        try:
            print("\nServer Menu:")
            print("Available commands:")
            print("1. Select client")
            print("2. List active clients")
            print("3. Broadcast command to all clients")
            print("4. Send file to a client")
            print("5. Exit")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                print("\nActive clients:", sorted(list(active_clients)))
                try:
                    selected_client = int(input("Enter client rank to select: "))
                    if selected_client not in active_clients:
                        print("Invalid client rank!")
                        selected_client = None
                        continue
                    
                    while True:
                        command = input(f"\n[To Client {selected_client}]$ ")
                        if command.lower() == 'back':
                            selected_client = None
                            break
                        
                        # Send command to selected client
                        comm.send(command, dest=selected_client, tag=1)
                        
                        if command.lower() == 'exit':
                            active_clients.remove(selected_client)
                            selected_client = None
                            break
                        
                        # Wait for response
                        response = comm.recv(source=selected_client, tag=2)
                        print(f"\nResponse from client {selected_client}:\n{response}")
                
                except ValueError:
                    print("Invalid input! Please enter a number.")
            
            elif choice == '2':
                print("\nActive clients:", sorted(list(active_clients)))
            
            elif choice == '3':
                command = input("\n[Broadcast]$ ")
                for client in active_clients:
                    comm.send(command, dest=client, tag=1)
                    if command.lower() == 'exit':
                        active_clients.remove(client)
                    else:
                        response = comm.recv(source=client, tag=2)
                        print(f"\nResponse from client {client}:\n{response}")
            
            elif choice == '4':
                print("\nAvailable files to send:")
                files = os.listdir(server_folder)
                for idx, file_name in enumerate(files):
                    print(f"{idx + 1}. {file_name}")
                
                file_choice = input("\nEnter the number of the file to send: ").strip()
                try:
                    file_choice = int(file_choice) - 1
                    if file_choice < 0 or file_choice >= len(files):
                        print("Invalid choice!")
                        continue
                    
                    file_name = files[file_choice]
                    file_path = os.path.join(server_folder, file_name)
                    
                    # Send file to selected client
                    selected_client = int(input("\nEnter client rank to send the file to: ").strip())
                    if selected_client not in active_clients:
                        print("Invalid client rank!")
                        continue
                    
                    with open(file_path, "rb") as file:
                        file_data = file.read()
                    
                    comm.send(file_name, dest=selected_client, tag=3)
                    comm.send(file_data, dest=selected_client, tag=4)
                    print(f"\nSent {file_name} to client {selected_client}")
                
                except ValueError:
                    print("Invalid input!")
            
            elif choice == '5':
                # Send exit command to all remaining clients
                for client in active_clients:
                    comm.send("exit", dest=client, tag=1)
                break
            
        except Exception as e:
            print(f"Server error: {e}")
    
    print("[Server] Shutting down...")

def client_process(comm, rank):
    """Client process that executes commands from the server"""
    print(f"[Client {rank}] Started")
    
    # Create a folder for the client if it doesn't exist
    client_folder = f"client_{rank}"
    if not os.path.exists(client_folder):
        os.makedirs(client_folder)
    
    while True:
        try:
            # Wait for command from server
            command = comm.recv(source=0, tag=1)
            
            if command.lower() == 'exit':
                print(f"[Client {rank}] Received exit command. Shutting down...")
                break
            
            print(f"[Client {rank}] Executing command: {command}")
            
            try:
                # Execute the command
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                output, error = process.communicate()
                
                # Prepare response
                if error:
                    response = f"Error: {error}"
                else:
                    response = output if output else "Command executed successfully (no output)"
                
            except Exception as e:
                response = f"Error executing command: {str(e)}"
            
            # Send response back to server
            comm.send(response, dest=0, tag=2)
            
            # Check for incoming file
            if comm.Iprobe(source=0, tag=3):
                file_name = comm.recv(source=0, tag=3)
                file_data = comm.recv(source=0, tag=4)
                file_path = os.path.join(client_folder, file_name)
                
                # Save the received file
                with open(file_path, "wb") as file:
                    file.write(file_data)
                print(f"[Client {rank}] Received and saved file: {file_name}")
        
        except Exception as e:
            print(f"[Client {rank}] Error: {e}")
            break
    
    print(f"[Client {rank}] Disconnected")

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    if size < 2:
        print("This program requires at least 2 MPI processes (1 server + 1 client)")
        return
    
    try:
        if rank == 0:
            server_process(comm, size)
        else:
            client_process(comm, rank)
    
    except Exception as e:
        print(f"Process {rank} encountered an error: {e}")
    
    # Ensure all processes sync before exiting
    comm.Barrier()

if __name__ == "__main__":
    main()