from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from Processes.common_exec import CommonExec

Item = TypeVar("Item", bound=CommonExec)


class Collection(ABC, Generic[Item]):
    def __init__(self):
        self.items: dict[int, Item] = {}

    def has(self, id: int) -> bool:
        return id in self.items

    @abstractmethod
    def add(self) -> str:
        pass

    def any(self) -> Item:
        return next(iter(self.items.values()))

    def __del__(self):
        for item in self.items.values():
            del item

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, id: int) -> Item:
        return self.items[id]

    def start(self, id: int) -> bool:
        if self.has(id):
            return self.items[id].run()
        return False

    def stop(self, id: int) -> bool:
        if self.has(id) and self.items[id].is_running():
            return self.items[id].stop()
        print(f"Id ({id}) is invalid, either it never existed or you already stopped it")
        return False

    def is_running(self, id: int) -> bool:
        return self.items[id].is_running()
