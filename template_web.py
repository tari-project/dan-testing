from Common.config import DATA_FOLDER, TEMPLATE_WEB_PORT
from Processes.common_exec import CommonExec
from Processes.subprocess_wrapper import SubprocessWrapper
import subprocess


class TemplateWebServer(CommonExec):
    def __init__(self, signaling_server_address: str):
        super().__init__("template-web")
        SubprocessWrapper.call(
            ["npm", "install"],
            stdin=subprocess.PIPE,
            stdout=open(f"{DATA_FOLDER}/stdout/template-web_install.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="template-web",
        )
        if TEMPLATE_WEB_PORT == "auto":
            self.http_port = self.get_port("HTTP")
        else:
            self.http_port = int(TEMPLATE_WEB_PORT)
        self.exec = ["npm", "--prefix", "template-web", "run", "dev", "--", "--port", str(self.http_port), "--host", "0.0.0.0"]
        self.env["VITE_SIGNALING_SERVER_ADDRESS"] = signaling_server_address
        self.run()
