from Logger.config_logger import setup_logger
from UserSettings.Configuration import RunConfiguration
from StrategyService.Strategy import Strategy
from TradeHandlerService.LemonClass import Lemon
#from TradeHandlerService.trade_handler import TradeHandler


settings_source = "usersettings.json"


def main():
    logger = setup_logger(__name__)

    # e.g. get strategy setting useing config.strategy
    config = RunConfiguration(settings_source)
    lemon = Lemon(config)
    #data = DataService()

    # run strategy
    strategy = Strategy(config, lemon) # data
    strategy.run_strategy_wrapper()
    new_portfolio = strategy.weights

    # translate to trade instructions and place orders
    #trade_handler = TradeHandler(config)
    #trade_handler.restructure(strategy.weights)


    # wait 30 days and repeat
    logger.info("Cycle ended. Standby for 30 days.")




if __name__ == "__main__":
    main()
