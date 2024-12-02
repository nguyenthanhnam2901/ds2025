import grpc
import os
import file_transfer_pb2
import file_transfer_pb2_grpc

# before running: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. file_transfer.proto

SERVER_HOST = 'localhost:50051'
CLIENT_DIRECTORY = './open_clientfd'

def list_files(stub):
    response = stub.ListFiles(file_transfer_pb2.Empty())
    print("Available files:")
    for filename in response.filenames:
        print(f"- {filename}")

def download_file(stub, filename):
    file_path = os.path.join(CLIENT_DIRECTORY, filename)
    try:
        response = stub.DownloadFile(file_transfer_pb2.FileRequest(filename=filename))
        os.makedirs(CLIENT_DIRECTORY, exist_ok=True)
        with open(file_path, 'wb') as f:
            for chunk in response:
                f.write(chunk.content)
        print(f"File '{filename}' downloaded successfully.")
    except grpc.RpcError as e:
        print(f"Error: {e.details()}")

def main():
    with grpc.insecure_channel(SERVER_HOST) as channel:
        stub = file_transfer_pb2_grpc.FileTransferStub(channel)
        
        while True:
            list_files(stub)
            requested_file = input("Enter the file name to download (or 'exit' to quit): ").strip()
            if requested_file.lower() == 'exit':
                print("Exiting...")
                break
            download_file(stub, requested_file)

if __name__ == "__main__":
    main()
