# type:ignore
import os
import time
from Common.config import TARI_DAN_BINS_FOLDER, USE_BINARY_EXECUTABLE, REDIRECT_SIGNALING_STDOUT, DATA_FOLDER
from Processes.common_exec import CommonExec


class SignalingServer(CommonExec):
    def __init__(self):
        super().__init__("SignalingServer")
        self.json_rpc_port = None
        self.address = None

    def start(self, local_ip: str):
        self.json_rpc_port = self.get_port("JRPC")
        self.address = f"http://{local_ip}:{self.json_rpc_port}"
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_DAN_BINS_FOLDER, "tari_signaling_server")]
        else:
            run = ["cargo", "run", "--bin", "tari_signaling_server", "--manifest-path", os.path.join("..", "tari-dan", "Cargo.toml"), "--"]
        self.exec = [
            *run,
            "-b",
            os.path.join(DATA_FOLDER, "signaling_server"),
            "--listen-addr",
            f"{local_ip}:{self.json_rpc_port}",
        ]
        self.run(REDIRECT_SIGNALING_STDOUT)
        print("Waiting for signaling server to start.", end="")
        while not os.path.exists(os.path.join(DATA_FOLDER, "signaling_server", "pid")):
            print(".", end="")
            time.sleep(1)
        print("done")


signaling_server = SignalingServer()
