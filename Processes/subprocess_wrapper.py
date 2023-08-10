# type:ignore
import subprocess
import platform
from typing import Any
from Common.config import TARI_DAN_BINS_FOLDER, TARI_BINS_FOLDER


class SubprocessWrapper:
    def call(*args: Any, **kwargs: Any) -> int:
        if type(args[0]) == list and platform.system() == "Windows":
            if args[0][0].startswith(TARI_BINS_FOLDER) or args[0][0].startswith(TARI_DAN_BINS_FOLDER):
                args[0][0] += ".exe"
            elif args[0][0] == "npm":
                args[0][0] += ".cmd"
            return subprocess.call(" ".join(args[0]), *args[1:], **kwargs)
        else:
            return subprocess.call(*args, **kwargs)

    def Popen(*args: Any, **kwargs: Any) -> subprocess.Popen[Any]:
        if type(args[0]) == list and platform.system() == "Windows":
            if args[0][0].startswith(TARI_BINS_FOLDER) or args[0][0].startswith(TARI_DAN_BINS_FOLDER):
                args[0][0] += ".exe"
            elif args[0][0] == "npm":
                args[0][0] += ".cmd"
            return subprocess.Popen(" ".join(args[0]), *args[1:], **kwargs)
        else:
            return subprocess.Popen(*args, **kwargs)

    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if type(args[0]) == list and platform.system() == "Windows":
            if args[0][0].startswith(TARI_BINS_FOLDER) or args[0][0].startswith(TARI_DAN_BINS_FOLDER):
                args[0][0] += ".exe"
            elif args[0][0] == "npm":
                args[0][0] += ".cmd"
            return subprocess.run(" ".join(args[0]), *args[1:], **kwargs)
        else:
            return subprocess.run(*args, **kwargs)
