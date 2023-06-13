# type:ignore
from config import REDIRECT_DAN_WALLET_WEBUI_STDOUT, DATA_FOLDER
from ports import ports
import os
from subprocess_wrapper import SubprocessWrapper
import signal
import subprocess
from common_exec import CommonExec


class TariConnectorSample(CommonExec):
    def __init__(self, signaling_server_address):
        super().__init__("connector-sample")
        npm = "npm"
        self.http_port = self.get_port("HTTP")

        # first do npm install in tari-connector repo
        self.process = SubprocessWrapper.call(
            [npm, "install"],
            stdin=subprocess.PIPE,
            stdout=open(f"{DATA_FOLDER}/stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector",
        )

        # create tari-connector link
        self.process = SubprocessWrapper.call(
            [npm, "link"],
            stdin=subprocess.PIPE,
            stdout=open(f"{DATA_FOLDER}/stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector",
        )
        # install everything
        self.process = SubprocessWrapper.call(
            [npm, "install"],
            stdin=subprocess.PIPE,
            stdout=open(f"{DATA_FOLDER}/stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector/examples/material-vite-ts",
        )
        # link tari-connector package
        self.process = SubprocessWrapper.call(
            [npm, "link", "tari-connector"],
            stdin=subprocess.PIPE,
            stdout=open(f"{DATA_FOLDER}/stdout/tari-connector_prepare.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="../tari-connector/examples/material-vite-ts",
        )
        # run the project
        self.exec = [npm, "run", "dev", "--", "--port", str(self.http_port)]
        self.env["VITE_SIGNALING_SERVER_ADDRESS"] = signaling_server_address
        self.run(
            REDIRECT_DAN_WALLET_WEBUI_STDOUT,
            "../tari-connector/examples/material-vite-ts",
        )
