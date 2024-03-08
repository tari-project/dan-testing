from Processes.miner import miner
from Processes.signaling_server import SignalingServer
from Processes.tari_connector_sample import TariConnectorSample
from Processes.template_server import Server
from Processes.common_exec import all_processes
from typing import Optional
from Collections.base_wallets import base_wallets
from Collections.validator_nodes import validator_nodes
from Collections.indexers import indexers
from Collections.dan_wallet_daemons import dan_wallets
from Collections.base_nodes import base_nodes
from Common.local_ip import local_ip
from template_web import TemplateWebServer
import os
import base64
import json
import process_type


class Commands:
    def __init__(
        self,
        tari_connector_sample: Optional[TariConnectorSample],
        template_web_server: Optional[TemplateWebServer],
        server: Server,
        signaling_server: SignalingServer,
    ) -> None:
        self.miner = miner
        self.tari_connector_sample = tari_connector_sample
        self.template_web_server = template_web_server
        self.server = server
        self.signaling_server = signaling_server
        self.indexers = indexers
        self.dan_wallets = dan_wallets
        self.validator_nodes = validator_nodes
        self.base_nodes = base_nodes
        self.base_wallets = base_wallets

    def burn(self, public_key: str, outfile: str, amount: int):
        public_key_bytes = bytes([int(public_key[i : i + 2], 16) for i in range(0, len(public_key), 2)])
        print(f"BURNING {amount}")
        burn = base_wallets.any().grpc_client.create_burn_transaction(amount, public_key_bytes)
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

    def start(self, what: str) -> bool:
        if what not in all_processes:
            return False
        return all_processes[what].run()

    def stop(self, what: str) -> bool:
        if what not in all_processes:
            return False
        return all_processes[what].stop()

    def is_running(self, what: str) -> bool:
        if what not in all_processes:
            return False
        return all_processes[what].is_running()

    def grpc(self, what: str) -> Optional[str]:
        id = process_type.get_index(what)
        if process_type.is_base_node(what):
            if id is not None and self.base_nodes.has(id):
                return self.base_nodes[id].grpc_client.address
        if process_type.is_base_wallet(what):
            if id is not None and self.base_wallets.has(id):
                return self.base_nodes[id].grpc_client.address

    def jrpc(self, what: str) -> Optional[str]:
        id = process_type.get_index(what)
        if id is not None:
            if process_type.is_validator_node(what):
                return self.validator_nodes.jrpc(id)
            if process_type.is_indexer(what):
                return self.indexers.jrpc(id)
            if process_type.is_asset_wallet(what):
                return self.dan_wallets.jrpc(id)
        if process_type.is_signaling_server(what):
            return f"{local_ip}:{self.signaling_server.json_rpc_port}"
        return None

    def http(self, what: str) -> Optional[str]:
        id = process_type.get_index(what)
        if id is not None:
            if process_type.is_validator_node(what):
                return self.validator_nodes.http(id)
            if process_type.is_indexer(what):
                return self.indexers.http(id)
            if process_type.is_asset_wallet(what):
                return self.dan_wallets.http(id)
        if process_type.is_connector(what):
            if self.tari_connector_sample:
                return f"http://{local_ip}:{self.tari_connector_sample.http_port}"
        if process_type.is_template_web(what):
            if self.template_web_server:
                return f"http://{local_ip}:{self.template_web_server.http_port}"
        return None
