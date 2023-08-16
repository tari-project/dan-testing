from Processes.indexer import Indexer
import time
from Processes.base_node import base_node
from Collections.validator_nodes import validator_nodes
from Common.local_ip import local_ip
from typing import Optional


class Indexers:
    def __init__(self):
        self.indexers: dict[int, Indexer] = {}

    def has_indexer(self, id: int) -> bool:
        return id in self.indexers

    def stop(self, id: int):
        if self.has_indexer(id):
            del self.indexers[id]
        else:
            print(f"Indexer id ({id}) is invalid, either it never existed or you already stopped it")

    def live(self):
        for id in self.indexers:
            print(f"Indexer<{id}> is running")

    def wait_for_sync(self):
        tip = base_node.grpc_client.get_tip() - 3
        print("Waiting for Indexers to sync to", tip)
        # We have to check if VNs are already running their jrpc server
        while True:
            try:
                while any(indexer.jrpc_client.get_epoch_manager_stats()["current_block_height"] != tip for indexer in self.indexers.values()):
                    print(
                        [indexer.jrpc_client.get_epoch_manager_stats()["current_block_height"] for indexer in self.indexers.values()],
                        tip,
                        end="\033[K\r",
                    )
                    time.sleep(1)
                break
            except:
                time.sleep(1)
        print("done\033[K")

    def get_addresses(self) -> list[str]:
        return [indexer.get_address() for indexer in self.indexers.values()]

    def add_indexer(self, id: int):
        if self.has_indexer(id):
            print(f"Indexer id ({id}) is already in use")
            return
        self.indexers[id] = Indexer(id, base_node.grpc_port, validator_nodes.get_addresses())

    def jrpc(self, index: int) -> Optional[str]:
        if index in self.indexers:
            return f"{local_ip}:{self.indexers[index].json_rpc_port}"
        return None

    def http(self, index: int) -> Optional[str]:
        print(index, self.indexers, self.indexers.keys(), index in self.indexers)
        if index in self.indexers:
            return f"http://{self.indexers[index].http_ui_address}"
        return None

    def any_indexer(self) -> Indexer:
        return next(iter(self.indexers.values()))

    def __iter__(self):
        return iter(self.indexers)

    def __getitem__(self, index: int):
        return self.indexers[index]


indexers = Indexers()
