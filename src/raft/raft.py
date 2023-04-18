import random
import time
import threading
import logging

# logging.basicConfig(level=logging.DEBUG)
from concurrent import futures
import sys
import grpc
import rsa
# from grpc import aio
import asyncio
# import rpc.raft_pb2 as raft_pb2
# import rpc.raft_pb2_grpc as raft_pb2_grpc
# from rpc.raft_pb2_grpc import RaftServicer


import rpc.bft_raft_pb2 as raft_pb2
import rpc.bft_raft_pb2_grpc as raft_pb2_grpc
from rpc.bft_raft_pb2_grpc import RaftServicer

# from client_rpc_handler import RoleType, ClientRPCHandler
from app import Application
from role_type import RoleType, dispatch
from random import randrange

from config import *


# replica
class Raft(RaftServicer):

    def __init__(self, port: int, all_address: list, num: int, public_keys: dict, private_key,
                 address: str = "localhost"):

        if num != len(all_address):
            raise Exception("num != len(all_address)")

        # persistent state on all servers
        self.address = address + ":" + str(port)  # server address
        self.all_address = all_address  # all server address
        self.peers = [add for add in all_address if add != self.address]
        self.port = port  # server port
        self.id = port  # server id # TODO
        self.term = 0  # latest term server has seen
        self.log = []  # log entries
        self.role = RoleType.FOLLOWER
        self.num = num  # total number of servers
        self.majority = self.get_majority(self.num)
        self.vote_for = -1  # candidateId that received vote in current term (or -1 if none)

        # only for test
        self.active = True

        # volatile state on all servers: log & commit
        self.committed_index = -1  # initially -1, represents currently the latest committed entry index
        self.last_applied = -1  # initially -1, represents currently the latest applied entry index

        # Volatile state on candidate:
        self.votes_granted = 0  # votes got in the currentTerm
        # Volatile state on leaders:
        self.next_index = {}  # initially is 0, nextIndex[i] next log entry to send to that server i
        self.match_index = {}  # initially -1, represents currently the highest match index
        for i in self.peers:
            self.next_index[i] = 0
            self.match_index[i] = -1
        # rpc
        # init timeout
        self.timeout = None
        self.reset_timeout()
        self.dead = False
        self.election_timer = None  # leader: heartbeat timer, follower/candidate: election timer
        # self.lock = threading.Lock()
        # self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.app = Application()

        # 拜占庭
        self.public_keys = public_keys
        self.private_key = private_key
        self.signed_votes = []
        self.lock = threading.Lock()
        self.delay_vote = None
        # self.should_vote_delay = False
        self.init()

    @staticmethod
    def get_majority(num):
        return (num + 1) // 2

    def init(self):
        # print(self.majority)

        self.election_timer = threading.Timer(self.timeout, self.leader_died)
        self.election_timer.start()
        print(self.timeout)
        # self.become(RoleType.FOLLOWER)  # init as follower
        # print(self.timeout)

    def AppendEntries(self, request, context):
        # TODO
        if self.active is False:
            print("replica is not active")
            return

        print(self.address + " received AppendEntries from " + str(request.leaderId))
        response = dispatch(self).append_entries(request, context)
        # logging.debug(self.address + " - append entries success: " + str(response.success))
        # print(request)
        return response
        # test
        # print("recieved append entries heartbeat")
        # self.reset_timer(self.leader_died, 1)
        # print("timer reset")
        # reply = {"term": 0, "success": True}
        # return raft_pb2.AppendEntriesReply(**reply)

    def RequestVote(self, request, context):
        if self.active is False:
            print("replica is not active")
            return

        logging.debug(self.address + " received RequestVote from " + str(request.candidateId))
        response = dispatch(self).vote(request, context)
        logging.debug(self.address + " vote to: " + str(response.voteFor) + " " + str(response.voteMe))
        return response

    def NewCommand(self, request, context):
        if self.active is False:
            print("replica is not active")
            return

        with self.lock:
            if self.role != RoleType.LEADER:
                return self.get_status_report()
            else:
                self.app.execute(request.command)
                self.log.append({'term': self.term, 'command': request.command})
                return self.get_status_report()

    def ReSendVoteReply(self, response, context):
        # print("ReSendVoteReply", response)
        # never reach here
        if not response.isValid:
            print('invalid vote,reset timer')
            self.reset_timer(dispatch(self).process_vote, self.timeout)
            return raft_pb2.Nothing()
        # response = stub.RequestVote.future(request).result()
        # print("vote response", response)
        if response.voteMe:
            self.votes_granted += 1
            # print('append', response)
            self.signed_votes.append(response)
            if self.votes_granted >= self.majority:
                self.become(RoleType.LEADER)

        if response.term > self.term:
            self.term = response.term
            self.become(RoleType.FOLLOWER)
            self.vote_for = -1
            self.votes_granted = 0
            self.timeout = float(
                randrange(ELECTION_TIMEOUT_MAX_MILLIS // 2, ELECTION_TIMEOUT_MAX_MILLIS) / 1000)
            self.reset_timer(self.leader_died, self.timeout)
        return raft_pb2.Nothing()

    # helper functions for replica to get status report and send back to client
    def get_status_report(self) -> raft_pb2.StatusReport:
        args = {'term': self.term, 'committedIndex': self.committed_index,
                'isLeader': self.role == RoleType.LEADER}
        # print('get_status_report')
        # print(self.role == RoleType.LEADER)
        report = raft_pb2.StatusReport(**args)

        # print("LOG: ", self.log)

        if not self.log:
            report.log.extend(self.log)
        else:
            res = [raft_pb2.LogEntry(term=self.log[i].get('term'),
                                     command=self.log[i].get('command')) for i in range(len(self.log))]
            # msg =
            report.log.extend(res)

        # report.log.extend(self.log)
        return report

    def GetStatus(self, request, context):
        # print('test')
        # print(self.get_status_report())
        return self.get_status_report()
        # print(report)
        # return report

    def GetCommittedCmd(self, request, context):
        request_index = request.index
        if self.committed_index >= request_index:
            return raft_pb2.GetCommittedCmdReply(command=self.log[request_index])
        else:
            return raft_pb2.GetCommittedCmdReply(command="")

    def Activate(self, request, context):
        self.active = True
        return self.get_status_report()

    def Deactivate(self, request, context):
        self.active = False
        return self.get_status_report()

    def become(self, role: RoleType):
        logging.debug(self.address + " become " + str(role) + ", prev term: " + str(self.term))
        # self.election_timer.cancel()
        with self.lock:
            self.role = role
        dispatch(self).run()

    def reset_timer(self, function, timeout: float):
        self.election_timer.cancel()  # cancel the previous timer
        self.election_timer = threading.Timer(timeout, function)
        self.election_timer.start()

    def reset_timeout(self):
        self.timeout = float(randrange(ELECTION_TIMEOUT_MAX_MILLIS / 2, ELECTION_TIMEOUT_MAX_MILLIS) / 1000)

    def leader_died(self):
        with self.lock:
            if self.role != RoleType.FOLLOWER:
                return
        if self.delay_vote is not None:
            dispatch(self).resend_vote_reply(self.delay_vote)
            self.become(RoleType.FOLLOWER)
            # logging.debug(self.address + " leader died")
            return
        logging.debug(self.address + " leader died")
        self.become(RoleType.CANDIDATE)

    def get_last_log_index(self):
        return len(self.log) - 1

    def get_last_log_term(self):
        return 0 if len(self.log) == 0 else self.log[-1].term

    # both inclusive
    def apply_log(self, index: int):
        for i in range(self.last_applied + 1, index + 1):
            # pass
            self.app.execute(self.log[i].get('command'))
        self.last_applied = index

    def sign_msg(self, msg):
        return rsa.sign(msg.encode(), self.private_key, 'SHA-256')

    # @staticmethod
    # msg is plain text, verify AE valid
    def verify_msg(self, term, leader_id, vote_from, vote_for, signature) -> bool:
        # print("checking " + "localhost:"+str(leader_id), str(vote_for))

        if "localhost:" + str(leader_id) != str(vote_for):
            # print('not equal')
            return False
        msg = str(term) + " " + str(leader_id) + " " + str(vote_from) + " " + str(vote_for)
        # print('sign',msg)
        public_key = self.public_keys[vote_from]
        try:
            rsa.verify(msg.encode(), signature, public_key)
            # print(True)
            return True
        except rsa.VerificationError:
            # print(False)
            return False
        # if rsa.verify(msg.encode(), signature, public_key):
        #     return True
        # else:
        #     return False


# def decode_msg(self, encrypted_msg):
#     return rsa.decrypt(encrypted_msg, self.private_key).decode()


async def async_server():
    all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]
    p = sys.argv[1]
    with open(f"keys/private/localhost:{p}.pem", "r") as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
    public_keys = {}
    for address in all_address:
        with open(f"keys/public/{address}.pem", "r") as f:
            # public_key = f.read()
            # public_key = RSA.importKey(public_key)
            public_key = rsa.PublicKey.load_pkcs1(f.read().encode())
            public_keys[address] = public_key
    print("Starting server on port: " + p)
    raft_server = Raft(int(p), all_address, 3, public_keys, private_key)
    # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = aio.server()
    # server = aio.server()
    raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
    server.add_insecure_port("localhost:" + p)
    await server.start()
    await server.wait_for_termination()
    # try:
    #     server.start()
    #     while True:
    #         server.wait_for_termination()
    # except KeyboardInterrupt:
    #     server.stop(0)
    #     print("Server" + raft_server.address + "is shutting down")


def serve_one():
    all_port = [5000, 5001, 5002]
    all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

    # for p in all_port:
    p = sys.argv[1]
    # private_key = sys.argv[2]
    # read private key from file
    with open(f"keys/private/localhost:{p}.pem", "r") as f:
        # private_key = f.read()
        # private_key = RSA.importKey(private_key)
        private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
        # print(private_key)

    public_keys = {}
    for address in all_address:
        with open(f"keys/public/{address}.pem", "r") as f:
            # public_key = f.read()
            # public_key = RSA.importKey(public_key)
            public_key = rsa.PublicKey.load_pkcs1(f.read().encode())
            public_keys[address] = public_key
            # print(public_key)

    # p = str(port)
    print("Starting server on port: " + p)
    raft_server = Raft(int(p), all_address, 3, public_keys, private_key)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # server = aio.server()
    raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
    server.add_insecure_port("localhost:" + p)
    try:
        # print(bytes(True))
        # print(bytes(False))
        ## encryption test
        # encrypted_msg = rsa.encrypt(bytes(True), public_keys["localhost:5000"])
        # # print(encrypted_msg)
        # # print(raft_server.public_keys)
        # clear_msg = rsa.decrypt(encrypted_msg, private_key)
        # print(clear_msg.decode())
        # encrypted_msg = rsa.encrypt("hello world".encode(), public_keys["localhost:5000"])
        # # print(encrypted_msg)
        # # print(raft_server.public_keys)
        # clear_msg = rsa.decrypt(encrypted_msg, private_key)
        # print(clear_msg.decode())

        # msg = str(1) + " " + str(5000) + " " + raft_server.address + " localhost:" + str(
        #     5000)
        # print('origin',msg)
        # # signature test
        # signature = rsa.sign(msg.encode(), private_key, "SHA-256")
        #
        # print(raft_server.verify_msg(1, 5000, "localhost:5000", "localhost:5000", signature))
        # print(not rsa.verify("hello dworld".encode(), signature, public_keys["localhost:5000"]))
        # print(rsa.verify("hello  world".encode(), signature, public_keys["localhost:5000"]))

        # recipient_key = raft_server.public_keys["localhost:5000"]
        # print(recipient_key)
        # session_key = get_random_bytes(16)
        #
        # # Encrypt the session key with the public RSA key
        # cipher_rsa = PKCS1_OAEP.new(recipient_key)
        # enc_session_key = cipher_rsa.encrypt(session_key)
        #
        # # Encrypt the data with the AES session key
        # cipher_aes = AES.new(session_key, AES.MODE_EAX)
        # ciphertext, tag = cipher_aes.encrypt_and_digest("hello world".encode("utf-8"))
        # test = [x for x in (enc_session_key, cipher_aes.nonce, tag, ciphertext)]
        #
        # private_key = raft_server.private_key
        # enc_session_key, nonce, tag, ciphertext = [x for x in (private_key.size_in_bytes(), 16, 16, -1)]
        # # Decrypt the session key with the private RSA key
        # cipher_rsa = PKCS1_OAEP.new(private_key)
        # session_key = cipher_rsa.decrypt(bytes(enc_session_key))

        # Decrypt the data with the AES session key
        # cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        # data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        # print(data.decode("utf-8"))
        ###
        server.start()
        while True:
            server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("Server" + raft_server.address + "is shutting down")


if __name__ == "__main__":
    serve_one()
    # asyncio.run(async_server())
