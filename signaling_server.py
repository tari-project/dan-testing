# type:ignore
import os
import time
from config import USE_BINARY_EXECUTABLE, REDIRECT_SIGNALING_STDOUT
from common_exec import CommonExec
import platform


class SignalingServer(CommonExec):
    def __init__(self):
        super().__init__("Signaling_server")
        self.json_rpc_port = self.get_port("JRPC")
        if USE_BINARY_EXECUTABLE:
            if platform.system() == "Windows":
                run = ["./tari_signaling_server.exe"]
            else:
                run = ["./tari_signaling_server"]
        else:
            run = ["cargo", "run", "--bin", "tari_signaling_server", "--manifest-path", "../tari-dan/Cargo.toml", "--"]
        self.exec = [
            *run,
            "-b",
            "signaling_server",
            "--listen-addr",
            f"127.0.0.1:{self.json_rpc_port}",
        ]
        self.run(REDIRECT_SIGNALING_STDOUT)
        print("Waiting for signaling server to start", end="")
        while not os.path.exists("signaling_server/pid"):
            print(".", end="")
            time.sleep(1)
        print("done")
