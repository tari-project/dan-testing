# type:ignore

from Common.config import TARI_DAN_BINS_FOLDER, NETWORK, REDIRECT_INDEXER_STDOUT, USE_BINARY_EXECUTABLE, DATA_FOLDER
from Common.ports import ports
import os
import time
import re
import requests
from Common.local_ip import local_ip
from Processes.subprocess_wrapper import SubprocessWrapper
from Processes.common_exec import CommonExec


class Indexer(CommonExec):
    def __init__(self, indexer_id: int, base_node_grpc_port: int, peers=[]):
        super().__init__("Indexer", indexer_id)
        self.id = indexer_id
        self.public_port = self.get_port("public_address")
        self.public_adress = f"/ip4/{local_ip}/tcp/{self.public_port}"
        self.json_rpc_port = self.get_port("JRPC")
        self.json_connect_address = f"{local_ip}:{self.json_rpc_port}"
        self.json_listen_address = f"0.0.0.0:{self.json_rpc_port}"
        self.http_port = self.get_port("HTTP")
        self.http_connect_address = f"{local_ip}:{self.http_port}"
        self.http_listen_address = f"0.0.0.0:{self.http_port}"
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_DAN_BINS_FOLDER, "tari_indexer")]
        else:
            run = [
                "cargo",
                "run",
                "--bin",
                "tari_indexer",
                "--manifest-path",
                os.path.join("..", "tari-dan", "Cargo.toml"),
                "--",
            ]
        self.exec = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, f"indexer_{self.id}"),
            "--log_config",
            os.path.join(DATA_FOLDER, f"indexer_{self.id}"),
            "--network",
            NETWORK,
            "-p",
            f"indexer.base_node_grpc_address={local_ip}:{base_node_grpc_port}",
            # "-p",
            # "indexer.p2p.transport.type=tcp",
            # "-p",
            # f"indexer.p2p.transport.tcp.listener_address={self.public_adress}",
            # "-p",
            # "indexer.p2p.allow_test_addresses=true",
            "-p",
            f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peers)}",
            # "-p",
            # f"indexer.p2p.public_addresses={self.public_adress}",
            "-p",
            f"indexer.json_rpc_address={self.json_listen_address}",
            "-p",
            f"indexer.http_ui_address={self.http_listen_address}",
            "-p",
            f"indexer.ui_connect_address=http://{self.json_connect_address}",
        ]
        self.run(REDIRECT_INDEXER_STDOUT)
        self.jrpc_client = JrpcIndexer(f"http://{self.json_connect_address}")
        while not os.path.exists(os.path.join(DATA_FOLDER, f"indexer_{self.id}", "localnet", "pid")):
            if self.process.poll() is None:
                time.sleep(1)
            else:
                raise Exception(f"Indexer did not start successfully: Exit code:{self.process.poll()}")
        print(f"Indexer {self.id} started")

    def get_address(self):
        if NETWORK == "localnet":
            indexer_id_file_name = os.path.join(DATA_FOLDER, f"indexer_{self.id}", "indexer_id.json")
        else:
            indexer_id_file_name = os.path.join(DATA_FOLDER, f"indexer_{self.id}", f"indexer_id_{NETWORK}.json")
        while not os.path.exists(indexer_id_file_name):
            time.sleep(1)
        f = open(indexer_id_file_name, "rt")
        content = "".join(f.readlines())
        node_id, public_key, public_address = re.search(r'"node_id":"(.*?)","public_key":"(.*?)".*"public_address":"(.*?)"', content).groups()
        public_address = public_address.replace("\\/", "/")
        return f"{public_key}::{public_address}"

    def get_info_for_ui(self):
        return {"http": self.http_connect_address, "jrpc": self.json_connect_address}


class JrpcIndexer:
    def __init__(self, jrpc_url):
        self.url = jrpc_url

    def call(self, method, params=[]):
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": 1, "params": params})
        if "error" in response.json():
            raise Exception(response.json()["error"])
        return response.json()["result"]

    def get_connections(self):
        self.call("get_connections")

    def get_comms_stats(self):
        self.call("get_comms_stats")

    def get_substate(self, address: str, version: int):
        return self.call("get_substate", [address, version])

    def get_epoch_manager_stats(self):
        return self.call("get_epoch_manager_stats")
