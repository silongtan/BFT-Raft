from enum import Enum
import rpc.raft_pb2 as raft_pb2
import grpc
from config import *
from random import randrange
import logging
import rpc.raft_pb2_grpc as raft_pb2_grpc
import threading


class RoleType(Enum):
    FOLLOWER = 'follower'
    CANDIDATE = 'candidate'
    LEADER = 'leader'

    def __str__(self):
        return str(self.value)


def dispatch(server):
    switcher = {
        RoleType.FOLLOWER: _Follower,
        RoleType.CANDIDATE: _Candidate,
        RoleType.LEADER: _Leader,
    }
    func = switcher.get(server.role, lambda: "Invalid role")
    return func(server)


class _Role:
    def __init__(self, server):
        self.server = server

    # def vote(self, request, context) -> raft_pb2.RequestVoteReply:
    #     pass
    #
    # def ask_vote(self, address: str):
    #     pass




class _Follower(_Role):
    def run(self):
        pass

    def vote(self, request, context) -> raft_pb2.RequestVoteReply:
        should_vote = False
        candidate_term = request.term
        # vote for the candidate with the higher term
        if self.server.term < candidate_term:
            self.server.term = request.term
            should_vote = True
            self.server.vote_for = request.candidateId
            # self.server.role = RoleType.FOLLOWER
            self.server.become(RoleType.FOLLOWER)
        elif self.server.term == candidate_term:
            if self.server.vote_for

        else:
        # reset_timer(leader_die,HEARTBEAT_INTERVAL)

        reply = {'term': self.server.term, 'voteMe': should_vote}
        return raft_pb2.RequestVoteReply(**reply)


class _Candidate(_Role):
    def run(self):
        self.server.term +=1
        self.server.votes_granted = 1
        self.server.vote_for = self.server.id

        barrier = threading.Barrier(self.server.majority - 1)

        for key,value in self.server.all_address.items():
            if key != self.server.address:
                candidate_thread = threading.Thread(target=self.ask_vote,args=(value,barrier))

    def ask_vote(self, address: str,barrier:threading.Barrier):
        try:
            with grpc.insecure_channel(address) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                args = {'term': self.server.term,
                        'candidateId': self.server.id,
                        'lastLogIndex': self.server.last_log_index,
                        'lastLogTerm': self.server.last_log_term}
                request = raft_pb2.RequestVoteRequest(**args)
                response = stub.RequestVote(request)
                if response.voteMe:
                    self.server.votes_granted += 1
                # TODO:不确定
                if response.term > self.server.term:
                    self.server.term = response.term
                    self.server.become(RoleType.FOLLOWER)
                    self.server.vote_for = -1
                    self.server.votes_granted = 0
                    self.server.timeout = float(randrange(ELECTION_TIMEOUT_MAX // 2, ELECTION_TIMEOUT_MAX) / 1000)

        except grpc.RpcError:
            logging.error("connection error")


class _Leader(_Role):
    def run(self):
        pass
