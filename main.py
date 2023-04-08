from Logger.config_logger import setup_logger
from UserSettings.Configuration import RunConfiguration
from StrategyService.StrategyClass import Strategy
from TradeHandlerService.LemonClass import Lemon
from TradeHandlerService.TradeTranslator import TradeHandler



def main():
    logger = setup_logger(__name__)

    settings_source = "usersettings.json"
    config = RunConfiguration(settings_source)
    
    lemon = Lemon(config)
    #data = DataService()

    # run strategy
    config.strategy = "hold"
    strategy = Strategy(strategy_name = config.strategy,
                        strategy_params=config.strategy_params,
                        lemon = lemon)
    strategy.run_strategy_wrapper()

    # translate to trade instructions and place orders
    trade_handler = TradeHandler(config = config,
                                 lemon = lemon)
    trade_handler.create_rebalance_frame(strategy.weights)
    trade_handler.create_trade_instructions()

    # place orders
    lemon.place_multi_order(trade_handler.trade_instructions)

    # wait 30 days and repeat
    logger.info("Cycle ended. Standby for 30 days.")




if __name__ == "__main__":
    main()