from Processes.validator_node import ValidatorNode
import time
from Processes.base_node import base_node
from Processes.wallet import wallet
from Processes.miner import miner
from Common.local_ip import local_ip
from typing import Optional


class ValidatorNodes:
    def __init__(self):
        self.validator_nodes: dict[int, ValidatorNode] = {}

    def has_vn(self, vn_id: int) -> bool:
        return vn_id in self.validator_nodes

    def stop(self, vn_id: int):
        if self.has_vn(vn_id):
            del self.validator_nodes[vn_id]
        else:
            print(f"VN id ({vn_id}) is invalid, either it never existed or you already stopped it")

    def live(self):
        for vn_id in self.validator_nodes:
            print(f"VN<{vn_id}> is running")

    def wait_for_sync(self):
        tip = base_node.grpc_client.get_tip() - 3
        print("Waiting for VNs to sync to", tip)
        # We have to check if VNs are already running their jrpc server
        while True:
            try:
                while any(vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] != tip for vn in self.validator_nodes.values()):
                    print(
                        [vn.jrpc_client.get_epoch_manager_stats()["current_block_height"] for vn in self.validator_nodes.values()],
                        tip,
                        end="\033[K\r",
                    )
                    time.sleep(1)
                break
            except:
                time.sleep(1)
        print("done\033[K")

    def get_addresses(self) -> list[str]:
        return [self.validator_nodes[vn_id].get_address() for vn_id in self.validator_nodes]

    def add_validator_node(self, vn_id: int):
        if self.has_vn(vn_id):
            print(f"VN id ({vn_id}) is already in use")
            return
        self.validator_nodes[vn_id] = ValidatorNode(base_node.grpc_port, wallet.grpc_port, vn_id, self.get_addresses())

    def register(self, claim_public_key: str):
        print("Waiting for wallet balance", end=".")
        for vn_id in self.validator_nodes:
            while wallet.grpc_client.get_balance().available_balance == 0:
                time.sleep(1)
                print(".", end="")
            self.validator_nodes[vn_id].register(local_ip, claim_public_key)
            # Uncomment next line if you want to have only one registeration per block
            # miner.mine(1)
        print("done")

        # Wait until they are all in the mempool
        i = 0
        print("Waiting for X tx's in mempool.", end="")
        while i < 10:
            if base_node.grpc_client.get_mempool_size() < len(self.validator_nodes) + 1:
                print(".", end="")
                time.sleep(1)
            else:
                break
            i += 1
        print("done")
        # Mining till the VNs are part of the committees
        miner.mine(20)  # Mine the register TXs
        time.sleep(1)

    def jrpc_vn(self, index: int) -> Optional[str]:
        if index in self.validator_nodes:
            return f"{local_ip}:{self.validator_nodes[index].json_rpc_port}"
        return None

    def http_vn(self, index: int) -> Optional[str]:
        print(index, self.validator_nodes, self.validator_nodes.keys(), index in self.validator_nodes)
        if index in self.validator_nodes:
            return f"http://{self.validator_nodes[index].http_ui_address}"
        return None

    def any_node(self) -> ValidatorNode:
        return next(iter(self.validator_nodes.values()))

    def __iter__(self):
        return iter(self.validator_nodes)

    def __getitem__(self, index: int):
        return self.validator_nodes[index]


validator_nodes = ValidatorNodes()
