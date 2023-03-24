import random
import grpc
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc


class Client:

    def __init__(self, replicas: list):
        self.raft_replicas = replicas
        self.stubs = {}
        for replica in self.raft_replicas:
            self.stubs[replica] = grpc.insecure_channel(replica)

    def __choose_replica(self) -> str:
        return random.choice(self.raft_replicas)

    # append_entries
    def send_new_command(self, request: str):
        replica = self.__choose_replica()
        print(replica)
        with grpc.insecure_channel(replica) as channel:
            # stub = self.stubs[replica]
            stub = raft_pb2_grpc.RaftStub(channel)
            new_command_request = raft_pb2.NewCommandRequest(command=request)
            status_reply = stub.NewCommand(new_command_request)
            print(status_reply)
            # print(status_reply.log)

    def send_get_status(self):
        replica = self.__choose_replica()
        with grpc.insecure_channel(replica) as channel:
            stub = raft_pb2_grpc.RaftStub(channel)
            get_status_request = raft_pb2.GetStatusRequest()
            status_reply = stub.GetStatus(get_status_request)
            print(status_reply)

    @staticmethod
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


if __name__ == '__main__':
    client = Client(["localhost:5000"])
    # client.send_new_command("test")
    # client.send_get_status()
    # client.send_get_committed_cmd("localhost:5000")
    with grpc.insecure_channel("localhost:5001") as channel:
        stub = raft_pb2_grpc.RaftStub(channel)
        # get_committed_cmd_request = raft_pb2.GetCommittedCmdRequest()
        vote_request = raft_pb2.RequestVoteRequest(term=1, candidateId=1, lastLogIndex=0, lastLogTerm=0)
        status_reply = stub.RequestVote(vote_request)
        print(status_reply)
