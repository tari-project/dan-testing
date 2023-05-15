# type:ignore

from config import NETWORK, REDIRECT_MINER_STDOUT, USE_BINARY_EXECUTABLE
from subprocess_wrapper import SubprocessWrapper
import subprocess


class Miner:
    def __init__(self, base_node_grpc_port, wallet_grpc_port):
        if USE_BINARY_EXECUTABLE:
            run = ["./tari_miner"]
        else:
            run = ["cargo", "run", "--bin", "tari_miner", "--manifest-path", "../tari/Cargo.toml", "--"]
        self.exec_template = [
            *run,
            "-b",
            "miner",
            "--network",
            NETWORK,
            "--max-blocks",
            "#blocks",
            "-p",
            f"miner.base_node_grpc_address=/ip4/127.0.0.1/tcp/{base_node_grpc_port}",
            "-p",
            f"miner.wallet_grpc_address=/ip4/127.0.0.1/tcp/{wallet_grpc_port}",
            "-p",
            f"miner.num_mining_threads=1",
        ]

    def mine(self, blocks: int):
        self.exec = list(self.exec_template)
        self.exec[self.exec.index("#blocks")] = str(blocks)
        if REDIRECT_MINER_STDOUT:
            self.process = SubprocessWrapper.call(self.exec, stdout=open("stdout/miner.log", "a+"), stderr=subprocess.STDOUT)
        else:
            self.process = SubprocessWrapper.call(self.exec)
