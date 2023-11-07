# type:ignore

from Common.config import TARI_BINS_FOLDER, NETWORK, REDIRECT_MINER_STDOUT, USE_BINARY_EXECUTABLE, DATA_FOLDER
from Processes.subprocess_wrapper import SubprocessWrapper
import subprocess
import os


class Miner:
    def __init__(self):
        pass

    def start(self, base_node_grpc_port, wallet_grpc_port, local_ip):
        self.name = "sha"
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_BINS_FOLDER, "minotari_sha")]
        else:
            run = ["cargo", "run", "--bin", "minotari_miner", "--manifest-path", os.path.join("..", "tari", "Cargo.toml"), "--"]
        self.exec_template = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, "sha"),
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
            self.process = SubprocessWrapper.call(self.exec, stdout=open(os.path.join(DATA_FOLDER, "stdout", "shamin.log"), "a+"), stderr=subprocess.STDOUT)
        else:
            self.process = SubprocessWrapper.call(self.exec)

    def get_logs(self):
        logs: list[tuple[str, str, str]] = []
        for path, _dirs, files in os.walk(os.path.join(DATA_FOLDER, self.name)):
            for file in files:
                if file.endswith(".log"):
                    logs.append((os.path.join(path, file), self.name, os.path.splitext(file)[0]))
        return logs

    def get_stdout(self):
        logs: list[tuple[str, str]] = []
        for path, _dirs, files in os.walk(os.path.join(DATA_FOLDER, "stdout")):
            for file in files:
                if self.name in file:
                    logs.append((os.path.join(path, file), "stdout"))
        return logs


miner = Miner()
