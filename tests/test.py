import sys
import unittest
import time
from multiprocessing import Process, Manager

sys.path.append('../src/raft')
from raft.raft import *
from raft.client import *


def whatever(magic_list):
    magic_list.append(1)


def serve(all_port: list, all_address: list, port: int):
    # all_port = [5000, 5001, 5002]
    # all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

    # for p in all_port:
    # p = sys.argv[1]
    p = str(port)
    print("Starting server on port: " + p)
    raft_server = Raft(int(p), all_address, 3,None,None)
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


class TestRaft(unittest.TestCase):

    def test01_initServer(self):
        raft_server = Raft(5000, ["localhost:5000"], 1, None, None)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
        server.add_insecure_port("localhost:5000")
        server.start()
        self.assertEqual(raft_server.address, "localhost:5000")
        server.stop(0)

    def test02_clientRPC(self):
        try:
            raft_server = Raft(5000, ["localhost:5000"], 1, None, None)
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
            server.add_insecure_port("localhost:5000")
            server.start()
            send_new_command("localhost:5000", "test")
            server.stop(0)
        except Exception as e:
            print(e)
            raise

    def test03_initRole(self):
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        for p in all_port:
            raft_server = Raft(p, all_address, 3, None, None)
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
            server.add_insecure_port("localhost:" + str(p))
            server.start()
            self.assertEqual(raft_server.role, RoleType.FOLLOWER)
            server.stop(0)

    def test04_leaderElection(self):
        is_leader = False
        raft_nodes = []
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        for port in all_port:
            p = Process(target=serve, args=(all_port, all_address, port))
            p.start()
            raft_nodes.append(p)

        time.sleep(1)
        res = send_get_status("localhost:5000")
        print(res)

        for i in range(10):
            time.sleep(1)
            for addr in all_address:
                # print(s.role, s.address)
                res = send_get_status(addr)
                print(res.isLeader)
                is_leader = res.isLeader
                break

        self.assertTrue(is_leader)

    def test05_duplicatedLeader(self):
        max_leader_count = 0
        raft_nodes = []
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        for port in all_port:
            p = Process(target=serve, args=(all_port, all_address, port))
            p.start()
            raft_nodes.append(p)

        time.sleep(1)

        for i in range(10):
            time.sleep(1)
            temp_count = 0
            for addr in all_address:
                res = send_get_status(addr)
                if res.isLeader:
                    temp_count += 1
            max_leader_count = max(temp_count, max_leader_count)

        self.assertTrue(max_leader_count == 1)







if __name__ == '__main__':
    unittest.main()
