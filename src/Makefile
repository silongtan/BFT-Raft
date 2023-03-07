# grpc.py file import path is not correct generated
proto:
	python -m grpc_tools.protoc -I rpc/protos --python_out=rpc/ --grpc_python_out=rpc/ rpc/protos/raft.proto

server:
	python3 rpc/server.py

client:
	python3 rpc/client.py