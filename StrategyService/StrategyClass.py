from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class Strategy:

    def __init__(self):
        self.strategy_name = self.__class__.__name__
        self.weights = {}

    def run_strategy(self):
        ''' Runs the selected strategy. '''
        raise NotImplementedError("Strategy not yet implemented.")