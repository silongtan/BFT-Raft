import random
import grpc
import rpc.bft_raft_pb2 as raft_pb2
import rpc.bft_raft_pb2_grpc as raft_pb2_grpc


def send_get_status(addr: str):
    # replica = self.__choose_replica()
    with grpc.insecure_channel(addr) as channel:
        stub = raft_pb2_grpc.RaftStub(channel)
        get_status_request = raft_pb2.GetStatusRequest()
        status_reply = stub.GetStatus(get_status_request)
        print(status_reply)
        return status_reply


def send_new_command(addr: str, request: str):
    with grpc.insecure_channel(addr) as channel:
        # stub = self.stubs[replica]
        stub = raft_pb2_grpc.RaftStub(channel)
        new_command_request = raft_pb2.NewCommandRequest(command=request)
        status_reply = stub.NewCommand(new_command_request)
        print(status_reply)
        # print(status_reply.log)


# class Client:
#
#     def __init__(self, replicas: list):
#         self.raft_replicas = replicas
#         self.stubs = {}
#         for replica in self.raft_replicas:
#             self.stubs[replica] = grpc.insecure_channel(replica)

    # append_entries

    # @staticmethod
def send_get_committed_cmd(replica_address: str):
    with grpc.insecure_channel(replica_address) as channel:
        stub = raft_pb2_grpc.RaftStub(channel)
        get_committed_cmd_request = raft_pb2.GetCommittedCmdRequest()
        status_reply = stub.GetCommittedCmd(get_committed_cmd_request)
        print(status_reply)

    # request: "append_entries"
    # def __send_request(self, request):
    #     replica = self.__choose_replica()
    #     with grpc.insecure_channel(replica) as channel:
    #         stub = raft_pb2_grpc.RaftStub(channel)
    #         stub.AppendEntries(request)

def activate_replica(replica_address: str):
    with grpc.insecure_channel(replica_address) as channel:
        stub = raft_pb2_grpc.RaftStub(channel)
        activate_replica_request = raft_pb2.ActivateServerRequest()
        status_reply = stub.Activate(activate_replica_request)
        print(status_reply)

def deactivate_replica(replica_address: str):
    with grpc.insecure_channel(replica_address) as channel:
        stub = raft_pb2_grpc.RaftStub(channel)
        activate_replica_request = raft_pb2.DeactivateServerRequest()
        status_reply = stub.Deactivate(activate_replica_request)
        print(status_reply)


if __name__ == '__main__':
    for i in range(5000,5003):
        with grpc.insecure_channel(f"localhost:{i}") as channel:
            stub = raft_pb2_grpc.RaftStub(channel)
            # get_committed_cmd_request = raft_pb2.GetCommittedCmdRequest()
            # vote_request = raft_pb2.RequestVoteRequest(term=1, candidateId=1, lastLogIndex=0, lastLogTerm=0)
            # get status request
            get_status_request = raft_pb2.GetStatusRequest()
            status_reply = stub.GetStatus(get_status_request)
            print(status_reply)
