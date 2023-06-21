# type:ignore
import os
import time
from config import USE_BINARY_EXECUTABLE, REDIRECT_SIGNALING_STDOUT, DATA_FOLDER
from common_exec import CommonExec


class SignalingServer(CommonExec):
    def __init__(self, local_ip):
        super().__init__("Signaling_server")
        self.json_rpc_port = self.get_port("JRPC")
        if USE_BINARY_EXECUTABLE:
            run = ["./tari_signaling_server"]
        else:
            run = ["cargo", "run", "--bin", "tari_signaling_server", "--manifest-path", "../tari-dan/Cargo.toml", "--"]
        self.exec = [
            *run,
            "-b",
            f"{DATA_FOLDER}/signaling_server",
            "--listen-addr",
            f"{local_ip}:{self.json_rpc_port}",
        ]
        self.run(REDIRECT_SIGNALING_STDOUT)
        print("Waiting for signaling server to start.", end="")
        while not os.path.exists(f"{DATA_FOLDER}/signaling_server/pid"):
            print(".", end="")
            time.sleep(1)
        print("done")
