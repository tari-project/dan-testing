from Processes.base_wallet import BaseWallet
from typing import Optional
from Collections.base_nodes import base_nodes
from Common.local_ip import local_ip


class BaseWallets:
    def __init__(self):
        self.wallets: dict[int, BaseWallet] = {}

    def has(self, id: Optional[int]) -> bool:
        if id is None:
            return False
        return id in self.wallets

    def add(self) -> int:
        id = len(self.wallets)
        self.wallets[id] = BaseWallet(id, base_nodes.any().get_address(), local_ip, base_nodes.get_addresses())
        return id

    def any(self) -> BaseWallet:
        return next(iter(self.wallets.values()))

    def __del__(self):
        for base_node in self.wallets.values():
            del base_node

    def __iter__(self):
        return iter(self.wallets)

    def __len__(self):
        return len(self.wallets)

    def __getitem__(self, id: int) -> BaseWallet:
        return self.wallets[id]


base_wallets = BaseWallets()
