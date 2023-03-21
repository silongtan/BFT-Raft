import random
import time
import threading
import logging

logging.basicConfig(level=logging.DEBUG)
from concurrent import futures
import sys
import grpc

import rpc.raft_pb2_grpc as raft_pb2_grpc
from rpc.raft_pb2_grpc import RaftServicer

from client_rpc_handler import RoleType, ClientRPCHandler
from role_type import RoleType, dispatch
from random import randrange

from config import *


class Raft(RaftServicer):

    def __init__(self, port: int, all_address: [], num: int, address: str = "localhost"):
        if num != len(all_address):
            raise Exception("num != len(all_address)")

        # persistent state on all servers
        self.address = address + str(port)  # server address
        self.port = port  # server port
        self.id = port  # server id # TODO
        self.term = 0  # latest term server has seen
        self.log = []  # log entries
        self.role = RoleType.FOLLOWER
        self.num = num  # total number of servers
        self.majority = (num + 1) // 2 + 1
        self.vote_for = -1  # candidateId that received vote in current term (or -1 if none)

        # volatile state on all servers: log & commit
        self.committed_index = -1  # initially -1, represents currently the latest committed entry index
        self.last_applied = -1  # initially -1, represents currently the latest applied entry index

        # Volatile state on candidate:
        self.votes_granted = 0  # votes got in the currentTerm
        # Volatile state on leaders:
        self.next_index = {}  # initially is 0, nextIndex[i] next log entry to send to that server i
        self.match_index = {}  # initially -1, represents currently the highest match index
        for i in all_address:
            self.next_index[i] = 0
            self.match_index[i] = -1
        # rpc
        self.timeout = float(randrange(ELECTION_TIMEOUT_MAX // 2, ELECTION_TIMEOUT_MAX) / 1000)
        self.dead = False
        self.election_timer = None
        # self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # timer
    # self.timer = time.time() + random.randint(2, 7)
    # self.timeout_thread = None
    # self.is_leader = False
    # self.majority = False
    # self.vote_received = 0
    # self.last_log_index = 0
    # self.last_log_term = 0

    def AppendEntries(self, request, context):
        response = dispatch(self).append_entries(request, context)
        return response

    def RequestVote(self, request, context):
        logging.debug(self.address + ":" + str(self.port) + " received RequestVote")
        response = dispatch(self).vote(request, context)
        logging.debug(self.address + ":" + str(self.port) + " - vote granted: " + str(response.voteMe))
        return response

    def NewCommand(self, request, context):
        return ClientRPCHandler.handle_new_command()

    def GetStatus(self, request, context):
        return ClientRPCHandler.handle_get_status()

    def GetCommittedCmd(self, request, context):
        return ClientRPCHandler.handle_get_committed_cmd()

    def activate(self):
        pass

    def deactivate(self):
        pass

    def become(self, role: RoleType):
        self.role = role
        dispatch(self).run()

    def reset_timer(self, function, timeout: int):
        self.election_timer.cancel()  # cancel the previous timer
        self.election_timer = threading.Timer(timeout, function)
        self.election_timer.start()

    def leader_died(self):
        if self.role != RoleType.FOLLOWER:
            return
        logging.debug("leader died")
        self.become(RoleType.CANDIDATE)


def serve():
    all_port = [5000, 5001, 5002]
    all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

    for p in all_port:
        print("Starting server on port: " + sys.argv[1])
        raft_server = Raft(p, all_address, 3)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        raft_pb2_grpc.add_RaftServicer_to_server(raft_server, server)
        server.add_insecure_port("localhost:" + sys.argv[1])
        server.start()
        server.wait_for_termination()


if __name__ == "__main__":
    serve()
