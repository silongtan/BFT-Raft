import sys
import unittest
import time
from multiprocessing import Process

sys.path.append('../src/raft')
from raft.raft import *
from raft.client import *


def serve(all_address: list, port: int, public_keys: dict, private_key: rsa.PrivateKey):
    p = str(port)
    print("Starting server on port: " + p)
    raft_server = Raft(int(p), all_address, 3, public_keys, private_key)
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
        try:
            self.assertEqual(raft_server.address, "localhost:5000")
            server.stop(0)
        except KeyboardInterrupt:
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
            server.stop(0)
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

        public_keys = {}
        for address in all_address:
            with open(f"../src/raft/keys/public/{address}.pem", "r") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read().encode())
                public_keys[address] = public_key

        for port in all_port:
            with open(f"../src/raft/keys/private/localhost:{port}.pem", "r") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
            p = Process(target=serve, args=(all_address, port, public_keys, private_key))
            p.start()
            raft_nodes.append(p)

        # time.sleep(10)
        #
        # while is_leader is False:
        #     for addr in all_address:
        #         res = send_get_status(addr)
        #         print(addr, res)
        #         is_leader = res.isLeader
        #         if is_leader:
        #             break
        #         time.sleep(3)

        for i in range(10):
            time.sleep(1)
            for addr in all_address:
                # print(s.role, s.address)
                res = send_get_status(addr)
                print(addr, res)
                is_leader = res.isLeader
                if is_leader:
                    break
            if is_leader:
                break

        try:
            self.assertTrue(is_leader)
            for p in raft_nodes:
                p.terminate()
        except KeyboardInterrupt:
            for p in raft_nodes:
                p.terminate()

    def test05_leaderDie(self):
        is_leader = False
        raft_nodes = []
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        public_keys = {}
        for address in all_address:
            with open(f"../src/raft/keys/public/{address}.pem", "r") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read().encode())
                public_keys[address] = public_key

        for port in all_port:
            with open(f"../src/raft/keys/private/localhost:{port}.pem", "r") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
            p = Process(target=serve, args=(all_address, port, public_keys, private_key))
            p.start()
            raft_nodes.append(p)

        time.sleep(10)

        while is_leader is False:
            for addr in all_address:
                res = send_get_status(addr)
                if res.isLeader:
                    is_leader = res.isLeader
                    print(addr, "I AM LEADER")
                    deactivate_replica(addr)
                    break
                time.sleep(3)
        time.sleep(10)

        is_leader = False

        while is_leader is False:
            for addr in all_address:
                res = send_get_status(addr)
                if res.isLeader:
                    print(addr, "I AM THE NEW LEADER")
                    is_leader = res.isLeader
                    break
                time.sleep(3)

        try:
            self.assertTrue(is_leader)
            for p in raft_nodes:
                p.terminate()
        except KeyboardInterrupt:
            for p in raft_nodes:
                p.terminate()

    def test06_duplicatedLeader(self):
        max_leader_count = 0
        raft_nodes = []
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        public_keys = {}
        for address in all_address:
            with open(f"../src/raft/keys/public/{address}.pem", "r") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read().encode())
                public_keys[address] = public_key

        for port in all_port:
            with open(f"../src/raft/keys/private/localhost:{port}.pem", "r") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
            p = Process(target=serve, args=(all_address, port, public_keys, private_key))
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
        try:
            self.assertTrue(max_leader_count == 1)
            for p in raft_nodes:
                p.terminate()
        except KeyboardInterrupt:
            for p in raft_nodes:
                p.terminate()


    def test07_logCheck(self):
        raft_nodes = []
        all_port = [5000, 5001, 5002]
        all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

        public_keys = {}
        for address in all_address:
            with open(f"../src/raft/keys/public/{address}.pem", "r") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read().encode())
                public_keys[address] = public_key

        for port in all_port:
            with open(f"../src/raft/keys/private/localhost:{port}.pem", "r") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
            p = Process(target=serve, args=(all_address, port, public_keys, private_key))
            p.start()
            raft_nodes.append(p)

        for i in range(10):
            command = "add key" + str(i) + " " + str(i)
            send_new_command(all_address[0], command)

        time.sleep(10)
        all_logs = []
        for addr in all_address:
            res = send_get_status(addr)
            all_logs.append(res.log)

        print(all_logs[0])

        for p in raft_nodes:
            p.terminate()


if __name__ == '__main__':
    unittest.main()
