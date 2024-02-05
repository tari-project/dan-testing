# -*- coding: utf-8 -*-

from grpc import insecure_channel  # type: ignore

try:
    from protos import wallet_pb2_grpc, wallet_pb2, types_pb2, network_pb2
except:
    print("You forgot to generate protos, run protos.sh or protos.bat")
    exit()

from Common.config import TARI_BINS_FOLDER, NETWORK, USE_BINARY_EXECUTABLE, DATA_FOLDER
from Processes.common_exec import CommonExec
import time
import os
from typing import Any


class GrpcWallet:
    def __init__(self, grpc_url: str):
        self.address = grpc_url
        self.channel = insecure_channel(self.address)
        self.stub = wallet_pb2_grpc.WalletStub(self.channel)

    def get_version(self) -> wallet_pb2.GetVersionResponse:
        request = wallet_pb2.GetVersionRequest()
        return self.stub.GetVersion(request)  # type:ignore

    def get_identity(self) -> network_pb2.GetIdentityResponse:
        request = network_pb2.GetIdentityRequest()
        return self.stub.Identify(request)  # type:ignore

    def get_address(self) -> wallet_pb2.GetAddressResponse:
        request = types_pb2.Empty()
        return self.stub.GetAddress(request)  # type:ignore

    def get_balance(self) -> wallet_pb2.GetBalanceResponse:
        request = wallet_pb2.GetBalanceRequest()
        return self.stub.GetBalance(request)  # type:ignore

    def check_connectivity(self) -> wallet_pb2.CheckConnectivityResponse:
        request = wallet_pb2.GetConnectivityRequest()
        return self.stub.CheckConnectivity(request)  # type:ignore

    def create_burn_transaction(
        self, amount: int, claim_public_key: bytes, message: str = "", fee_per_gram: int = 5
    ) -> wallet_pb2.CreateBurnTransactionResponse:
        request = wallet_pb2.CreateBurnTransactionRequest(amount=amount, fee_per_gram=fee_per_gram, message=message, claim_public_key=claim_public_key)
        return self.stub.CreateBurnTransaction(request)  # type:ignore


class BaseWallet(CommonExec):
    def __init__(self, id: int, base_node_address: str, local_ip: str, peer_seeds: list[str] = []):
        super().__init__("BaseWallet", id)
        self.local_ip = local_ip
        self.public_port = self.get_port("public_address")
        self.public_address = f"/ip4/{local_ip}/tcp/{self.public_port}"
        self.grpc_port = self.get_port("GRPC")
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_BINS_FOLDER, "minotari_console_wallet")]
        else:
            run = ["cargo", "run", "--bin", "minotari_console_wallet", "--manifest-path", os.path.join("..", "tari", "Cargo.toml"), "--"]
        self.exec = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, self.name),
            "-n",
            "--network",
            NETWORK,
            "--enable-grpc",
            "--password",
            "a",
            "-p",
            "wallet.p2p.transport.type=tcp",
            "-p",
            f"wallet.custom_base_node={base_node_address}",
            "-p",
            f"wallet.grpc_address=/ip4/{local_ip}/tcp/{self.grpc_port}",
            "-p",
            f"wallet.p2p.transport.tcp.listener_address={self.public_address}",
            "-p",
            f"wallet.p2p.public_addresses={self.public_address}",
            "-p",
            "wallet.p2p.allow_test_addresses=true",
            # "-p",
            # f'{NETWORK}.p2p.seeds.peer_seeds=""',
        ]
        if peer_seeds:
            self.exec.append("-p")
            self.exec.append(f"{NETWORK}.p2p.seeds.peer_seeds={','.join(peer_seeds)}")

        self.run()

    def run(self, cwd: str | None = None) -> bool:
        if not super().run(cwd):
            return False
        # Sometimes it takes a while to establish the grpc connection
        while True:
            try:
                self.grpc_client = GrpcWallet(f"{self.local_ip}:{self.grpc_port}")
                self.grpc_client.get_version()
                break
            except Exception as e:
                print(e)
            time.sleep(1)
        return True

    def get_info_for_ui(self) -> dict[str, Any]:
        return {"name": self.name, "grpc": self.grpc_client.address}
