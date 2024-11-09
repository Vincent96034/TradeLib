from abc import ABC, abstractmethod

from tradelib.utils import setup_logger

logger = setup_logger(__name__)


class Strategy(ABC):
    """Base class for strategies."""

    def __init__(self):
        self.strategy_name = self.__class__.__name__
        self.weights = {}

    @abstractmethod
    def run_strategy(self):
        """Runs the selected strategy."""
        raise NotImplementedError("Strategy not yet implemented.")
