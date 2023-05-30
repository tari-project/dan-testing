# type:ignore
from config import REDIRECT_DAN_WALLET_STDOUT, USE_BINARY_EXECUTABLE, REDIRECT_DAN_WALLET_WEBUI_STDOUT
import base64
import os
import requests
import time
from typing import Any
from common_exec import CommonExec
from stats import stats
from subprocess_wrapper import SubprocessWrapper
from threading import Lock
import subprocess


class JrpcDanWalletDaemon:
    def __init__(self, jrpc_url):
        self.id = 0
        self.url = jrpc_url
        self.token = None

    def call(self, method, params=[]):
        self.id += 1
        headers = None
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(self.url, json={"jsonrpc": "2.0", "method": method, "id": self.id, "params": params}, headers=headers)
        x = response.json()
        if "error" in x:
            print(x["error"])
        else:
            return x["result"]

    def auth(self):
        resp = self.call("auth.request", [["Admin"], None])
        auth_token = resp["auth_token"]
        resp = self.call("auth.accept", [auth_token])
        self.token = resp["permissions_token"]

    def keys_list(self):
        return self.call("keys.list")

    def accounts_create(self, name: str, custom_access_rules: Any = None, fee: int | None = None, is_default: bool = True):
        id = stats.start_run("accounts.create")
        res = self.call("accounts.create", [name, custom_access_rules, fee, is_default])
        stats.end_run(id)
        return res

    def create_free_test_coins(self, account: Any, amount: int, fee: int | None = None):
        id = stats.start_run("accounts.create_free_test_coins")
        res = self.call("accounts.create_free_test_coins", [account, amount, fee])
        stats.end_run(id)
        return res

    def accounts_list(self, offset=0, limit=1):
        return self.call("accounts.list", [offset, limit])

    def transaction_submit_instruction(self, instruction):
        tx_id = self.call(
            "transactions.submit_instruction",
            {"instruction": instruction, "fee_account": "TestAccount", "dump_outputs_into": "TestAccount", "fee": 1},
        )["hash"]
        while True:
            tx = self.transaction_get(tx_id)
            status = tx["status"]
            if status != "Pending":
                if status == "Rejected":
                    raise Exception(f"Transaction rejected:{tx['transaction_failure']}")
                return tx
            time.sleep(1)

    def transaction_get(self, tx_id):
        return self.call("transactions.get", {"hash": tx_id})

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

    def transfer(self, account: Any, amount: int, resource_address: Any, destination_publickey: Any, fee: int | None):
        id = stats.start_run("accounts.create_free_test_coins")
        res = self.call("accounts.transfer", [account["account"]["name"], amount, resource_address, destination_publickey, fee])
        stats.end_run(id)
        return res

    def confidential_transfer(self, account: Any, amount: int, resource_address: Any, destination_publickey: Any, fee: int | None):
        id = stats.start_run("accounts.create_free_test_coins")
        res = self.call(
            "accounts.confidential_transfer", [account["account"]["name"], amount, resource_address, destination_publickey, fee]
        )
        stats.end_run(id)
        return res


class DanWalletDaemon(CommonExec):
    def __init__(self, dan_wallet_id: int, indexer_jrpc_port: int, signaling_server_port: int):
        super().__init__("Dan_wallet_daemon", dan_wallet_id)
        self.json_rpc_port = super().get_port("JRPC")
        if USE_BINARY_EXECUTABLE:
            run = ["./tari_dan_wallet_daemon"]
        else:
            run = ["cargo", "run", "--bin", "tari_dan_wallet_daemon", "--manifest-path", "../tari-dan/Cargo.toml", "--"]
        self.exec = [
            *run,
            "-b",
            f"dan_wallet_daemon_{dan_wallet_id}",
            "--network",
            "localnet",
            "--listen-addr",
            f"127.0.0.1:{self.json_rpc_port}",
            "--indexer_url",
            f"http://127.0.0.1:{indexer_jrpc_port}/json_rpc",
        ]
        if signaling_server_port:
            self.exec = [*self.exec, "--signaling_server_address", f"127.0.0.1:{signaling_server_port}"]
        self.run(REDIRECT_DAN_WALLET_STDOUT)

        # (out, err) = self.process.communicate()
        jrpc_address = f"http://127.0.0.1:{self.json_rpc_port}"
        self.jrpc_client = JrpcDanWalletDaemon(jrpc_address)
        self.http_client = DanWalletUI(self.id, jrpc_address)
        while not os.path.exists(f"dan_wallet_daemon_{dan_wallet_id}/localnet/pid"):
            if self.process.poll() is None:
                time.sleep(1)
            else:
                raise Exception(f"DAN wallet did not start successfully: Exit code:{self.process.poll()}")
        print(f"Dan wallet daemon {dan_wallet_id} started")


npm_install_done = False
npm_install_mutex = Lock()


class DanWalletUI(CommonExec):
    def __init__(self, dan_wallet_id, daemon_jrpc_address):
        global npm_install_done, npm_install_mutex
        super().__init__("dan_wallet_ui", dan_wallet_id)
        npm_install_mutex.acquire()
        if not npm_install_done:
            self.process = SubprocessWrapper.call(
                ["npm", "install"],
                stdin=subprocess.PIPE,
                stdout=open(f"stdout/tari-connector_prepare.log", "a+"),
                stderr=subprocess.STDOUT,
                cwd="../tari-dan/applications/tari_dan_wallet_web_ui",
            )
            npm_install_done = True
        npm_install_mutex.release()
        self.http_port = self.get_port("HTTP")
        self.exec = [
            "npm",
            "--prefix",
            "../tari-dan/applications/tari_dan_wallet_web_ui",
            "run",
            "dev",
            "--",
            "--port",
            str(self.http_port),
        ]
        self.daemon_jrpc_address = daemon_jrpc_address
        self.env["VITE_DAEMON_JRPC_ADDRESS"] = daemon_jrpc_address
        self.run(REDIRECT_DAN_WALLET_WEBUI_STDOUT)
