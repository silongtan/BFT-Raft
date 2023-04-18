import asyncio
import time
from enum import Enum

import grpc
from config import *
from random import randrange
import logging
# import rpc.raft_pb2 as raft_pb2
# import rpc.raft_pb2_grpc as raft_pb2_grpc
import threading
import rpc.bft_raft_pb2 as raft_pb2
import rpc.bft_raft_pb2_grpc as raft_pb2_grpc

import json


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

    # handle receive
    def resend_vote_reply(self, delay_vote: dict):
        pass

    def vote(self, request, context) -> raft_pb2.RequestVoteReply:
        if self.server.active is False:
            print(self.server.address, "replica is not active and can't vote")
            return
        self.server.reset_timer(self.server.leader_died, self.server.timeout)
        reply = {'term': self.server.term, 'voteMe': False, 'isValid': True}
        return raft_pb2.RequestVoteReply(**reply)

    # handle receive
    # TODO:If AppendEntries RPC received from new leader: convert to
    # follower
    def append_entries(self, request, context) -> raft_pb2.AppendEntriesReply:
        # pass
        if self.server.active is False:
            print(self.server.address, "replica is not active and can't append entries")
            return
        leader_term = request.term
        leader_id = request.leaderId
        prev_log_index = request.prevLogIndex
        prev_log_term = request.prevLogTerm
        leader_commit_index = request.leaderCommitIndex or 0
        success = False

        # print(len(request.signedVote) + 1)
        # print(self.server.majority)
        if len(request.signedVote) + 1 < self.server.majority:
            # print("request.signedVote:::", len(request.signedVote))
            reply = {"term": self.server.term, "success": False}
            # print("never reach!!!!!!!!!")
            return raft_pb2.AppendEntriesReply(**reply)

        # print(leader_id, self.server.vote_for)
        # if leader_id != self.server.vote_for:
        #     print('hhhhhhhhhhhh')
        #     reply = {"term": self.server.term, "success": False}
        #     # print("never reach!!!!!!!!!")
        #     return raft_pb2.AppendEntriesReply(**reply)

        # check integrity
        # for vote in request.signedVote:
        #     vote_from = vote.voteFrom
        #     vote_for = vote.voteFor
        #     signature = vote.signature
        #     if not self.server.verify_msg(leader_term, leader_id, vote_from, vote_for, signature):
        #         raise Exception("invalid signature")
        #         reply = {"term": self.server.term, "success": False}
        #         print("never reach!!!!!!!!!")
        #         return raft_pb2.AppendEntriesReply(**reply)

        self.server.isLeaderDead = False
        # print("reaching here")
        if leader_term < self.server.term:
            success = False
        else:
            # print("this is because leader send append entries to cause this server become follower")
            with self.server.lock:
                current_role = self.server.role

            if current_role != RoleType.FOLLOWER:
                print(self.server.address,
                      "this is because leader send append entries to cause this server become follower, previous role type is: ",
                      self.server.role)
                self.server.become(RoleType.FOLLOWER)
            else:
                print(self.server.address, " this is still follower")
                self.server.reset_timer(self.server.leader_died, self.server.timeout)

            if prev_log_index == -1:
                success = True
                # self.server.log = request.entries
                self.server.log = [{'term': r.term, 'command': r.command} for r in request.entries]
            elif prev_log_term == self.server.log[prev_log_index].get('term') and len(self.server.log) > prev_log_index:
                success = True
                self.server.log = self.server.log[:prev_log_index + 1] + [{'term': r.term, 'command': r.command} for r
                                                                          in request.entries]
        if leader_commit_index > self.server.committed_index:
            # print('leader_commit_index > self.server.committed_index', leader_commit_index, self.server.committed_index)
            # print('leader_commit_index', leader_commit_index)
            # print('len(self.server.log) - 1', len(self.server.log) - 1)
            self.server.committed_index = min(leader_commit_index, len(self.server.log) - 1)
            print('committed_index', self.server.committed_index)
            self.server.apply_log(self.server.committed_index)
        if leader_term > self.server.term:
            self.server.term = leader_term

        self.server.reset_timer(self.server.leader_died, self.server.timeout)
        reply = {"term": self.server.term, "success": success}
        return raft_pb2.AppendEntriesReply(**reply)


