from Processes.indexer import Indexer
import time
from Collections.collection import Collection
from Collections.base_nodes import base_nodes
from Collections.validator_nodes import validator_nodes
from Common.local_ip import local_ip
from typing import Optional


class Indexers(Collection[Indexer]):
    def __init__(self):
        super().__init__()

    def wait_for_sync(self):
        tip = base_nodes.any().grpc_client.get_tip() - 3
        print("Waiting for Indexers to sync to", tip)
        # We have to check if VNs are already running their jrpc server
        while True:
            try:
                while any(indexer.jrpc_client.get_epoch_manager_stats()["current_block_height"] != tip for indexer in self.items.values()):
                    print(
                        [indexer.jrpc_client.get_epoch_manager_stats()["current_block_height"] for indexer in self.items.values()],
                        tip,
                        end="\033[K\r",
                    )
                    time.sleep(1)
                break
            except:
                time.sleep(1)
        print("done\033[K")

    def get_addresses(self) -> list[str]:
        return [indexer.get_address() for indexer in self.items.values()]

    def add(self) -> str:
        id = len(self.items)
        self.items[id] = Indexer(id, base_nodes.any().grpc_port, validator_nodes.get_addresses())
        return self.items[id].name

    def jrpc(self, index: int) -> Optional[str]:
        if index in self.items:
            return f"{local_ip}:{self.items[index].json_rpc_port}"
        return None

    def http(self, index: int) -> Optional[str]:
        print(index, self.items, self.items.keys(), index in self.items)
        if index in self.items:
            return f"http://{self.items[index].http_connect_address}"
        return None


indexers = Indexers()
