from typing import Optional

from TradeHandlerService.LemonClass import Lemon
from StrategyService.StrategyClass import Strategy
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class Portfolio:
    def __init__(self,
                 lemon: Lemon,
                 strategy = None,
                 profilers: list = []):
        self.lemon = lemon
        self.strategy = strategy
        self.profilers = profilers
        self.loaded_profilers = []
        self.result = {}
        self.valid_profiler_inputs = {
            "lemon": self.lemon,
            "strategy": self.strategy}
        self.validate_inputs()

    def validate_inputs(self):
        """ Validate inputs of Porfolio Class."""
        if not isinstance(self.profilers, list):
            raise TypeError("`profilers` must be a list")
        if not isinstance(self.lemon, Lemon):
            raise TypeError("`lemon` must be an instance of Lemon")
        if not isinstance(self.strategy, Strategy):
            raise TypeError("`strategy` must be an instance of Strategy")

    def add_profiler(self, profiler):
        """ Provides profiler with needed input and adds it to the list `loaded_profilers`."""
        profiler.input = self.valid_profiler_inputs[profiler.get_required_input()]
        self.loaded_profilers.append(profiler)

    def load_profilers(self):
        for profiler in self.loaded_profilers:
            profiler.input = self.valid_profiler_inputs[profiler.get_required_input()]
            name = profiler.get_name()
            self.result[name] = profiler.run_profiler()


    