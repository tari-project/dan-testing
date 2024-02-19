import os
import signal
from Processes.subprocess_wrapper import SubprocessWrapper
import subprocess
from Common.ports import ports
from typing import Optional, Any
from Common.config import NAME_COLOR, COLOR_RESET, EXEC_COLOR, DATA_FOLDER
import sys
from copy import deepcopy


class CommonExec:
    def __init__(self, name: str, id: Optional[int] = None):
        self.env: dict[str, str] = {}
        self.id = id
        if id is None:
            self.name = name
        else:
            self.name = f"{name}_{id}"
        self.exec = ""
        self.process: Optional[subprocess.Popen[Any]] = None
        all_processes[self.name] = self

    def get_port(self, interface: str) -> int:
        return ports.get_free_port(f"{self.name} {interface}")

    def run(self, cwd: Optional[str] = None) -> bool:
        if self.is_running():
            return False
        env: dict[str, str] = os.environ.copy()
        self.process = SubprocessWrapper.Popen(
            deepcopy(self.exec),
            stdin=subprocess.PIPE,
            stdout=open(os.path.join(DATA_FOLDER, "stdout", f"{self.name}.log"), "a+"),
            stderr=subprocess.STDOUT,
            env={**env, **self.env},
            cwd=cwd,
        )
        return True

    def is_running(self) -> bool:
        if self.process:
            return self.process.poll() is None
        return False

    def stop(self) -> bool:
        if not self.process or not self.is_running():
            return False
        print(f"Kill {NAME_COLOR}{self.name}{COLOR_RESET}")
        print(f"To run {EXEC_COLOR}{' '.join(self.exec).replace(' -n', '')}{COLOR_RESET}", end=" ")
        if self.env:
            print(f"With env {EXEC_COLOR}{self.env}{COLOR_RESET}", end="")
        if sys.platform == "win32":
            # You can't send ctrl+c to a process in windows without sending it to the whole process group
            self.process.send_signal(signal.SIGTERM)
        else:
            # This closes the process correctly
            self.process.send_signal(signal.SIGINT)
        del self.process
        self.process = None
        return True

    def __del__(self):
        self.stop()

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

    def get_dbs(self):
        dbs: list[tuple[str, str]] = []
        for path, _dirs, files in os.walk(os.path.join(DATA_FOLDER, self.name)):
            for file in files:
                if file.endswith(".sqlite") or file.endswith(".db"):
                    dbs.append((os.path.join(path, file), self.name))
        return dbs


all_processes: dict[str, CommonExec] = {}
