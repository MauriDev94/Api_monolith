from abc import ABC, abstractmethod
from typing import Generic, TypeVar

Output = TypeVar("Output")


class UseCaseNoParams(ABC, Generic[Output]):
    """Base contract for use cases that do not require input parameters."""

    @abstractmethod
    def execute(self) -> Output:
        """Execute business flow and return a result."""
        pass
