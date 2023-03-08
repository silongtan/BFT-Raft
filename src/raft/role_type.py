# from __future__ import annotations

from enum import Enum
from abc import ABC, abstractmethod
import rpc.raft_pb2 as raft_pb2
import rpc.raft_pb2_grpc as raft_pb2_grpc
from rpc_visitor import RPCVisitor


class RoleType(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


def dispatch(role: RoleType, visitor: RPCVisitor):
    switcher = {
        RoleType.FOLLOWER: _Follower,
        RoleType.CANDIDATE: _Candidate,
        RoleType.LEADER: _Leader,
    }
    func = switcher.get(role, lambda: "Invalid role")
    return func().accept(visitor)


class Role(ABC):
    def accept(self, visitor: RPCVisitor):
        pass


class _Follower(Role):
    def accept(self, visitor: RPCVisitor):
        return visitor.visit_follower()


class _Candidate(Role):
    def accept(self, visitor: RPCVisitor):
        return visitor.visit_candidate()


class _Leader(Role):
    def accept(self, visitor: RPCVisitor):
        return visitor.visit_leader()
