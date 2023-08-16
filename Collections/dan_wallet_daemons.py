from Processes.dan_wallet_daemon import DanWalletDaemon
import time
from Processes.base_node import base_node
from Processes.wallet import wallet
from Collections.validator_nodes import validator_nodes
from Common.local_ip import local_ip
from typing import Optional


class DanWalletDaemons:
    def __init__(self):
        self.dan_wallets: dict[int, DanWalletDaemon] = {}

    def has_dan_wallet(self, id: int) -> bool:
        return id in self.dan_wallets

    def stop(self, id: int):
        if self.has_dan_wallet(id):
            del self.dan_wallets[id]
        else:
            print(f"Dan wallet daemon id ({id}) is invalid, either it never existed or you already stopped it")

    def live(self):
        for id in self.dan_wallets:
            print(f"DanWalletDaemon<{id}> is running")

    def add_dan_wallet_daemon(self, id: int, indexer_jrpc: int, signaling_server_jrpc: int):
        if self.has_dan_wallet(id):
            print(f"Dan wallet daemon id ({id}) is already in use")
            return
        self.dan_wallets[id] = DanWalletDaemon(id, indexer_jrpc, signaling_server_jrpc, local_ip)

    def jrpc(self, index: int) -> Optional[str]:
        if index in self.dan_wallets:
            return f"{local_ip}:{self.dan_wallets[index].json_rpc_port}"
        return None

    def http(self, index: int) -> Optional[str]:
        print(index, self.dan_wallets, self.dan_wallets.keys(), index in self.dan_wallets)
        if index in self.dan_wallets:
            return f"http://{self.dan_wallets[index].http_ui_address}"
        return None

    def any_dan_wallet_daemon(self) -> DanWalletDaemon:
        return next(iter(self.dan_wallets.values()))

    def __iter__(self):
        return iter(self.dan_wallets)

    def __getitem__(self, index: int):
        return self.dan_wallets[index]


dan_wallets = DanWalletDaemons()
