import threading
from collections import defaultdict
from time import time
import statistics


class Stats:
    def __init__(self):
        self.mutex = threading.Lock()
        self.id = 0
        self.counter: dict[str, int] = defaultdict(int)
        self.times: dict[str, list[float]] = defaultdict(list)
        self.names: dict[int, str] = {}
        self.start_time: dict[int, float] = {}

    def start_run(self, name: str) -> int:
        self.mutex.acquire()
        id = self.id
        self.id += 1
        self.mutex.release()
        self.start_time[id] = time()
        self.names[id] = name
        return id

    def end_run(self, id: int):
        self.mutex.acquire()
        end = time()
        name = self.names[id]
        self.counter[name] += 1
        self.times[name].append(end - self.start_time[id])
        self.mutex.release()

    def __repr__(self):
        res: list[str] = []
        for name in self.counter:
            res.append(
                f"{name} was called {self.counter[name]} times, with total_runtime {sum(self.times[name]):.2f}s, average time {sum(self.times[name])/len(self.times[name]):.2f}s, maximum time {max(self.times[name]):.2f}s, median time {statistics.median(self.times[name]):.2f}s"
            )
        return "\n".join(res)


stats = Stats()
