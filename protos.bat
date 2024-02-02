pip install grpcio-tools
mkdir protos
python -m grpc_tools.protoc --proto_path ../tari/applications/minotari_app_grpc/proto/  --python_out=./protos --grpc_python_out=./protos ../tari/applications/minotari_app_grpc/proto/*.proto --pyi_out=./protos