class _Follower(_Role):
    def run(self):
        # print('test')f
        self.server.delay_vote = None
        self.server.vote_for = -1
        self.server.votes_granted = 0
        self.server.signed_votes = []
        self.server.reset_timeout()
        self.server.reset_timer(self.server.leader_died, self.server.timeout)
        # self.server.reset_timer(lambda: print("reachingiiiiiiiii"), self.server.timeout)

    def resend_vote_reply(self, delay_vote: dict):
        print('resend')
        # send revote reply
        # msg = str(delay_vote.get('candidate_term')) + " " + str(
        #     delay_vote.get('candidate_id')) + " " + self.server.address + " localhost:" + str(
        #     delay_vote.get('candidate_id'))
        # print('resend_vote_reply  delay_vote', delay_vote)
        # print(msg)
        # reply = {'term': self.server.term, 'voteMe': True, 'signature': self.server.sign_msg(msg),
        #          'voteFrom': self.server.address, 'voteFor': 'localhost:' + str(delay_vote.get('candidate_id')),
        #          'isValid': True}
        # try:
        #     with grpc.insecure_channel(delay_vote.get('voteFor')) as channel:
        #         stub = raft_pb2_grpc.RaftStub(channel)
        #         request = raft_pb2.RequestVoteReply(**delay_vote, isValid=True)
        #         response = stub.ReSendVoteReply(request)
        # except grpc.RpcError as e:
        #     print("connection error", e)
        #     logging.error("connection error")

    def vote(self, request, context) -> raft_pb2.RequestVoteReply:
        if self.server.active is False:
            print(self.server.address, "follower is not active and can't append vote")
            return
        should_vote = False
        candidate_id = request.candidateId
        candidate_term = request.term
        candidate_last_log_index = request.lastLogIndex
        # if not self.server.isLeaderDead:
        #     reply = {'term': self.server.term, 'voteMe': False, 'signature': None,
        #              'voteFrom': self.server.address, 'voteFor': 'localhost:' + str(candidate_id)}
        #     # print('server'+self.server.)
        #     return raft_pb2.RequestVoteReply(**reply)
        # vote for the candidate with the higher term
        # if self.server.delay_vote is not None:
        #     reply = {'term': self.server.term, 'voteMe': False, 'signature': None,
        #              'voteFrom': self.server.address, 'voteFor': 'localhost:' + str(candidate_id),
        #              'isValid': True}
        #     # print('server'+self.server.)
        #     return raft_pb2.RequestVoteReply(**reply)

        if candidate_term < self.server.term:
            should_vote = False
        else:
            if self.server.vote_for == -1 or self.server.vote_for == candidate_id:
                if candidate_last_log_index >= self.server.get_last_log_index():
                    should_vote = True
                    self.server.vote_for = candidate_id
                    self.server.term = candidate_term
                    # TODO:
                    # self.server.become(RoleType.FOLLOWER)
                    self.server.reset_timer(self.server.leader_died, self.server.timeout)

        if should_vote:
            self.server.reset_timer(self.server.leader_died, self.server.timeout)

        msg = str(candidate_term) + " " + str(candidate_id) + " " + self.server.address + " localhost:" + str(
            candidate_id)
        reply = {'term': self.server.term, 'voteMe': should_vote, 'signature': self.server.sign_msg(msg),
                 'voteFrom': self.server.address, 'voteFor': 'localhost:' + str(candidate_id)}

        if should_vote:
            self.server.reset_timer(self.server.leader_died, self.server.timeout)

        # if not self.server.isLeaderDead:
        #     reply['voteMe'] = False
        #     return raft_pb2.RequestVoteReply(**reply)
        # time.sleep(3)
        # raft_pb2.RequestVoteReply(**reply).Re, self.server.timeout)
        # threading.Timer(3, lambda: raft_pb2.RequestVoteReply(**reply)).start()
        if reply['voteMe']:
            # self.server.delay_vote = reply
            return raft_pb2.RequestVoteReply(**reply, isValid=True)
        else:
            return raft_pb2.RequestVoteReply(**reply, isValid=True)

    # def send_vote_reply(self, request, context):
    #     should_vote = False
    #     candidate_id = request.candidateId
    #     candidate_term = request.term
    #     msg = str(candidate_term) + " " + str(candidate_id) + " " + self.server.address + " localhost:" + str(
    #         candidate_id)
    #     reply = {'term': self.server.term, 'voteMe': should_vote, 'signature': self.server.sign_msg(msg),
    #              'voteFrom': self.server.address, 'voteFor': 'localhost:' + str(candidate_id)}
    #     return raft_pb2.RequestVoteReply(**reply)

    # def append_entries(self, request, context) -> raft_pb2.AppendEntriesReply:
    #     leader_term = request.term
    #     leader_id = request.leaderId
    #     prev_log_index = request.prevLogIndex
    #     prev_log_term = request.prevLogTerm
    #     leader_commit_index = request.leaderCommitIndex
    #     success = False
    #     self.server.reset_timeout()
    #     if leader_term < self.server.term:
    #         return raft_pb2.AppendEntriesReply(term=self.server.term, success=False)
    #     # TODO:


