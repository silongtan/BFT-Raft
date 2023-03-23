import random
import time
import threading
import logging

logging.basicConfig(level=logging.DEBUG)
from concurrent import futures
import sys
import grpc
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc
from rpc.raft_pb2_grpc import RaftServicer

from client_rpc_handler import RoleType, ClientRPCHandler
from app import Application
from role_type import RoleType, dispatch
from random import randrange

from config import *


# replica
class Raft(RaftServicer):

    def __init__(self, port: int, all_address: list, num: int, address: str = "localhost"):

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
        self.init()

    @staticmethod
    def get_majority(num):
        return (num + 1) // 2

    def init(self):
        # print(self.majority)

        self.election_timer = threading.Timer(self.timeout, self.leader_died)
        self.election_timer.start()
        # print(self.timeout)
        # self.become(RoleType.FOLLOWER)  # init as follower
        # print(self.timeout)

    def AppendEntries(self, request, context):
        # TODO
        print(self.address + " received AppendEntriesReply from " + str(request.leaderId))
        response = dispatch(self).append_entries(request, context)
        # logging.debug(self.address + " - append entries success: " + str(response.success))
        return response
        # test
        # print("recieved append entries heartbeat")
        # self.reset_timer(self.leader_died, 1)
        # print("timer reset")
        # reply = {"term": 0, "success": True}
        # return raft_pb2.AppendEntriesReply(**reply)

    def RequestVote(self, request, context):
        logging.debug(self.address + " received RequestVote from " + str(request.candidateId))
        response = dispatch(self).vote(request, context)
        logging.debug(self.address + " - vote granted: " + str(response.voteMe))
        return response

    def NewCommand(self, request, context):
        if self.role != RoleType.LEADER:
            return raft_pb2.StatusReport(self.get_status_report())
        else:
            self.app.execute(request.command)
            self.log.append({'term': self.term, 'command': request.command})
            return raft_pb2.StatusReport(self.get_status_report())

    def get_status_report(self):
        return {'term': self.term, 'committedIndex': self.committed_index,
                'isLeader': self.role == RoleType.LEADER, 'log': self.log}

    def GetStatus(self, request, context):
        return raft_pb2.StatusReport(self.get_status_report())

    def GetCommittedCmd(self, request, context):
        request_index = request.index
        if self.committed_index >= request_index:
            return raft_pb2.GetCommittedCmdReply(self.log[request_index])
        else:
            return raft_pb2.GetCommittedCmdReply("")

    def activate(self):
        pass

    def deactivate(self):
        pass

    def become(self, role: RoleType):
        logging.debug("become " + str(role) + ", current term: " + str(self.term))
        self.role = role
        dispatch(self).run()

    def reset_timer(self, function, timeout: int):
        self.election_timer.cancel()  # cancel the previous timer
        self.election_timer = threading.Timer(timeout, function)
        self.election_timer.start()

    def reset_timeout(self):
        self.timeout = float(randrange(ELECTION_TIMEOUT_MAX_MILLIS // 2, ELECTION_TIMEOUT_MAX_MILLIS) / 1000)

    def leader_died(self):
        if self.role != RoleType.FOLLOWER:
            return
        logging.debug("leader died")
        self.become(RoleType.CANDIDATE)

    def get_last_log_index(self):
        return len(self.log) - 1

    def get_last_log_term(self):
        return 0 if len(self.log) == 0 else self.log[-1].term

    # both inclusive
    def apply_log(self, index: int):
        for i in range(self.last_applied + 1, index + 1):
            self.app.execute(self.log[i])
        self.last_applied = index


def serve():
    all_port = [5000, 5001, 5002]
    all_address = ["localhost:5000", "localhost:5001", "localhost:5002"]

    # for p in all_port:
    p = sys.argv[1]
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


if __name__ == "__main__":
    serve()
