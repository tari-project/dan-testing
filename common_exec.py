import os
import signal
from subprocess_wrapper import SubprocessWrapper
import subprocess
from ports import ports
from typing import Optional, Any, Union
from config import NAME_COLOR, COLOR_RESET, EXEC_COLOR, DATA_FOLDER
import psutil
import os


def kill_process_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.send_signal(signal.SIGTERM)
        parent.send_signal(signal.SIGTERM)
    except psutil.NoSuchProcess:
        pass


class CommonExec:
    def __init__(self, name: str, id: Optional[int] = None):
        self.env: dict[str, str] = {}
        self.id = id
        if id is not None:
            self.name = f"{name}_{id}"
        else:
            self.name = name
        self.exec = ""
        self.process: Optional[subprocess.Popen[Any]] = None

    def get_port(self, interface: str) -> int:
        return ports.get_free_port(f"{self.name} {interface}")

    def run(self, redirect: Union[bool, int], cwd: Optional[str] = None):
        env: dict[str, str] = os.environ.copy()
        if (self.id is not None and self.id >= redirect) or (not self.id and redirect):
            self.process = SubprocessWrapper.Popen(
                self.exec,
                stdin=subprocess.PIPE,
                stdout=open(os.path.join(DATA_FOLDER, "stdout", f"{self.name}.log"), "a+"),
                stderr=subprocess.STDOUT,
                env={**env, **self.env},
                cwd=cwd,
            )
        else:
            self.process = SubprocessWrapper.Popen(self.exec, stdin=subprocess.PIPE, env={**env, **self.env}, cwd=cwd)

    def __del__(self):
        print(f"Kill {NAME_COLOR}{self.name}{COLOR_RESET}")
        print(f"To run {EXEC_COLOR}{' '.join(self.exec)}{COLOR_RESET}", end=" ")
        if self.env:
            print(f"With env {EXEC_COLOR}{self.env}{COLOR_RESET}", end="")
        print()
        if self.process:
            try:
                self.process.send_signal(signal.CTRL_C_EVENT)
            except:
                pass
            kill_process_tree(self.process.pid)
            if self.process:
                self.process.kill()
            del self.process

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
