from raft import raft as raft
from raft import client as client
import unittest


class TestRaft(unittest.TestCase):
    def test01_initServer(self):
        # all_port = [5000, 5001, 5002]
        # all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        # for p in all_port:
        #     print("Starting server on port: " + raft.sys.argv[1])
        #     raft_server = raft.Raft(p, all_address, 3)
        #     server = raft.grpc.server(raft.futures.ThreadPoolExecutor(max_workers=10))
        #     raft.raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
        #     server.add_insecure_port("localhost:" + raft.sys.argv[1])
        #     server.start()
        #     server.wait_for_termination()
        #     self.assertEqual(raft_server.address, p)
        raft_server = raft.Raft(5000, ["localhost:5000"])
        server = raft.grpc.server(raft.futures.ThreadPoolExecutor(max_workers=10))
        raft.raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
        server.add_insecure_port("localhost:5000")
        server.start()
        server.wait_for_termination()
        print(1)
        self.assertEqual(raft_server.address, 5000)

    def test02_clientRPC(self):
        print(2)
        try:
            c = client.Client(["localhost:5000"])
            c.send_new_command("test")
        except Exception as e:
            print(e)
            raise

    def test03_initRole(self):
        print(3)
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        for p in all_port:
            print("Starting server on port: " + raft.sys.argv[1])
            raft_server = raft.Raft(p, all_address, 3)
            server = raft.grpc.server(raft.futures.ThreadPoolExecutor(max_workers=10))
            raft.raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
            server.add_insecure_port("localhost:" + raft.sys.argv[1])
            server.start()
            server.wait_for_termination()
            self.assertEqual(raft_server.address, p)

    # def test04_changeRole(self):
    #     pass


if __name__ == '__main__':
    unittest.main()
