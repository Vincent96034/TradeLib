from TradeHandlerService.TradeData import Portfolio
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class Strategy:

    def __init__(self, strategy_name: str, strategy_params: dict, portfolio: Portfolio):
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        self.strategy_object = None
        self.weights = {}
        self.portfolio = portfolio
    

    def run_strategy_wrapper(self):
        ''' Runs the selected strategy on the current object instance of the StrategyCls class. '''
        strategy = strategy_factory(self.strategy_name)(StrategyCls = self)
        strategy.strategy_run()
        self.strategy_object = strategy
        self.weights = strategy.weights
        logger.info(f"Ran strategy: {self.strategy_name}")



def strategy_factory(strategy_name: str):
    '''
    A factory function that returns an instance of a strategy class, specified by the `strategy_name` argument.

    Parameters:
    strategy_name (str): The name of the strategy to be returned. 
                Accepted values are "pca" and "hold".

    Returns:
    class: An instance of the specified strategy class, or "hold" if the `strategy_name` is not recognized.
    '''
    from StrategyService.Strategies.Hold_Strategy import Hold_Strategy
    from StrategyService.Strategies.PCA_Strategy import PCA_Strategy

    strategy_dict = {
        "pca": PCA_Strategy,
        "hold": Hold_Strategy,
    }
    return strategy_dict.get(strategy_name, Hold_Strategy)
