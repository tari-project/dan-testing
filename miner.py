# type:ignore

from config import TARI_BINS_FOLDER, NETWORK, REDIRECT_MINER_STDOUT, USE_BINARY_EXECUTABLE, DATA_FOLDER
from subprocess_wrapper import SubprocessWrapper
import subprocess
import os


class Miner:
    def __init__(self, base_node_grpc_port, wallet_grpc_port, local_ip):
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_BINS_FOLDER, "tari_miner")]
        else:
            run = ["cargo", "run", "--bin", "tari_miner", "--manifest-path", os.path.join("..", "tari", "Cargo.toml"), "--"]
        self.exec_template = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, "miner"),
            "--network",
            NETWORK,
            "--max-blocks",
            "#blocks",
            "-p",
            f"miner.base_node_grpc_address=/ip4/{local_ip}/tcp/{base_node_grpc_port}",
            "-p",
            f"miner.wallet_grpc_address=/ip4/{local_ip}/tcp/{wallet_grpc_port}",
            "-p",
            f"miner.num_mining_threads=1",
        ]

    def mine(self, blocks: int):
        self.exec = list(self.exec_template)
        self.exec[self.exec.index("#blocks")] = str(blocks)
        if REDIRECT_MINER_STDOUT:
            self.process = SubprocessWrapper.call(
                self.exec, stdout=open(os.path.join(DATA_FOLDER, "stdout", "miner.log"), "a+"), stderr=subprocess.STDOUT
            )
        else:
            self.process = SubprocessWrapper.call(self.exec)
