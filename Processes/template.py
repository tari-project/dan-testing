# type:ignore
import struct

from Common.config import (
    TARI_DAN_BINS_FOLDER,
    USE_BINARY_EXECUTABLE,
    DATA_FOLDER,
)
from Common.ports import ports
from Processes.dan_wallet_daemon import JrpcDanWalletDaemon
from typing import Any
from Processes.subprocess_wrapper import SubprocessWrapper
import re
import os
import array
import subprocess

cargo_install_generate_installed = False


class Template:
    def __init__(self, template, name=None, from_source=True):
        self.template = template
        self.name = name or template
        self.from_source = from_source
        if from_source:
            self.generate()
            self.compile()

    def generate(self):
        try:
            os.makedirs(os.path.join(DATA_FOLDER, "templates"))
        except:
            pass

        global cargo_install_generate_installed
        if not cargo_install_generate_installed:
            cargo_install_generate_installed = True
            exec = ["cargo", "install", "cargo-generate"]
            SubprocessWrapper.call(
                exec,
                stdout=open(os.path.join(DATA_FOLDER, "stdout", f"cargo_generate_install.log"), "a+"),
                stderr=subprocess.STDOUT,
            )

        exec = ["cargo", "generate", "--git", "https://github.com/tari-project/wasm-template.git", "-s", self.template, "-n", self.name]
        SubprocessWrapper.call(
            exec,
            stdout=open(os.path.join(DATA_FOLDER, "stdout", f"template_{self.name}_cargo_generate.log"), "a+"),
            stderr=subprocess.STDOUT,
            cwd=os.path.join(DATA_FOLDER, "templates"),
        )

    def compile(self):
        wd = os.getcwd()
        os.chdir(os.path.join(DATA_FOLDER, "templates", self.name, "package"))
        exec = ["cargo", "build", "--target", "wasm32-unknown-unknown", "--release"]
        SubprocessWrapper.call(
            exec,
            stdout=open(os.path.join("..", "..", "..", "stdout", f"template_{self.name}_cargo_build.log"), "a+"),
            stderr=subprocess.STDOUT,
        )
        os.chdir(wd)

    def publish_template(self, jrpc_port: int, server_port: int, local_ip: str):
        if USE_BINARY_EXECUTABLE:
            run = [os.path.join(TARI_DAN_BINS_FOLDER, "tari_validator_node_cli")]
        else:
            run = [
                "cargo",
                "run",
                "--bin",
                "tari_validator_node_cli",
                "--manifest-path",
                os.path.join("..", "tari-dan", "Cargo.toml"),
                "--",
            ]

        if self.from_source:
            exec = [
                *run,
                "--vn-daemon-jrpc-endpoint",
                f"/ip4/{local_ip}/tcp/{jrpc_port}",
                "templates",
                "publish",
                "--binary-url",
                f"http://localhost:{server_port}/templates/{self.name}/package/target/wasm32-unknown-unknown/release/{self.name}.wasm",
                "--template-code-path",
                os.path.join(DATA_FOLDER, "templates", self.name, "package"),
                "--template-name",
                f"{self.name}",
                "--template-version",
                "1",
                "--template-type",
                "wasm",
            ]
        else:
            exec = [
                *run,
                "--vn-daemon-jrpc-endpoint",
                f"/ip4/{local_ip}/tcp/{jrpc_port}",
                "templates",
                "publish",
                "--binary-url",
                f"http://localhost:{server_port}/templates/{self.template}",
                # "--template-code-path",
                # os.path.join(DATA_FOLDER, "templates", self.name, "package"),
                "--template-name",
                f"{self.name}",
                "--template-version",
                "1",
                "--template-type",
                "wasm",
            ]

        result = SubprocessWrapper.run(exec, stdout=subprocess.PIPE)
        if r := re.search(r"The template address will be ([0-9a-f]{64})", result.stdout.decode()):
            self.id = r.group(1)
            print("Address:", self.id)
        else:
            print("Registration failed", result.stdout.decode())

    def call_function(self, function_name: str, dan_wallet_client: JrpcDanWalletDaemon, params: list[Any] = [], dump_into_account: bool = True):
        for p in range(len(params)):
            if params[p].startswith("w:"):
                params[p] = f"Workspace({params[p][2:]})"
        result = dan_wallet_client.transaction_submit_instruction(
            {
                "CallFunction": {
                    "template_address": self.id,
                    "function": function_name,
                    "args": params,
                }
            },
            dump_buckets=dump_into_account,
        )
        print(result)
        return result
