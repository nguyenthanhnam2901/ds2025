from mpi4py import MPI
import pty
import os
import select
import sys
import time
import subprocess
import uuid

'''
Can only run in Linux.
Require: mpi4py, xterm, bash
Run:
mpiexec -n 4 remote_shell_MPI.py
'''

def run_server(comm, size):
    # Create a unique server directory to prove command execution
    server_dir = f"/tmp/mpi_server_{uuid.uuid4().hex[:8]}"
    os.makedirs(server_dir, exist_ok=True)
    
    print(f"[Server] Started in {server_dir}")
    print(f"[Server] Waiting for {size-1} clients...")
    sys.stdout.flush()
    
    terminals = {}
    
    for client_rank in range(1, size):
        master_fd, slave_fd = pty.openpty()
        pid = os.fork()
        
        if pid == 0:  # Child process
            os.close(master_fd)
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.close(slave_fd)
            
            # Change to server directory
            os.chdir(server_dir)
            os.execvp('/bin/bash', ['/bin/bash'])
        else:  # Parent process
            os.close(slave_fd)
            terminals[client_rank] = {'fd': master_fd, 'pid': pid}
    
    while terminals:
        for client_rank, term in list(terminals.items()):
            if comm.Iprobe(source=client_rank):
                command = comm.recv(source=client_rank)
                
                if command == "exit":
                    print(f"[Server] Client {client_rank} disconnected")
                    os.close(term['fd'])
                    os.kill(term['pid'], 9)
                    del terminals[client_rank]
                    continue
                
                print(f"[Server] Client {client_rank} executing: {command}")
                os.write(term['fd'], (command + '\n').encode())
                time.sleep(0.1)
                
                output = b""
                while True:
                    ready, _, _ = select.select([term['fd']], [], [], 0.1)
                    if not ready:
                        break
                    try:
                        chunk = os.read(term['fd'], 4096)
                        if not chunk:
                            break
                        output += chunk
                    except OSError:
                        break
                
                # Add server identifier to output
                server_info = f"\n[Executed on server in {server_dir}]\n"
                output = output + server_info.encode()
                comm.send(output.decode(), dest=client_rank)
        time.sleep(0.1)
    
    # Cleanup server directory
    os.system(f"rm -rf {server_dir}")

def run_client(comm, rank):
    script_content = f"""#!/usr/bin/env python3
import sys
import time
import os

def read_response():
    response_file = "/tmp/mpi_response_{rank}"
    if os.path.exists(response_file):
        with open(response_file, 'r') as f:
            response = f.read()
        os.remove(response_file)
        return response
    return None

print("Client {rank} started. All commands will be executed on the server.")
print("Local working directory:", os.getcwd())

while True:
    try:
        cmd = input("\\033[92m[Client {rank}]$\\033[0m ")
        if not cmd:
            continue
            
        with open("/tmp/mpi_cmd_{rank}", "w") as f:
            f.write(cmd)
            
        if cmd == "exit":
            break
            
        # Wait for response
        for _ in range(50):  # 5 seconds timeout
            response = read_response()
            if response is not None:
                print(response, end='')
                break
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        with open("/tmp/mpi_cmd_{rank}", "w") as f:
            f.write("exit")
        break
"""
    
    script_path = f"/tmp/mpi_client_{rank}.py"
    with open(script_path, "w") as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    
    terminal_cmd = f"xterm -T 'Client {rank}' -e python3 {script_path}"
    subprocess.Popen(terminal_cmd, shell=True)
    
    time.sleep(1)
    
    while True:
        try:
            cmd_file = f"/tmp/mpi_cmd_{rank}"
            if os.path.exists(cmd_file):
                with open(cmd_file, 'r') as f:
                    command = f.read().strip()
                os.remove(cmd_file)
                
                if command:
                    comm.send(command, dest=0)
                    
                    if command == "exit":
                        break
                        
                    response = comm.recv(source=0)
                    with open(f"/tmp/mpi_response_{rank}", "w") as f:
                        f.write(response)
                    
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    # Cleanup
    try:
        os.remove(script_path)
        os.remove(f"/tmp/mpi_cmd_{rank}")
        os.remove(f"/tmp/mpi_response_{rank}")
    except:
        pass

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    if rank == 0:
        run_server(comm, size)
    else:
        run_client(comm, rank)

if __name__ == "__main__":
    main()