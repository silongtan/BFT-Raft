# BFT-Raft

## Overview
BFTRaft, a variant of the Raft consensus algorithm that is designed to be Byzantine Fault Tolerant. Our approach draws inspiration from both the original Raft algorithm and the Practical Byzantine Fault Tolerance algorithm, with the goal of maintaining the safety, fault tolerance, and liveness properties of Raft in the face of Byzantine faults. At the same time, we strive to preserve Raft’s simplicity and ease of understanding. To demonstrate the viability of our approach, we have implemented a proof-of- concept of BFTRaft using the Python programming language.


## Byzantine Problem in Raft
If there are nodes in the Raft system that are behaving in a Byzantine way, the safety and availability of the system are negatively impacted.  In a Byzantine setting, nodes can behave arbitrarily, including sending contradictory messages or intentionally trying to disrupt the log replication protocol. In such a scenario, the safety and consistency guarantees of Raft are compromised. Therefore, Raft's log replication mechanism is not Byzantine fault-tolerant, and additional mechanisms are needed to handle Byzantine failures.

## Achieve Byzantine Fault Tolerant
### Message Signatures
To prevent a Byzantine leader from tampering with the data or forging messages, BFT Raft uses digital signatures extensively. Specifically, when a client sends a request to the leader, it includes a signature generated using its private key. The leader then replicates the message along with the client's signature, ensuring that any changes made to the message will invalidate the signature. This means that any tampering by a malicious leader will be detected by the replicas.

### Client intervention
BFT Raft permits clients to intervene and replace the current leader if it fails to make progress. This feature prevents Byzantine leaders from monopolizing the system and causing it to become unresponsive.

### Incremental hashing
Whenever a new entry is added to the log, the replica computes a cryptographic hash function over the previous hash and the newly appended log entry. The resulting hash value represents a unique fingerprint of the entire log, which includes the new entry.

This approach ensures that the replicas in the system have the same view of the state of the system and that no malicious replicas can modify the log without detection. It also provides a way for replicas to catch up quickly after recovering from a failure, as they only need to synchronize their log with a trusted replica and verify the hash values and signatures.

### Election verification
When a node becomes the leader in BFT Raft, its first action is to send AppendEntries Remote Procedure Call (RPC) messages to each of the other nodes in the system. These AppendEntries messages contain a quorum of RequestVoteResponse RPC messages that the node received during the election process, which led to its selection as the leader.

Digital signatures are used to validate the RequestVoteResponses that are included in the AppendEntries RPC message sent by an elected leader. Specifically, RSA is used as the signature algorithm.

### Lazy Voters
In BFT Raft, a node does not grant its vote to a candidate unless it believes that the current leader is dead. A node determines that its leader is dead if it does not receive a heartbeat from the leader within its own election timeout.

By requiring a node to believe that the current leader is dead before granting its vote to a candidate, BFT Raft prevents nodes from starting unnecessary elections and gaining the requisite votes to become the leader. This helps to avoid situations where a malicious node tries to starve the system by constantly triggering elections and preventing progress from being made.

