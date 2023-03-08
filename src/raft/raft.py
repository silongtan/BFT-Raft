from rpc.raft_pb2_grpc import RaftServicer
import grpc
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc
from concurrent import futures
import rpc
import threading
import time
import random

F = "follower"
C = "candidate"
L = "leader"

class Raft(RaftServicer):

    def __init__(self):
        pass
        self.term = 0
        self.log = {}
        self.role = F
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
        self.timer = time.time() + random.randint(2,7)
        self.timeout_thread = None

    def GetStatus(self, request, context):
        print("GetStatus from raft")
        status_reply = raft_pb2.StatusReport(term=1, committedIndex=2, isLeader=True,
                                             log=[{'term': 1, 'command': "test"}])

        print(status_reply)

        return status_reply

    def AppendEntries(self, request, context):
        print("AppendEntries")
        return raft_pb2.AppendEntriesReply(status="OK")

    def RequestVote(self, request, context):
        print("RequestVote")
        return raft_pb2.RequestVoteReply()

    def GetCommittedCmd(self, request, context):
        print("GetCommittedCmd")
        return raft_pb2.GetCommittedCmdReply(term=1)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServicer_to_server(Raft(), server)
    server.add_insecure_port("localhost:5000")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
