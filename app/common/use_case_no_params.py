from abc import ABC, abstractmethod
from typing import TypeVar, Generic

Output = TypeVar("Output")


class UseCaseNoParams(ABC, Generic[Output]):
    @abstractmethod
    def execute(self) -> Output:
        pass
