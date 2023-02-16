from UserSettings.Configuration import RunConfiguration
from StrategyService.Strategy import Strategy
from TradeHandlerService.LemonClass import Lemon
#from TradeHandlerService.trade_handler import TradeHandler


settings_source = "usersettings.json"


def main():

    # e.g. get strategy setting useing config.strategy
    config = RunConfiguration(settings_source)

    # run strategy
    strategy = Strategy(config)
    strategy.run_strategy_wrapper()
    # OUT: strategy.weights


    # translate to trade instructions and place orders
    #trade_handler = TradeHandler(config)
    #trade_handler.restructure(strategy.weights)
    lemon = Lemon(config)
    lemon.get_bank_statements()

    # wait 30 days and repeat
    print("finished cycle")





if __name__ == "__main__":
    main()
