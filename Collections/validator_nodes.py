from Processes.validator_node import ValidatorNode
import time
from Processes.miner import miner
from Collections.base_wallets import base_wallets
from Collections.base_nodes import base_nodes
from Common.local_ip import local_ip
from typing import Optional
from Collections.collection import Collection


class ValidatorNodes(Collection[ValidatorNode]):
    def __init__(self):
        super().__init__()

    def wait_for_sync(self):
        tip = base_nodes.any().grpc_client.get_tip() - 3
        print("Waiting for VNs to sync to", tip)
        # We have to check if VNs are already running their jrpc server
        while True:
            try:
                while any(vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] != tip for vn in self.items.values()):
                    print(
                        [vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] for vn in self.items.values()],
                        tip,
                        end="\033[K\r",
                    )
                    time.sleep(1)
                break
            except:
                time.sleep(1)
        print("done\033[K")

    def get_addresses(self) -> list[str]:
        return [self.items[vn_id].get_address() for vn_id in self.items]

    def add(self):
        id = len(self.items)
        self.items[id] = ValidatorNode(base_nodes.any().grpc_port, base_wallets.any().grpc_port, id, self.get_addresses())

    def register(self, claim_public_key: str):
        print("Waiting for wallet balance", end=".")
        for vn_id in self.items:
            while base_wallets.any().grpc_client.get_balance().available_balance == 0:
                time.sleep(1)
                print(".", end="")
            self.items[vn_id].register(local_ip, claim_public_key)
            # Uncomment next line if you want to have only one registeration per block
            # miner.mine(1)
        print("done")

        # Wait until they are all in the mempool
        i = 0
        print("Waiting for X tx's in mempool.", end="")
        while i < 10:
            if base_nodes.any().grpc_client.get_mempool_size() < len(self.items) + 1:
                print(".", end="")
                time.sleep(1)
            else:
                break
            i += 1
        print("done")
        # Mining till the VNs are part of the committees
        miner.mine(20)  # Mine the register TXs
        time.sleep(1)

    def jrpc(self, index: int) -> Optional[str]:
        if index in self.items:
            return f"{local_ip}:{self.items[index].json_rpc_port}"
        return None

    def http(self, index: int) -> Optional[str]:
        print(index, self.items, self.items.keys(), index in self.items)
        if index in self.items:
            return f"http://{self.items[index].http_connect_address}"
        return None


validator_nodes = ValidatorNodes()
