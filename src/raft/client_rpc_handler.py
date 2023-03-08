from enum import Enum
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc


class RoleType(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


#
# class RaftRPCHandler:
#     @staticmethod
#     def handle_append_entries(role: RoleType, **kwargs):
#         switcher = {
#             RoleType.FOLLOWER: _Follower.handle_append_entries,
#             RoleType.CANDIDATE: _Candidate.handle_append_entries,
#             RoleType.LEADER: _Leader.handle_append_entries,
#         }
#         func = switcher.get(role, lambda: "Invalid role")
#         return func(**kwargs)
#
#     @staticmethod
#     def handle_request_vote(role: RoleType, **kwargs):
#         switcher = {
#             RoleType.FOLLOWER: _Follower.handle_request_vote,
#             RoleType.CANDIDATE: _Candidate.handle_request_vote,
#             RoleType.LEADER: _Leader.handle_request_vote,
#         }
#         func = switcher.get(role, lambda: "Invalid role")
#         return func(**kwargs)
#
#     @staticmethod
#     def send_append_entries(stub, **kwargs):
#         pass
#
#     @staticmethod
#     def send_request_vote(stub, **kwargs):
#         pass


# class _Follower:
#     @staticmethod
#     def handle_append_entries(**kwargs):
#         print("AppendEntries")
#         return raft_pb2.AppendEntriesReply(status="OK")
#
#     @staticmethod
#     def handle_request_vote(**kwargs):
#         print("RequestVote")
#         return raft_pb2.RequestVoteReply()
#
#     @staticmethod
#     def send_append_entries(stub, **kwargs):
#         pass
#
#     @staticmethod
#     def send_request_vote(stub, **kwargs):
#         pass
#
#
# class _Candidate:
#     @staticmethod
#     def handle_append_entries(**kwargs):
#         pass
#
#     @staticmethod
#     def handle_request_vote(**kwargs):
#         pass
#
#     @staticmethod
#     def send_append_entries(stub, **kwargs):
#         pass
#
#     @staticmethod
#     def send_request_vote(stub, **kwargs):
#         pass
#
#
# class _Leader:
#     @staticmethod
#     def handle_append_entries(**kwargs):
#         pass
#
#     @staticmethod
#     def handle_request_vote(**kwargs):
#         pass
#
#     @staticmethod
#     def send_append_entries(stub, **kwargs):
#         pass
#
#     @staticmethod
#     def send_request_vote(stub, **kwargs):
#         pass
#

class ClientRPCHandler:
    @staticmethod
    def handle_get_committed_cmd():
        print("GetCommittedCmd")
        return raft_pb2.GetCommittedCmdReply(term=1)

    @staticmethod
    def handle_get_status():
        print("GetStatus from raft")
        status_reply = raft_pb2.StatusReport(term=1, committedIndex=2, isLeader=True,
                                             log=[{'term': 1, 'command': "test"}])

        print(status_reply)

        return status_reply

    @staticmethod
    def handle_new_command():
        print("NewCommand")
        status_reply = raft_pb2.StatusReport(term=1, committedIndex=2, isLeader=True,
                                             log=[{'term': 1, 'command': "test"}])

        print(status_reply)

        return status_reply
