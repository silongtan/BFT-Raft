from multiprocessing import Process, Queue
from concurrent import futures
import sys
import grpc
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP  # More secure RSA formulation
from Crypto import Random
# from raft import serve
from raft import Raft

def main():
    num_nodes = 3
    # generate keys
    random_generator = Random.new().read
    private_keys = [RSA.generate(1024, random_generator) for i in range(num_nodes + 1)]
    public_keys = [k.publickey() for k in private_keys]

    # generate queues
    queues = [Queue() for i in range(num_nodes + 1)]
    client_num = num_nodes
    client_queue = queues[client_num]

    # start up the nodes
    raft_nodes = []
    # customize
    all_port = [5000, 5001, 5002]
    all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

    for port in all_port:
        p = Process(target=serve, args=(all_port, all_address, port))
        p.start()
        raft_nodes.append(p)

def serve(all_port: list, all_address: list, port: int):
    # all_port = [5000, 5001, 5002]
    # all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

    # for p in all_port:
    # p = sys.argv[1]
    p = str(port)
    print("Starting server on port: " + p)
    raft_server = Raft(int(p), all_address, 3)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
    server.add_insecure_port("localhost:" + p)
    try:
        server.start()
        while True:
            server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("Server" + raft_server.address + "is shutting down")

def generate_key_pairs(num:int):
    random_generator = Random.new().read
    private_keys = [RSA.generate(1024, random_generator) for _ in range(num + 1)]

    port = 5000
    for key in private_keys:
        print("generating")

        file_out = open(f"keys/private/{port}.pem", "wb")
        file_out.write(key.export_key())
        file_out.close()

        file_out = open(f"keys/public/localhost:{port}.pem", "wb")
        file_out.write(key.publickey().export_key())
        file_out.close()
        port += 1

if __name__ == '__main__':
    # main()
    generate_key_pairs(3)