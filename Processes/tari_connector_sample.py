# type:ignore
from Common.config import REDIRECT_DAN_WALLET_WEBUI_STDOUT, DATA_FOLDER
from Common.ports import ports
import os
from Processes.subprocess_wrapper import SubprocessWrapper
import signal
import subprocess
from Processes.common_exec import CommonExec


class TariConnectorSample(CommonExec):
    def __init__(self, signaling_server_address):
        super().__init__("connector-sample")
        npm = "npm"
        self.http_port = self.get_port("HTTP")

        # first do npm install in tari-connector repo
        self.process = SubprocessWrapper.call(
            [npm, "install"],
            stdin=subprocess.PIPE,
            stdout=open(os.path.join(DATA_FOLDER, "stdout", f"tari-{self.name}_prepare.log"), "a+"),
            stderr=subprocess.STDOUT,
            cwd=os.path.join("..", "tari-connector"),
        )

        # create tari-connector link
        self.process = SubprocessWrapper.call(
            [npm, "link"],
            stdin=subprocess.PIPE,
            stdout=open(os.path.join(DATA_FOLDER, "stdout", f"tari-{self.name}_prepare.log"), "a+"),
            stderr=subprocess.STDOUT,
            cwd=os.path.join("..", "tari-connector"),
        )
        # install everything
        self.process = SubprocessWrapper.call(
            [npm, "install"],
            stdin=subprocess.PIPE,
            stdout=open(os.path.join(DATA_FOLDER, "stdout", f"tari-{self.name}_prepare.log"), "a+"),
            stderr=subprocess.STDOUT,
            cwd=os.path.join("..", "tari-connector", "examples", "material-vite-ts"),
        )
        # link tari-connector package
        self.process = SubprocessWrapper.call(
            [npm, "link", "tari-connector"],
            stdin=subprocess.PIPE,
            stdout=open(os.path.join(DATA_FOLDER, "stdout", f"tari-{self.name}_prepare.log"), "a+"),
            stderr=subprocess.STDOUT,
            cwd=os.path.join("..", "tari-connector", "examples", "material-vite-ts"),
        )
        # run the project
        self.exec = [npm, "run", "dev", "--", "--port", str(self.http_port), "--host", "0.0.0.0"]
        self.env["VITE_SIGNALING_SERVER_ADDRESS"] = signaling_server_address
        self.run(
            REDIRECT_DAN_WALLET_WEBUI_STDOUT,
            os.path.join("..", "tari-connector", "examples", "material-vite-ts"),
        )
