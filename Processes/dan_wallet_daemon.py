# type:ignore
from Common.config import TARI_DAN_BINS_FOLDER, REDIRECT_DAN_WALLET_STDOUT, USE_BINARY_EXECUTABLE, DATA_FOLDER
import base64
import os
import requests
import socket
import time
from typing import Any, Optional
from Processes.common_exec import CommonExec
from Stats.stats import stats
from Processes.subprocess_wrapper import SubprocessWrapper
from threading import Lock
import subprocess


class JrpcDanWalletDaemon:
    def __init__(self, jrpc_url: str):
        self.id = 0
        self.url = jrpc_url
        self.token = None
        self.last_account_name = ""

    def call(self, method: str, params: list[Any] = []):
        self.id += 1
        headers = None
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": self.id, "params": params}, headers=headers)
        json_response = response.json()
        if "error" in json_response:
            print(json_response["error"])
        else:
            return json_response["result"]

    def auth(self):
        resp = self.call("auth.request", [["Admin"], None])
        auth_token = resp["auth_token"]
        resp = self.call("auth.accept", [auth_token, "AdminToken"])
        self.token = resp["permissions_token"]

    def keys_list(self):
        return self.call("keys.list")

    def accounts_create(self, name: str, custom_access_rules: Any = None, fee: Optional[int] = None, is_default: bool = True):
        id = stats.start_run("accounts.create")
        res = self.call("accounts.create", [name, custom_access_rules, fee, is_default])
        self.last_account_name = name
        stats.end_run(id)
        return res

    def create_free_test_coins(self, account: Any, amount: int, fee: Optional[int] = None, key_id: Optional[int] = None):
        id = stats.start_run("accounts.create_free_test_coins")
        res = self.call("accounts.create_free_test_coins", [account, amount, fee, key_id])
        self.last_account_name = account
        stats.end_run(id)
        return res

    def accounts_list(self, offset: int = 0, limit: int = 1) -> dict[str, Any]:
        return self.call("accounts.list", [offset, limit])

    def transaction_submit_instruction(self, instruction, dump_buckets: bool = True):
        tx_id = 0
        if dump_buckets:
            res = self.call(
                "transactions.submit_instruction",
                {
                    "instructions": [instruction],
                    "fee_account": self.last_account_name,
                    "dump_outputs_into": self.last_account_name,
                    "fee": 1000,
                },
            )
            tx_id = res["transaction_id"]
        else:
            res = self.call(
                "transactions.submit_instruction",
                {"instructions": [instruction], "fee_account": self.last_account_name, "fee": 1000},
            )
            tx_id = res["transaction_id"]
        while True:
            tx = self.transaction_get(tx_id)
            print(tx)
            status = tx["status"]
            if status != "Pending":
                if status == "Rejected":
                    raise Exception(f"Transaction rejected:{tx['transaction_failure']}")
                return tx
            time.sleep(1)

    def transaction_get(self, tx_id):
        return self.call("transactions.get", {"transaction_id": tx_id})

    def claim_burn(self, burn: Any, account: Any):
        account = account["account"]["address"]["Component"]
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
        ClaimBurnRequest = {"account": account, "claim_proof": claim_proof, "fee": 10}
        return self.call("accounts.claim_burn", ClaimBurnRequest)

    def get_balances(self, account: Any):
        return self.call("accounts.get_balances", [account["account"]["name"], True])

    def transfer(self, account: Any, amount: int, resource_address: Any, destination_publickey: Any, fee: Optional[int]):
        id = stats.start_run("accounts.create_free_test_coins")
        res = self.call("accounts.transfer", [account["account"]["name"], amount, resource_address, destination_publickey, fee])
        stats.end_run(id)
        return res

    def confidential_transfer(self, account: Any, amount: int, resource_address: Any, destination_publickey: Any, fee: Optional[int]):
        id = stats.start_run("accounts.create_free_test_coins")
        res = self.call("accounts.confidential_transfer", [account["account"]["name"], amount, resource_address, destination_publickey, fee])
        stats.end_run(id)
        return res

    def get_all_tx_by_status(self, status: Optional[str] = None):
        return self.call("transactions.get_all_by_status", [status])


class DanWalletDaemon(CommonExec):
    def __init__(self, dan_wallet_id: int, indexer_jrpc_port: int, signaling_server_port: int, local_ip: str):
        super().__init__("Dan_wallet_daemon", dan_wallet_id)
        self.json_rpc_port = super().get_port("JRPC")
        self.json_connect_address = f"{local_ip}:{self.json_rpc_port}"
        self.json_listen_address = f"0.0.0.0:{self.json_rpc_port}"
        self.http_port = self.get_port("HTTP")
        self.http_connect_address = f"{local_ip}:{self.http_port}"
        self.http_listen_address = f"0.0.0.0:{self.http_port}"
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_DAN_BINS_FOLDER, "tari_dan_wallet_daemon")]
        else:
            run = ["cargo", "run", "--bin", "tari_dan_wallet_daemon", "--manifest-path", os.path.join("..", "tari-dan", "Cargo.toml"), "--"]
        self.exec = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, self.name),
            "--network",
            "localnet",
            "--json-rpc-address",
            self.json_listen_address,
            "--indexer-url",
            f"http://{local_ip}:{indexer_jrpc_port}/json_rpc",
            "-p",
            f"dan_wallet_daemon.http_ui_address={self.http_listen_address}",
            "--ui-connect-address",
            f"http://{self.json_connect_address}",
        ]
        if signaling_server_port:
            self.exec = [*self.exec, "--signaling-server-address", f"{local_ip}:{signaling_server_port}"]
        self.run(REDIRECT_DAN_WALLET_STDOUT)

        # (out, err) = self.process.communicate()
        self.jrpc_client = JrpcDanWalletDaemon(f"http://{self.json_connect_address}")
        while not os.path.exists(os.path.join(DATA_FOLDER, self.name, "localnet", "pid")):
            if self.process.poll() is None:
                time.sleep(1)
            else:
                raise Exception(f"DAN wallet did not start successfully: Exit code:{self.process.poll()}")
        print(f"Dan wallet daemon {dan_wallet_id} started")

    def get_info_for_ui(self):
        return {"http": self.http_connect_address, "jrpc": self.json_connect_address}
