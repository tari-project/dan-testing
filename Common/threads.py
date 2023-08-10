import threading
import time
from typing import Any, Callable


class Threads:
    def __init__(self):
        self.threads: list[threading.Thread] = []

    def set_semaphore_limit(self, limit: int):
        if limit:
            self.semaphore = threading.Semaphore(limit)
        else:
            self.semaphore = None

    def add(self, target: Callable[..., None], args: Any):
        def thread_target(target: Callable[..., None], args: Any):
            if self.semaphore:
                self.semaphore.acquire()
            target(*args)
            if self.semaphore:
                self.semaphore.release()

        thread = threading.Thread(target=thread_target, args=(target, args))
        self.threads.append(thread)
        thread.start()

    def wait(self):
        for thread in self.threads:
            thread.join()
        self.threads = []


threads = Threads()
threads.set_semaphore_limit(10)
