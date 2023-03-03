import rpc.raft_pb2
from rpc.raft_pb2_grpc import RaftServicer

class Raft(RaftServicer):
    pass



if __name__ == '__main__':
    Raft()