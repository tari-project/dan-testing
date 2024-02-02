from commands import Commands
from Common.config import DATA_FOLDER, WEBUI_PORT
from Common.local_ip import local_ip
from Common.ports import ports
from http.server import BaseHTTPRequestHandler, HTTPServer
from jsonrpcserver import method, Result, Success, dispatch, InvalidParams, Error
from Processes.common_exec import CommonExec
from Processes.subprocess_wrapper import SubprocessWrapper
from Processes.template import Template
from typing import Any, Optional
import cgi
import os
import subprocess
import threading
import webbrowser
import process_type


class JrpcHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.commands: Commands = server.commands
        super().__init__(request, client_address, server)
        self.define_methods()

    def do_POST(self):
        if self.path == "/upload_template":
            content_type, _ = cgi.parse_header(self.headers["Content-Type"])
            if content_type == "multipart/form-data":
                form_data = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
                if "file" in form_data:
                    uploaded_file = form_data["file"]
                    try:
                        os.makedirs(os.path.join(DATA_FOLDER, "templates"))
                    except:
                        pass
                    path = f"{uploaded_file.filename}"
                    if os.path.exists(os.path.join(DATA_FOLDER, "templates", path)):
                        os.remove(os.path.join(DATA_FOLDER, "templates", path))
                    f = open(os.path.join(DATA_FOLDER, "templates", uploaded_file.filename), "wb")
                    f.write(uploaded_file.file.read())
                    f.close()
                    template = Template(path, uploaded_file.filename, from_source=False)
                    template.publish_template(self.commands.validator_nodes.any_node().json_rpc_port, self.commands.server.port, local_ip)
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    return
        # Process request
        request = self.rfile.read(int(self.headers["Content-Length"])).decode()
        response = dispatch(request, validator=lambda _: None)  # type:ignore
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

    def log_message(self, format: str, *args: Any) -> None:
        # This will shutdown the logs to stdout
        return

    def define_methods(self):
        @method
        def ping() -> Result:  # type:ignore
            return Success("pong")

        @method
        def base_nodes() -> Result:  # type:ignore
            res = {}
            for id in self.commands.base_nodes:
                res[id] = self.commands.base_nodes[id].get_info_for_ui()
            return Success(res)

        @method
        def base_wallets() -> Result:  # type:ignore
            res = {}
            for id in self.commands.base_wallets:
                res[id] = self.commands.base_wallets[id].get_info_for_ui()
            return Success(res)

        @method
        def vns() -> Result:  # type:ignore
            res = {}
            for id in self.commands.validator_nodes:
                res[id] = self.commands.validator_nodes[id].get_info_for_ui()
            return Success(res)

        @method
        def dan_wallets() -> Result:  # type:ignore
            res = {}
            for id in self.commands.dan_wallets:
                res[id] = self.commands.dan_wallets[id].get_info_for_ui()
            return Success(res)

        @method
        def indexers() -> Result:  # type:ignore
            res = {}
            for id in self.commands.indexers:
                res[id] = self.commands.indexers[id].get_info_for_ui()
            return Success(res)

        @method
        def mine(blocks: int) -> Result:  # type:ignore
            self.commands.mine(blocks)
            return Success()

        @method
        def jrpc(what: str) -> Result:  # type:ignore
            jrpc_address = self.commands.jrpc(what)
            if jrpc_address:
                return Success(jrpc_address)
            return InvalidParams()

        @method
        def burn(public_key: str, outfile: str, amount: int) -> Result:  # type:ignore
            self.commands.burn(public_key, outfile, amount)
            return Success()

        @method
        def get_logs(what: Optional[str]) -> Result:  # type:ignore
            try:
                if what is None:
                    logs: list[tuple[str, str, str]] = []
                    for path, _dirs, files in os.walk(DATA_FOLDER):
                        for file in files:
                            if not path.endswith("stdout"):
                                if file.endswith(".log"):
                                    logs.append((os.path.join(path, file), os.path.split(path)[1], os.path.splitext(file)[0]))  # type:ignore
                    return Success(logs)
                if process_type.is_miner(what):
                    return Success(self.commands.miner.get_logs())
                if process_type.is_connector(what):
                    if self.commands.tari_connector_sample:
                        return Success(self.commands.tari_connector_sample.get_logs())
                    return Success("Not running")
                if process_type.is_signaling_server(what):
                    return Success(self.commands.signaling_server.get_logs())
                id = process_type.get_index(what)
                if id is None:
                    return InvalidParams()
                if process_type.is_validator_node(what):
                    if id in self.commands.validator_nodes:
                        return Success(self.commands.validator_nodes[id].get_logs())
                if process_type.is_asset_wallet(what):
                    if id in self.commands.dan_wallets:
                        return Success(self.commands.dan_wallets[id].get_logs())
                if process_type.is_indexer(what):
                    if id in self.commands.indexers:
                        return Success(self.commands.indexers[id].get_logs())
                if process_type.is_base_node(what):
                    if self.commands.base_nodes.has(id):
                        return Success(self.commands.base_nodes[id].get_logs())
                if process_type.is_base_wallet(what):
                    if self.commands.base_wallets.has(id):
                        return Success(self.commands.base_wallets[id].get_logs())
                return InvalidParams()
            except Exception as error:
                Error(error)
            return Error("Unknown")

        @method
        def get_stdout(what: Optional[str]) -> Result:  # type:ignore
            print("GetStdout", what)
            try:
                if what is None:
                    logs: list[tuple[str, str]] = []
                    for path, _dirs, files in os.walk(os.path.join(DATA_FOLDER, "stdout")):
                        for file in files:
                            logs.append((os.path.join(path, file), os.path.splitext(file)[0]))
                    return Success(logs)
                if process_type.is_miner(what):
                    return Success(self.commands.miner.get_stdout())
                if process_type.is_connector(what):
                    if self.commands.tari_connector_sample:
                        return Success(self.commands.tari_connector_sample.get_stdout())
                    else:
                        return Success("Not running")
                if process_type.is_signaling_server(what):
                    return Success(self.commands.signaling_server.get_stdout())
                id = process_type.get_index(what)
                if id is None:
                    return InvalidParams()
                if process_type.is_validator_node(what):
                    if id in self.commands.validator_nodes:
                        return Success(self.commands.validator_nodes[id].get_stdout())
                if process_type.is_asset_wallet(what):
                    if id in self.commands.dan_wallets:
                        return Success(self.commands.dan_wallets[id].get_stdout())
                if process_type.is_indexer(what):
                    if id in self.commands.indexers:
                        return Success(self.commands.indexers[id].get_stdout())
                if process_type.is_base_node(what):
                    if self.commands.base_nodes.has(id):
                        return Success(self.commands.base_nodes[id].get_stdout())
                if process_type.is_base_wallet(what):
                    if self.commands.base_wallets.has(id):
                        return Success(self.commands.base_wallets[id].get_stdout())
                return InvalidParams()
            except Exception as error:
                Error(error)
            return Error("Unknown")

        @method
        def get_file(filename: str) -> Result:  # type:ignore
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
    def __init__(self, jrpc_webui_server_address: str, local_ip: str):
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
        self.exec = ["npm", "--prefix", "webui", "run", "dev", "--", "--port", str(self.http_port), "--host", "0.0.0.0"]
        self.env["VITE_DAEMON_JRPC_ADDRESS"] = jrpc_webui_server_address
        self.run(True)
        if WEBUI_PORT == "auto":
            webbrowser.open(f"http://{local_ip}:{self.http_port}")


class JrpcWebuiServer:
    def __init__(self, commands: Commands):
        self.port: int = ports.get_free_port("JRPC Server")
        server_address: tuple[str, int] = ("0.0.0.0", self.port)
        self.httpd = JrpcServer(commands, server_address, JrpcHandler)
        self.server = threading.Thread(target=self.httpd.serve_forever)
        self.server.start()
        self.webui = WebuiServer(f"{local_ip}:{self.port}", local_ip)

    def __del__(self):
        # TODO: Figure out how to stop the server on windows. Once any of the @method above is called, the server will be unstoppable
        if self.httpd:
            self.httpd.shutdown()
