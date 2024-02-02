from Processes.base_node import BaseNode
from typing import Optional
from Common.local_ip import local_ip


class BaseNodes:
    def __init__(self):
        self.base_nodes: dict[int, BaseNode] = {}

    def has(self, id: Optional[int]) -> bool:
        if id is None:
            return False
        return id in self.base_nodes

    def add(self) -> int:
        id = len(self.base_nodes)
        addresses = self.get_addresses()
        self.base_nodes[id] = BaseNode(id, local_ip, addresses)
        return id

    def any(self) -> BaseNode:
        return next(iter(self.base_nodes.values()))

    def get_addresses(self) -> list[str]:
        return [self.base_nodes[base_node_id].get_address() for base_node_id in self.base_nodes]

    def __del__(self):
        for base_node in self.base_nodes.values():
            del base_node

    def __iter__(self):
        return iter(self.base_nodes)

    def __len__(self):
        return len(self.base_nodes)

    def __getitem__(self, id: int) -> BaseNode:
        return self.base_nodes[id]


base_nodes = BaseNodes()
