from UserSettings.Configuration import RunConfiguration
from StrategyService.StrategyFactory import strategy_factory


class Strategy:

    def __init__(self, config: RunConfiguration):
        self.weights = []
        self.strategy_method = config.strategy
        self.strategy_object = None
    

    def run_strategy_wrapper(self):
        
        strategy = strategy_factory(self.strategy_method)()
        strategy.strategy_run()

        self.strategy_object = strategy
    