from Processes.base_node import BaseNode
from Common.local_ip import local_ip
from Collections.collection import Collection


class BaseNodes(Collection[BaseNode]):
    def __init__(self):
        super().__init__()

    def add(self):
        id = len(self.items)
        addresses = self.get_addresses()
        self.items[id] = BaseNode(id, local_ip, addresses)

    def get_addresses(self) -> list[str]:
        return [self.items[base_node_id].get_address() for base_node_id in self.items]


base_nodes = BaseNodes()
