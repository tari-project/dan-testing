# type:ignore

from Common.ports import ports
from Common.config import TARI_DAN_BINS_FOLDER, NETWORK, REDIRECT_VN_FROM_INDEX_STDOUT, NO_FEES, USE_BINARY_EXECUTABLE, DATA_FOLDER
from Processes.subprocess_wrapper import SubprocessWrapper
import subprocess
import os
import time
import re
import requests
from Processes.common_exec import CommonExec
from Common.local_ip import local_ip


class JrpcValidatorNode:
    def __init__(self, jrpc_url):
        self.id = 0
        self.url = jrpc_url
        self.token = None

    def internal_call(self, method, params=[]):
        self.id += 1
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": self.id, "params": params})
        return response.json()["result"]

    def call(self, method, params=[]):
        return self.internal_call(method, params)

    def get_identity(self):
        return self.call("get_identity")

    def get_epoch_manager_stats(self):
        return self.call("get_epoch_manager_stats")

    def get_all_vns(self, epoch):
        return self.call("get_all_vns", epoch)

    def get_fees(self, claim_leader_public_key, epoch):
        return self.call("get_fees", [claim_leader_public_key, epoch])

    def get_network_committees(self):
        return self.call("get_network_committees")

    def get_fees(self, min_epoch, max_epoch, validator_node):
        return self.call("get_fees", [[min_epoch, max_epoch], validator_node])


class ValidatorNode(CommonExec):
    def __init__(self, base_node_grpc_port, wallet_grpc_port, node_id, peers=[]):
        super().__init__("Validator_node", node_id)
        self.public_port = self.get_port("public_address")
        self.public_address = f"/ip4/{local_ip}/tcp/{self.public_port}"
        self.json_rpc_port = self.get_port("JRPC")
        self.json_connect_address = f"{local_ip}:{self.json_rpc_port}"
        self.json_listen_address = f"0.0.0.0:{self.json_rpc_port}"
        self.http_port = self.get_port("HTTP")
        self.http_connect_address = f"{local_ip}:{self.http_port}"
        self.http_listen_address = f"0.0.0.0:{self.http_port}"
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_DAN_BINS_FOLDER, "tari_validator_node")]
        else:
            run = ["cargo", "run", "--bin", "tari_validator_node", "--manifest-path", os.path.join("..", "tari-dan", "Cargo.toml"), "--"]
        self.exec = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, self.name),
            "--network",
            NETWORK,
            "-p",
            f"validator_node.base_node_grpc_address={local_ip}:{base_node_grpc_port}",
            "-p",
            f"validator_node.wallet_grpc_address={local_ip}:{wallet_grpc_port}",
            # "-p",
            # "validator_node.p2p.transport.type=tcp",
            # "-p",
            # f"validator_node.p2p.transport.tcp.listener_address=/ip4/0.0.0.0/tcp/{self.public_port}",
            # "-p",
            # "validator_node.p2p.allow_test_addresses=true",
            "-p",
            f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peers)}",
            # "-p",
            # f"validator_node.p2p.public_address={self.public_adress}",
            # "-p",
            # f"validator_node.public_address={self.public_address}",
            "-p",
            f"validator_node.json_rpc_address={self.json_listen_address}",
            "-p",
            f"validator_node.http_ui_address={self.http_listen_address}",
            "-p",
            f"validator_node.auto_register={False}",
            "-p",
            f"validator_node.no_fees={NO_FEES}",
            "--ui-connect-address",
            f"http://{self.json_connect_address}",
        ]
        self.run(REDIRECT_VN_FROM_INDEX_STDOUT)
        print("Waiting for VN to start.", end="")
        while not os.path.exists(os.path.join(DATA_FOLDER, self.name, "localnet", "pid")):
            print(".", end="")
            if self.process.poll() is None:
                time.sleep(1)
            else:
                raise Exception(f"Validator node did not start successfully: Exit code:{self.process.poll()}")
        print("done")
        self.jrpc_client = JrpcValidatorNode(f"http://{self.json_connect_address}")

    def get_address(self) -> str:
        identity = self.jrpc_client.get_identity()
        public_key = identity["public_key"]
        public_addresses = identity["public_addresses"]
        return "::".join([public_key, *public_addresses])

    def register(self, local_ip: str, claim_public_key: str = "d6d21f5c18406b390ce405fd21773d90bddb221b38c950dccf8f26840937004d"):
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_DAN_BINS_FOLDER, "tari_validator_node_cli")]
        else:
            run = [
                "cargo",
                "run",
                "--bin",
                "tari_validator_node_cli",
                "--manifest-path",
                os.path.join("..", "tari-dan", "Cargo.toml"),
                "--",
            ]
        self.exec_cli = [
            *run,
            "--vn-daemon-jrpc-endpoint",
            f"/ip4/{local_ip}/tcp/{self.json_rpc_port}",
            # "--validator-maturity",
            # "1000",
            "vn",
            "register",
            claim_public_key,
        ]
        if self.id >= REDIRECT_VN_FROM_INDEX_STDOUT:
            self.cli_process = SubprocessWrapper.call(
                self.exec_cli, stdout=open(os.path.join(DATA_FOLDER, "stdout", f"{self.name}_cli.log"), "a+"), stderr=subprocess.STDOUT
            )
            if self.cli_process != 0:
                raise Exception("Validator node cli registration process failed")
            print(f"Validator node register: ok")
        else:
            self.cli_process = SubprocessWrapper.call(self.exec_cli)
            if self.cli_process != 0:
                raise Exception("Validator node cli registration process failed")
            print(f"Validator node register: ok")

    def get_info_for_ui(self):
        return {"http": self.http_connect_address, "jrpc": self.json_connect_address}
