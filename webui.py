from common_exec import CommonExec
from config import DATA_FOLDER, WEBUI_PORT
from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpcserver import method, Result, Success, dispatch, InvalidParams, Error
from ports import ports
from subprocess_wrapper import SubprocessWrapper
from typing import Type, Any, Optional
from commands import Commands
import subprocess
import threading
import http
import json
import os
import webbrowser


class JrpcHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.commands: Commands = server.commands
        super().__init__(request, client_address, server)

    def do_POST(self):
        # Process request
        request = self.rfile.read(int(self.headers["Content-Length"])).decode()
        self.define_methods()
        response = dispatch(request, validator=lambda _: None)
        # Return response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()
        self.wfile.write(response.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def define_methods(self):
        @method
        def ping() -> Result:
            return Success("pong")

        @method
        def vns() -> Result:
            res = {}
            for id in self.commands.validator_nodes:
                res[id] = self.commands.validator_nodes[id].get_info_for_ui()
            return Success(res)

        @method
        def dan_wallets() -> Result:
            res = {}
            for id in self.commands.dan_wallets:
                res[id] = self.commands.dan_wallets[id].get_info_for_ui()
            return Success(res)

        @method
        def indexers() -> Result:
            res = {}
            for id in self.commands.indexers:
                res[id] = self.commands.indexers[id].get_info_for_ui()
            return Success(res)

        @method
        def http_vn(id: int) -> Result:
            http_address = self.commands.http_vn(id)
            if http_address:
                return Success(http_address)
            return InvalidParams()

        @method
        def http_dan(id: int) -> Result:
            http_address = self.commands.http_dan(id)
            if http_address:
                return Success(http_address)
            return InvalidParams()

        @method
        def http_indexer(id: int) -> Result:
            http_address = self.commands.http_indexer(id)
            if http_address:
                return Success(http_address)
            return InvalidParams()

        @method
        def http_connector(id: int) -> Result:
            http_address = self.commands.http_connector(id)
            if http_address:
                return Success(http_address)
            return InvalidParams()

        @method
        def mine(blocks: int) -> Result:
            self.commands.mine(blocks)
            return Success()

        @method
        def jrpc_vn(id: int) -> Result:
            jrpc_address = self.commands.jrpc_vn(id)
            if jrpc_address:
                return Success(jrpc_address)
            return InvalidParams()

        @method
        def jrpc_dan(id: int) -> Result:
            jrpc_address = self.commands.jrpc_dan(id)
            if jrpc_address:
                return Success(jrpc_address)
            return InvalidParams()

        @method
        def jrpc_indexer(id: int) -> Result:
            jrpc_address = self.commands.jrpc_indexer(id)
            if jrpc_address:
                return Success(jrpc_address)
            return InvalidParams()

        @method
        def jrpc_signaling() -> Result:
            jrpc_address = self.commands.jrpc_signaling()
            if jrpc_address:
                return Success(jrpc_address)
            return InvalidParams()

        @method
        def grpc_node() -> Result:
            return Success(self.commands.grpc("node"))

        @method
        def grpc_wallet() -> Result:
            return Success(self.commands.grpc("wallet"))

        @method
        def burn(public_key: str, outfile: str, amount: int) -> Result:
            self.commands.burn(public_key, outfile, amount)
            return Success()

        @method
        def get_logs() -> Result:
            os.walk(
                os.path.join(
                    DATA_FOLDER,
                )
            )
            pass

        @method
        def get_logs(what: Optional[str]) -> Result:
            try:
                if what is None:
                    logs: list[tuple[str, str, str]] = []
                    for path, _dirs, files in os.walk(DATA_FOLDER):
                        for file in files:
                            if not path.endswith("stdout"):
                                if file.endswith(".log"):
                                    logs.append((os.path.join(path, file), os.path.split(path)[1], os.path.splitext(file)[0]))
                    return Success(logs)
                if what == "node":
                    return Success(self.commands.base_node.get_logs())
                if what == "miner":
                    return Success(self.commands.miner.get_logs())
                if what == "wallet":
                    return Success(self.commands.wallet.get_logs())
                if what == "connector":
                    return Success(self.commands.tari_connector_sample.get_logs())
                if what == "signaling_server":
                    return Success(self.commands.signaling_server.get_logs())
                if len(what.split(" ")) != 2:
                    return InvalidParams()
                what, index = what.split(" ")
                index = int(index)
                if what == "vn":
                    if index in self.commands.validator_nodes:
                        return Success(self.commands.validator_nodes[index].get_logs())
                if what == "dan":
                    if index in self.commands.dan_wallets:
                        return Success(self.commands.dan_wallets[index].get_logs())
                if what == "indexer":
                    if index in self.commands.indexers:
                        return Success(self.commands.indexers[index].get_logs())
                return InvalidParams()
            except Exception as error:
                Error(error)
            return Error("Unknown")

        @method
        def get_stdout(what: Optional[str]) -> Result:
            try:
                if what is None:
                    logs: list[tuple[str, str]] = []
                    for path, _dirs, files in os.walk(os.path.join(DATA_FOLDER, "stdout")):
                        for file in files:
                            logs.append((os.path.join(path, file), os.path.splitext(file)[0]))
                    return Success(logs)
                if what == "node":
                    return Success(self.commands.base_node.get_stdout())
                if what == "miner":
                    return Success(self.commands.miner.get_stdout())
                if what == "wallet":
                    return Success(self.commands.wallet.get_stdout())
                if what == "connector":
                    return Success(self.commands.tari_connector_sample.get_stdout())
                if what == "signaling_server":
                    return Success(self.commands.signaling_server.get_stdout())
                if len(what.split(" ")) != 2:
                    return InvalidParams()
                what, index = what.split(" ")
                index = int(index)
                if what == "vn":
                    if index in self.commands.validator_nodes:
                        return Success(self.commands.validator_nodes[index].get_stdout())
                if what == "dan":
                    if index in self.commands.dan_wallets:
                        return Success(self.commands.dan_wallets[index].get_stdout())
                if what == "indexer":
                    if index in self.commands.indexers:
                        return Success(self.commands.indexers[index].get_stdout())
                return InvalidParams()
            except Exception as error:
                Error(error)
            return Error("Unknown")

        @method
        def get_file(filename: str) -> Result:
            if os.path.exists(filename):
                file = open(filename, "rt", encoding="utf-8")
                data = file.read()
                file.close()
                return Success(data)
            return InvalidParams("File not found")


class JrpcServer(HTTPServer):
    def __init__(self, commands: Commands, server_address: Any, RequestHandlerClass: Any, bind_and_activate: bool = True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.commands = commands


class WebuiServer(CommonExec):
    def __init__(self, jrpc_webui_server_address, local_ip):
        super().__init__("webui")
        SubprocessWrapper.call(
            ["npm", "install"],
            stdin=subprocess.PIPE,
            stdout=open(f"{DATA_FOLDER}/stdout/webui_install.log", "a+"),
            stderr=subprocess.STDOUT,
            cwd="webui",
        )
        if WEBUI_PORT == "auto":
            self.http_port = self.get_port("HTTP")
        else:
            self.http_port = int(WEBUI_PORT)
        self.exec = ["npm", "--prefix", "webui", "run", "dev", "--", "--port", str(self.http_port), "--host", local_ip]
        self.env["VITE_DAEMON_JRPC_ADDRESS"] = jrpc_webui_server_address
        self.run(True)
        if WEBUI_PORT == "auto":
            webbrowser.open(f"http://{local_ip}:{self.http_port}")


class JrpcWebuiServer:
    def __init__(self, local_ip: str, commands: Commands):
        self.port: int = ports.get_free_port("JRPC Server")
        server_address: tuple[str, int] = ("0.0.0.0", self.port)
        self.httpd = JrpcServer(commands, server_address, JrpcHandler)
        self.server = threading.Thread(target=self.httpd.serve_forever)
        self.server.start()
        self.webui = WebuiServer(f"{local_ip}:{self.port}", local_ip)

    def __del__(self):
        if self.httpd:
            self.httpd.shutdown()
