
from abc import ABC, abstractmethod
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc


class RPCVisitor(ABC):
    def visit_follower(self):
        pass

    def visit_candidate(self):
        pass

    def visit_leader(self):
        pass


class AppendEntriesHandler(RPCVisitor):
    def visit_follower(self):
        print("AppendEntries")
        return raft_pb2.AppendEntriesReply(status="OK")

    def visit_candidate(self):
        pass

    def visit_leader(self):
        pass


class RequestVoteHandler(RPCVisitor):
    def visit_follower(self):
        print("RequestVote")
        return raft_pb2.RequestVoteReply()

    def visit_candidate(self):
        pass

    def visit_leader(self):
        pass
