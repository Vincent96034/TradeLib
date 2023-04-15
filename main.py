from Logger.config_logger import setup_logger
from UserSettings.Configuration import RunConfiguration
from StrategyService.StrategyClass import Strategy
from TradeHandlerService.TradingBackends.LemonClass import Lemon
from TradeHandlerService.TradeData import Portfolio
from TradeHandlerService.TradeTranslator import TradeHandler



def main():
    logger = setup_logger(__name__)

    settings_source = "usersettings.json"
    config = RunConfiguration(settings_source)
    lemon = Lemon(config.LM_data_key, config.LM_trading_key, config.LM_trading_type)

    portfolio = Portfolio(
        positions = lemon.get_positions(),
        trades = lemon.get_trades(),
        trading_backend=lemon
    )

    # run strategy
    # TODO: update this to reflect new strategy setup
    config.strategy = "hold"
    strategy = Strategy(strategy_name = config.strategy,
                        strategy_params=config.strategy_params,
                        portfolio = portfolio)
    strategy.run_strategy_wrapper()

    pf_dict, pf_value = portfolio.get_portfolio()

    # translate to trade instructions and place orders
    trade_handler = TradeHandler()
    trade_handler.create_rebalance_frame(
        portfolio_dict=pf_dict,
        portfolio_value=pf_value,
        w_new = strategy.weights,
        add_value=0
    )
    trade_handler.create_trade_instructions()

    # place orders
    lemon.place_multi_order(trade_handler.trade_instructions, pf_dict)

    # wait 30 days and repeat
    logger.info("Cycle ended. Standby for 30 days.")




if __name__ == "__main__":
    main()