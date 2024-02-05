from Processes.base_wallet import BaseWallet
from Collections.base_nodes import base_nodes
from Common.local_ip import local_ip
from Collections.collection import Collection


class BaseWallets(Collection[BaseWallet]):
    def __init__(self):
        super().__init__()

    def add(self):
        id = len(self.items)
        self.items[id] = BaseWallet(id, base_nodes.any().get_address(), local_ip, base_nodes.get_addresses())


base_wallets = BaseWallets()
