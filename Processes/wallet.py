# -*- coding: utf-8 -*-
# type: ignore

from grpc import insecure_channel

try:
    from protos import wallet_pb2_grpc, wallet_pb2, types_pb2
except:
    print("You forgot to generate protos, run protos.sh or protos.bat")
    exit()

from Common.config import TARI_BINS_FOLDER, NETWORK, REDIRECT_WALLET_STDOUT, USE_BINARY_EXECUTABLE, DATA_FOLDER
from typing import Any
from Processes.common_exec import CommonExec
import time
import os


class GrpcWallet:
    def __init__(self, grpc_url):
        self.address = grpc_url
        self.channel = insecure_channel(self.address)
        self.stub = wallet_pb2_grpc.WalletStub(self.channel)

    def get_version(self):
        request = types_pb2.Empty()
        return self.stub.GetVersion(request)

    def get_identity(self):
        request = types_pb2.Empty()
        return self.stub.Identify(request)

    def get_balance(self) -> wallet_pb2.GetBalanceResponse:
        request = wallet_pb2.GetBalanceRequest()
        return self.stub.GetBalance(request)

    def burn(self, amount: int, claim_public_key: bytes, fee_per_gram: int = 5) -> Any:
        request = wallet_pb2.CreateBurnTransactionRequest(amount=amount, fee_per_gram=fee_per_gram, claim_public_key=claim_public_key)
        return self.stub.CreateBurnTransaction(request)


class Wallet(CommonExec):
    def __init__(self):
        pass

    def start(self, base_node_address, local_ip):
        super().__init__("Wallet")
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
            os.path.join(DATA_FOLDER, "wallet"),
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
        self.run(REDIRECT_WALLET_STDOUT)
        # Sometimes it takes a while to establish the grpc connection
        while True:
            try:
                self.grpc_client = GrpcWallet(f"{local_ip}:{self.grpc_port}")
                self.grpc_client.get_version()
                break
            except:
                pass
            time.sleep(1)

    def stop(self):
        print(f'To run the wallet : {" ".join(self.exec).replace("-n ", "")}')
        raise Exception("Base node cannot be stopped")


wallet = Wallet()
