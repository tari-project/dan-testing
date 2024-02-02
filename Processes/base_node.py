# -*- coding: utf-8 -*-

from grpc import insecure_channel  # type:ignore

from protos import types_pb2, base_node_pb2_grpc, base_node_pb2, network_pb2, block_pb2
from Common.config import TARI_BINS_FOLDER, NETWORK, REDIRECT_BASE_NODE_STDOUT, USE_BINARY_EXECUTABLE, DATA_FOLDER
import os
import re
import time
from typing import Iterator, Any
from Processes.common_exec import CommonExec


class GrpcBaseNode:
    def __init__(self, grpc_url: str):
        self.address = grpc_url
        self.channel = insecure_channel(self.address)
        self.stub = base_node_pb2_grpc.BaseNodeStub(self.channel)

    def get_version(self) -> str:
        request = types_pb2.Empty()
        return self.stub.GetVersion(request)  # type:ignore

    def get_mempool_stats(self) -> base_node_pb2.MempoolStatsResponse:
        request = types_pb2.Empty()
        return self.stub.GetMempoolStats(request)  # type:ignore

    def get_mempool_size(self) -> int:
        return self.get_mempool_stats().unconfirmed_txs

    def get_identity(self) -> network_pb2.NodeIdentity:
        request = types_pb2.Empty()
        return self.stub.Identify(request)  # type:ignore

    def get_public_key(self) -> bytes:
        return self.get_identity().public_key

    def get_public_addresses(self) -> list[str]:
        return self.get_identity().public_addresses  # type:ignore

    def get_tip_info(self) -> base_node_pb2.TipInfoResponse:
        request = types_pb2.Empty()
        return self.stub.GetTipInfo(request)  # type:ignore

    def get_tip(self) -> int:
        return self.get_tip_info().metadata.height_of_longest_chain

    def get_active_validator_nodes(self, height: int) -> base_node_pb2.GetActiveValidatorNodesResponse:
        request = base_node_pb2.GetActiveValidatorNodesRequest(height=height)
        return self.stub.GetActiveValidatorNodes(request)  # type:ignore

    def search_utxos(self, commitments: list[bytes]) -> block_pb2.HistoricalBlock:
        request = base_node_pb2.SearchUtxosRequest(commitments=commitments)
        return self.stub.SearchUtxos(request)  # type:ignore

    def get_signature(self, public_nonce: str | bytes, signature: str | bytes) -> types_pb2.Signature:
        if type(public_nonce) == str:
            public_nonce = bytes.fromhex(public_nonce)
        if type(signature) == str:
            signature = bytes.fromhex(signature)
        return types_pb2.Signature(public_nonce=public_nonce, signature=signature)  # type:ignore

    def search_kernels(self, signatures: list[types_pb2.Signature]) -> Iterator[block_pb2.HistoricalBlock]:
        request = base_node_pb2.SearchKernelsRequest(signatures=signatures)
        return self.stub.SearchKernels(request)  # type:ignore


class BaseNode(CommonExec):
    def __init__(self, id: int, local_ip: str, peer_seeds: list[str] = []):
        super().__init__("BaseNode", id)
        self.public_port = self.get_port("public_address")
        self.public_address = f"/ip4/{local_ip}/tcp/{self.public_port}"
        self.grpc_port = self.get_port("GRPC")
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_BINS_FOLDER, "minotari_node")]
        else:
            run = ["cargo", "run", "--bin", "minotari_node", "--manifest-path", os.path.join("..", "tari", "Cargo.toml"), "--"]
        self.exec = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, self.name),
            "-n",
            "--network",
            NETWORK,
            "--mining-enabled",
            "-p",
            "base_node.p2p.transport.type=tcp",
            "-p",
            f"base_node.p2p.transport.tcp.listener_address={self.public_address}",
            "-p",
            f"base_node.p2p.public_addresses={self.public_address}",
            "-p",
            f"base_node.grpc_address=/ip4/{local_ip}/tcp/{self.grpc_port}",
            "-p",
            f"base_node.grpc_enabled=true",
            "-p",
            "base_node.p2p.allow_test_addresses=true",
            "-p",
            "base_node.metadata_auto_ping_interval=3",
            "-p",
            "base_node.report_grpc_error=true",
        ]
        if peer_seeds:
            self.exec.append("-p")
            self.exec.append(f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peer_seeds)}")
        self.run(REDIRECT_BASE_NODE_STDOUT)
        # Sometimes it takes a while to establish the grpc connection
        while True:
            try:
                self.grpc_client = GrpcBaseNode(f"{local_ip}:{self.grpc_port}")
                self.grpc_client.get_version()
                break
            except Exception as e:
                print(e)
            time.sleep(1)

    def get_address(self) -> str:
        base_node_id_file_name = os.path.join(DATA_FOLDER, self.name, NETWORK, "config", "base_node_id.json")
        while not os.path.exists(base_node_id_file_name):
            time.sleep(1)
        f = open(base_node_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(r'"node_id":"(.*?)","public_key":"(.*?)".*"public_addresses":\["(.*?)"', content).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"

    def get_info_for_ui(self) -> dict[str, Any]:
        return {"name": self.name, "grpc": self.grpc_client.address, "address": self.get_address()}
