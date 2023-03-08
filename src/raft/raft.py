import random
import time
from concurrent import futures

import grpc

# import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc
from rpc.raft_pb2_grpc import RaftServicer

from client_rpc_handler import RoleType, ClientRPCHandler
from role_type import RoleType, dispatch
from rpc_visitor import AppendEntriesHandler, RequestVoteHandler


class Raft(RaftServicer):

    def __init__(self):
        self.term = 0
        self.log = {}
        self.role = RoleType.FOLLOWER
        self.isLeader = False
        self.majority = False
        # vote
        self.voteFor = None
        self.voteReceived = 0
        # log & commit
        self.committedIndex = 0
        self.last_log_index = 0
        self.last_log_term = 0
        # timer
        self.timer = time.time() + random.randint(2, 7)
        self.timeout_thread = None

    ### Vote section
    def request_vote(self, request, stub):
        pass
        # if (self.role == C):
        #     response = stub.RequestVote(request)
        #     if response.voteMe:
        #         self.voteReceived += 1

    def handle_vote(self, request, context):
        pass

    def AppendEntries(self, request, context):
        return dispatch(self.role,  AppendEntriesHandler())

    def RequestVote(self, request, context):
        return dispatch(self.role, RequestVoteHandler())

    def NewCommand(self, request, context):
        return ClientRPCHandler.handle_new_command()

    def GetStatus(self, request, context):
        return ClientRPCHandler.handle_get_status()

    def GetCommittedCmd(self, request, context):
        return ClientRPCHandler.handle_get_committed_cmd()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServicer_to_server(Raft(), server)
    server.add_insecure_port("localhost:5000")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
