import threading
from typing import Any, Callable


class Threads:
    def __init__(self):
        self.threads: list[threading.Thread] = []

    def add(self, target: Callable[..., None], args: Any):
        thread = threading.Thread(target=target, args=args)
        self.threads.append(thread)
        thread.start()

    def wait(self):
        for thread in self.threads:
            thread.join()
        self.threads = []


threads = Threads()
