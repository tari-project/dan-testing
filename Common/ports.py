import socket, errno
import sys
import threading
from Common.config import NAME_COLOR, COLOR_RESET, COLOR_BRIGHT_CYAN


def is_port_used(port: int):
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sck.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno != errno.EADDRINUSE:
            print(f"Some error on getting port usage {e}")
            sys.stdout.flush()
        return True
    sck.close()
    return False


class Ports:
    def __init__(self):
        self.last_used = 18003
        self.mutex = threading.Lock()
        self.assigned_ports: dict[str, int] = {}

    def assign_port(self, name: str) -> int:
        self.mutex.acquire()
        self.last_used += 1
        while is_port_used(self.last_used):
            self.last_used += 1
        last_used = self.last_used
        self.mutex.release()
        print(f"Port {COLOR_BRIGHT_CYAN}{self.last_used}{COLOR_RESET} has been assigned to {NAME_COLOR}{name}{COLOR_RESET}")
        sys.stdout.flush()
        return last_used

    def get_free_port(self, name: str) -> int:
        if name in self.assigned_ports:
            return self.assigned_ports[name]
        self.assigned_ports[name] = self.assign_port(name)
        return self.assigned_ports[name]


ports = Ports()
