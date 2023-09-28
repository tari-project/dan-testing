from Processes.base_node import base_node
from Processes.miner import miner
from Processes.dan_wallet_daemon import DanWalletDaemon
from Processes.indexer import Indexer
from Processes.miner import Miner
from Processes.signaling_server import SignalingServer
from Stats.stats import stats
from Processes.tari_connector_sample import TariConnectorSample
from Processes.template import Template
from Processes.template_server import Server
from Processes.wallet import wallet
from Common.threads import threads
from Processes.validator_node import ValidatorNode
from Processes.wallet import Wallet
from typing import Optional
from Collections.validator_nodes import validator_nodes
from Collections.indexers import indexers
from Collections.dan_wallet_daemons import dan_wallets
from Common.local_ip import local_ip
import os
import base64
import json


class Commands:
    def __init__(
        self,
        tari_connector_sample: TariConnectorSample,
        server: Server,
        signaling_server: SignalingServer,
    ) -> None:
        self.miner = miner
        self.tari_connector_sample = tari_connector_sample
        self.server = server
        self.signaling_server = signaling_server
        self.indexers = indexers
        self.dan_wallets = dan_wallets
        self.validator_nodes = validator_nodes

    def burn(self, public_key: str, outfile: str, amount: int):
        public_key_bytes = bytes([int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2)])
        print(f"BURNING {amount}")
        burn = wallet.grpc_client.burn(amount, public_key_bytes)
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

    def grpc(self, what: str) -> Optional[str]:
        if what == "node":
            return f"{local_ip}:{base_node.grpc_port}"
        if what == "wallet":
            return f"{local_ip}:{wallet.grpc_port}"
        return None

    def jrpc_vn(self, index: int) -> Optional[str]:
        return self.validator_nodes.jrpc_vn(index)

    def jrpc_dan(self, index: int) -> Optional[str]:
        if index in self.dan_wallets:
            return f"{local_ip}:{dan_wallets[index].json_rpc_port}"
        return None

    def jrpc_indexer(self, index: int) -> Optional[str]:
        if index in self.indexers:
            return f"{local_ip}:{indexers[index].json_rpc_port}"
        return None

    def jrpc_signaling(self) -> str:
        return f"{local_ip}:{self.signaling_server.json_rpc_port}"

    def http_vn(self, index: int) -> Optional[str]:
        return self.validator_nodes.http_vn(index)

    def http_dan(self, index: int) -> Optional[str]:
        if index in self.dan_wallets:
            return f"http://{self.dan_wallets[index].http_ui_address}"
        return None

    def http_indexer(self, index: int) -> Optional[str]:
        if index in self.indexers:
            return f"http://{self.indexers[index].http_ui_address}"
        return None

    def http_connector(self) -> str:
        try:
            return f"http://{local_ip}:{self.tari_connector_sample.http_port}"
        except:
            return ""
