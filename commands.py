from base_node import BaseNode
from dan_wallet_daemon import DanWalletDaemon
from indexer import Indexer
from miner import Miner
from signaling_server import SignalingServer
from stats import stats
from tari_connector_sample import TariConnectorSample
from template import Template
from template_server import Server
from threads import threads
from validator_node import ValidatorNode
from wallet import Wallet
from typing import Optional
import os
import base64
import json


class Commands:
    def __init__(
        self,
        local_ip: str,
        wallet: Wallet,
        base_node: BaseNode,
        miner: Miner,
        dan_wallets: dict[int, DanWalletDaemon],
        indexers: dict[int, Indexer],
        validator_nodes: dict[int, ValidatorNode],
        tari_connector_sample: TariConnectorSample,
        server: Server,
        signaling_server: SignalingServer,
    ) -> None:
        self.local_ip = local_ip
        self.wallet = wallet
        self.base_node = base_node
        self.miner = miner
        self.dan_wallets = dan_wallets
        self.indexers = indexers
        self.validator_nodes = validator_nodes
        self.tari_connector_sample = tari_connector_sample
        self.server = server
        self.signaling_server = signaling_server

    def burn(self, public_key: str, outfile: str, amount: int):
        public_key_bytes = bytes([int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2)])
        print(f"BURNING {amount}")
        burn = self.wallet.grpc_client.burn(amount, public_key_bytes)
        os.mkdir("output")

        with open("output/" + outfile, "w") as f:
            claim_proof = {
                "commitment": base64.b64encode(burn.commitment).decode("utf-8"),
                "range_proof": base64.b64encode(burn.range_proof).decode("utf-8"),
                "reciprocal_claim_public_key": base64.b64encode(burn.reciprocal_claim_public_key).decode("utf-8"),
                "ownership_proof": {
                    "u": base64.b64encode(burn.ownership_proof.u).decode("utf-8"),
                    "v": base64.b64encode(burn.ownership_proof.v).decode("utf-8"),
                    "public_nonce": base64.b64encode(burn.ownership_proof.public_nonce).decode("utf-8"),
                },
            }

            json.dump(claim_proof, f)
        print("written to file", outfile)

    def mine(self, blocks: int):
        self.miner.mine(blocks)  # Mine the register TXs

    def grpc(self, what: str) -> Optional[int]:
        if what == "node":
            return self.base_node.grpc_port
        if what == "wallet":
            return self.wallet.grpc_port
        return None

    def jrpc_vn(self, index: int) -> Optional[str]:
        if index in self.validator_nodes:
            return f"{self.local_ip}:{self.validator_nodes[index].json_rpc_port}"
        return None

    def jrpc_dan(self, index: int) -> Optional[str]:
        if index in self.dan_wallets:
            return f"{self.local_ip}:{self.dan_wallets[index].json_rpc_port}"
        return None

    def jrpc_indexer(self, index: int) -> Optional[str]:
        if index in self.indexers:
            return f"{self.local_ip}:{self.indexers[index].json_rpc_port}"
        return None

    def jrpc_signaling(self) -> str:
        return f"{self.local_ip}:{self.signaling_server.json_rpc_port}"

    def http_vn(self, index: int) -> Optional[str]:
        if index in self.validator_nodes:
            return f"http://{self.validator_nodes[index].http_ui_address}"
        return None

    def http_dan(self, index: int) -> Optional[str]:
        if index in self.dan_wallets:
            return f"http://{self.dan_wallets[index].http_ui_address}"
        return None

    def http_indexer(self, index: int) -> Optional[str]:
        if index in self.indexers:
            return f"http://{self.indexers[index].http_ui_address}"
        return None

    def http_connector(self) -> str:
        return f"http://{self.local_ip}:{self.tari_connector_sample.http_port}"
