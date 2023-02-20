from UserSettings.Configuration import RunConfiguration
from TradeHandlerService.LemonClass import Lemon
from StrategyService.StrategyFactory import strategy_factory

from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class Strategy:

    def __init__(self, config: RunConfiguration, lemon: Lemon):
        self.weights = {}
        self.strategy_method = config.strategy
        self.strategy_object = None
        self.lemon = lemon
    

    def run_strategy_wrapper(self):
        ''' xxx '''
        strategy = strategy_factory(self.strategy_method)(StrategyCls = self)
        strategy.strategy_run()
        self.strategy_object = strategy
        self.weights = strategy.weights
        logger.info(f"Ran strategy: {strategy.__class__}")
