from __future__ import annotations
from UserSettings.Configuration import RunConfiguration
from TradeHandlerService.LemonClass import Lemon

from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class Strategy:

    def __init__(self, config: RunConfiguration, lemon: Lemon):
        self.weights = {}
        self.strategy_method = config.strategy
        self.strategy_object = None
        self.lemon = lemon
    

    def run_strategy_wrapper(self):
        ''' Runs the selected strategy on the current object instance of the StrategyCls class. '''
        strategy = strategy_factory(self.strategy_method)(StrategyCls = self)
        strategy.strategy_run()
        self.strategy_object = strategy
        self.weights = strategy.weights
        logger.info(f"Ran strategy: {strategy.__class__}")



def strategy_factory(method: str):
    '''
    A factory function that returns an instance of a strategy class, specified by the `method` argument.

    Parameters:
    method (str): The name of the strategy to be returned. 
                Accepted values are "pca" and "hold".

    Returns:
    class: An instance of the specified strategy class, or None if the `method` is not recognized.
    '''
    from StrategyService.Strategies.Hold_Strategy import Hold_Strategy
    from StrategyService.Strategies.PCA_Strategy import PCA_Strategy

    strategy_dict = {
        "pca": PCA_Strategy,
        "hold": Hold_Strategy,
    }
    return strategy_dict.get(method, Hold_Strategy)
