import sys
import unittest
sys.path.append('../src/raft')
from raft.raft import *
from raft.client import *


class TestRaft(unittest.TestCase):

    def test01_initServer(self):
        raft_server = Raft(5000, ["localhost:5000"], 1)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
        server.add_insecure_port("localhost:5000")
        server.start()
        self.assertEqual(raft_server.address, "localhost:5000")
        server.stop(0)

    def test02_clientRPC(self):
        try:
            raft_server = Raft(5000, ["localhost:5000"], 1)
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
            server.add_insecure_port("localhost:5000")
            server.start()
            c = Client(["localhost:5000"])
            c.send_new_command("test")
            server.stop(0)
        except Exception as e:
            print(e)
            raise

    def test03_initRole(self):
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        for p in all_port:
            raft_server = Raft(p, all_address, 3)
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
            server.add_insecure_port("localhost:" + str(p))
            server.start()
            self.assertEqual(raft_server.role, RoleType.FOLLOWER)
            server.stop(0)

    def test04_leaderElection(self):
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]
        server_list = []

        for p in all_port:
            raft_server = Raft(p, all_address, 3)
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
            server.add_insecure_port("localhost:" + str(p))
            server_list.append(server)
            server.start()
            self.assertEqual(raft_server.role, RoleType.FOLLOWER)
            server.stop(0)


if __name__ == '__main__':
    unittest.main()
