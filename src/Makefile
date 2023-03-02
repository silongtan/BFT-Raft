proto:
	python -m grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. protos/greet.proto

server:
	python3 rpc/server.py

client:
	python3 rpc/client.py