class _Candidate(_Role):
    # TODO: barrier
    def run(self):
        self.server.term += 1
        self.server.votes_granted = 1
        self.server.vote_for = self.server.id
        self.server.signed_votes = []
        self.server.reset_timeout()

        # barrier = threading.Barrier(self.server.majority - 1, timeout=self.server.timeout)
        barrier = None
        self.server.reset_timer(self.process_vote, self.server.timeout)
        for value in self.server.peers:
            self.ask_vote(value, barrier)
            # asyncio.run(self.ask_vote(value, barrier))
        # threading.Thread(target=self.ask_vote,args=(value,barrier)).start()
        # self.server.reset_timer(self.process_vote, self.server.timeout)

    # TODO: barrier

    def ask_vote(self, address: str, barrier: threading.Barrier):
        if self.server.active is False:
            print(self.server.address, "candidate is not active and can't ask entries")
            return
        print(self.server.address, 'ask vote', address)
        try:
            with grpc.insecure_channel(address) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)
                args = {'term': self.server.term,
                        'candidateId': self.server.id,
                        'lastLogIndex': self.server.get_last_log_index(),
                        'lastLogTerm': self.server.get_last_log_term()}
                request = raft_pb2.RequestVoteRequest(**args)
                response = stub.RequestVote(request)
                if not response.isValid:
                    print('waiting for another vote when leader died, reset timer')
                    # self.server.reset_timer(self.process_vote, self.server.timeout)
                    self.server.election_timer.cancel()
                    return
                # response = stub.RequestVote.future(request).result()
                # print("vote response", response)
                if response.voteMe:
                    self.server.votes_granted += 1
                    # print('append', response)
                    self.server.signed_votes.append(response)
                    if self.server.votes_granted >= self.server.majority:
                        self.server.become(RoleType.LEADER)

                if response.term > self.server.term:
                    self.server.term = response.term
                    self.server.become(RoleType.FOLLOWER)
                    self.server.vote_for = -1
                    self.server.votes_granted = 0
                    self.server.timeout = float(
                        randrange(ELECTION_TIMEOUT_MAX_MILLIS // 2, ELECTION_TIMEOUT_MAX_MILLIS) / 1000)
                    self.server.reset_timer(self.server.leader_died, self.server.timeout)
        except grpc.RpcError as e:
            print("connection error", e)
            logging.error("connection error")

    def process_vote(self):
        if self.server.active is False:
            print(self.server.address, "replica is not active and can't process vote")
            return
        print(self.server.address, "process vote, votes_granted", self.server.votes_granted, self.server.address)
        if self.server.votes_granted >= self.server.majority:
            # logging.info("become leader")
            self.server.become(RoleType.LEADER)
        else:
            print(self.server.address, "process vote fail, become follower")
            self.server.become(RoleType.CANDIDATE)


# def append_entries(self, request, context) -> raft_pb2.AppendEntriesReply:
#     leader_term = request.term
#     leader_id = request.leaderId
#     prev_log_index = request.prevLogIndex
#     prev_log_term = request.prevLogTerm
#     leader_commit_index = request.leaderCommitIndex
#
#     if leader_term > self.server.term:
#         print(0)
#         self.server.become(RoleType.FOLLOWER)
#     elif prev_log_term > self.server.get_last_log_term():
#         print(1)
#         self.server.become(RoleType.FOLLOWER)
#     elif prev_log_term == self.server.get_last_log_term() and prev_log_index >= self.server.get_last_log_index():
#         print(2)
#         self.server.become(RoleType.FOLLOWER)
#     return raft_pb2.AppendEntriesReply(term=self.server.term, success=False)


class _Leader(_Role):
    def run(self):
        if self.server.active is False:
            print(self.server.address, "leader is not active and can't run")
            return
        print(self.server.address, "I am leader leading in term:", self.server.term)
        self.server.next_index = {key: len(self.server.log) for key in self.server.peers}
        self.server.match_index = {key: -1 for key in self.server.peers}

        # TODO: heartbeat
        self.broadcast_append_entries()

    def broadcast_append_entries(self):
        # TODO: multi-thread
        if self.server.active is False:
            print(self.server.address, "leader is not active and can't broadcast append entries")
            return
        self.server.reset_timer(self.broadcast_append_entries, HEARTBEAT_INTERVAL_SECONDS)
        for value in self.server.peers:
            self.send_append_entries(value)

    def send_append_entries(self, address: str):
        if self.server.active is False:
            print(self.server.address, "leader is not active and can't send append entries")
            return
        with self.server.lock:
            # print(self.server.address, "broadcast append entries to ", address)
            current_role = self.server.role
        if current_role != RoleType.LEADER:
            return
        try:
            with grpc.insecure_channel(address) as channel:
                stub = raft_pb2_grpc.RaftStub(channel)

                prev_log_index = self.server.next_index[address] - 1
                # print()
                # print('print(prev_log_index)',prev_log_index)
                entries = self.server.log[self.server.next_index[address]:]
                entries = [raft_pb2.LogEntry(term=entry.get('term'), command=entry.get('command')) for entry in entries]
                # print('prev_log_index: ', prev_log_index)
                # print('tttttt: ', self.server.log, )
                # if prev_log_index != -1:
                #     print('self.server.log[prev_log_index]', self.server.log[prev_log_index])
                # print('self.server.log[prev_log_index].term if prev_log_index != -1 else 0:',
                #       self.server.log[prev_log_index].get('term') if prev_log_index != -1 else 0)
                args = {'term': self.server.term,
                        'leaderId': self.server.id,
                        'prevLogIndex': prev_log_index,
                        'prevLogTerm': self.server.log[prev_log_index].get('term') if prev_log_index != -1 else 0,
                        # 'entries': entries,
                        'leaderCommitIndex': self.server.committed_index, }
                # args['entries']
                # 'signedVote': self.server.signed_votes}
                # print(self.server.signed_votes)
                # if DEBUG:
                #     if len(entries) > 0:
                #         logging.debug(self.server.id, "send append entries to nextIndex[i]",
                #                       self.server.next_index[address],
                #                       "with args", json.dumps(args,indent=4), "to", address)
                #     else:
                #         logging.debug(str(self.server.id) + " send heartbeat to" + address)
                # print(self.server.address,'signedVote', self.server.signed_votes)
                request = raft_pb2.AppendEntriesRequest(**args)
                request.entries.extend(entries)
                request.signedVote.extend(self.server.signed_votes)
                # print("request.signedVote", request.signedVote)
                response = stub.AppendEntries(request)
                if response.term > self.server.term:
                    print(self.server.address, "will become follower, other is in term: ", response.term,
                          "I am in term: ", self.server.term)
                    self.server.term = response.term
                    self.server.become(RoleType.FOLLOWER)
                    return
                if not response.success:
                    if self.server.next_index[address] > 0:
                        self.server.next_index[address] -= 1
                else:
                    # TODO
                    self.server.next_index[address] += len(entries)
                    self.server.match_index[address] = self.server.next_index[address] - 1
                for i in range(self.server.committed_index + 1, len(self.server.log)):
                    if self.server.log[i].get('term') == self.server.term:
                        count = 1
                        for value in self.server.match_index.values():
                            if value >= i:
                                count += 1
                        if count >= self.server.majority:
                            print('committed')
                            self.server.committed_index = i
                            self.server.apply_log(self.server.committed_index)

        except grpc.RpcError as e:
            print("connection error", e)
            logging.error("connection error")
