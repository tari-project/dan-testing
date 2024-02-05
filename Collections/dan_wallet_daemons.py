from Processes.dan_wallet_daemon import DanWalletDaemon
from Common.local_ip import local_ip
from typing import Optional
from Collections.collection import Collection
from Processes.signaling_server import signaling_server
from Collections.indexers import indexers


class DanWalletDaemons(Collection[DanWalletDaemon]):
    def __init__(self):
        super().__init__()

    def add(self):
        id = len(self.items)
        self.items[id] = DanWalletDaemon(id, indexers[id % len(indexers)].json_rpc_port, signaling_server.json_rpc_port, local_ip)

    def jrpc(self, index: int) -> Optional[str]:
        if index in self.items:
            return f"{local_ip}:{self.items[index].json_rpc_port}"
        return None

    def http(self, index: int) -> Optional[str]:
        print(index, self.items, self.items.keys(), index in self.items)
        if index in self.items:
            return f"http://{self.items[index].http_connect_address}"
        return None


dan_wallets = DanWalletDaemons()
