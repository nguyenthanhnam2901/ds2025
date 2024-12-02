import grpc
from concurrent import futures
import os
import file_transfer_pb2
import file_transfer_pb2_grpc

# before running: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. file_transfer.proto

SERVER_DIRECTORY = './open_listenfd'
BUFFER_SIZE = 1024

class FileTransferService(file_transfer_pb2_grpc.FileTransferServicer):
    def ListFiles(self, request, context):
        files = os.listdir(SERVER_DIRECTORY)
        return file_transfer_pb2.FileList(filenames=files)

    def DownloadFile(self, request, context):
        file_path = os.path.join(SERVER_DIRECTORY, request.filename)
        if not os.path.exists(file_path):
            context.abort(grpc.StatusCode.NOT_FOUND, "File not found")
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(BUFFER_SIZE):
                yield file_transfer_pb2.FileChunk(content=chunk)

def serve():
    os.makedirs(SERVER_DIRECTORY, exist_ok=True)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_transfer_pb2_grpc.add_FileTransferServicer_to_server(FileTransferService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
