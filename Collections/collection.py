from abc import ABC, abstractmethod
from typing import TypeVar, Generic

Item = TypeVar("Item")


class Collection(ABC, Generic[Item]):
    def __init__(self):
        self.items: dict[int, Item] = {}

    def has(self, id: int) -> bool:
        return id in self.items

    @abstractmethod
    def add(self):
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

    def stop(self, id: int):
        if self.has(id):
            del self.items[id]
        print(f"Id ({id}) is invalid, either it never existed or you already stopped it")
