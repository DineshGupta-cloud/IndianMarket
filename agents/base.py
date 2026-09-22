from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Base class for all research agents."""

    name: str = "BaseAgent"

    def __init__(self, ticker: str, **kwargs):
        self.ticker = ticker.upper()
        self.ns_ticker = f"{self.ticker}.NS"
        self.context = kwargs

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Execute the agent and return structured results."""
        pass

    def log(self, message: str):
        print(f"  [{self.name}] {message}")
