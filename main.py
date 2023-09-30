# from Logger.config_logger import setup_logger
from UserSettings.configuration import RunConfiguration
from StrategyService.Strategies.pca_strategy import PCA_Strategy
from TradeHandlerService.TradingBackends.alpaca_class import Alpaca
from TradeHandlerService.portfolio import Portfolio
from TradeHandlerService.trade_translator import TradeHandler
from Logger.config_logger import setup_logger


def main():
    """Default run"""
    logger = setup_logger(__name__)

    settings_source = "usersettings.json"
    config = RunConfiguration(settings_source)
    alpaca = Alpaca(config.alpaca_secret,
                    config.alpaca_key,
                    config.alpaca_paper)
    portfolio = Portfolio(trading_backend=alpaca)
    portfolio.initialize()

    # run strategy
    strategy = PCA_Strategy(
        ratio=0.12,
        company_pool="NASDAQ100",
        portfolio_type="tail",
        factor_estimate_cov=True
    )
    strategy.run_strategy()
    logger.info("Strategy calculated.")

    # translate to trade instructions
    trade_handler = TradeHandler()
    trade_handler.create_rebalance_frame(
        portfolio_dict=portfolio.get_portfolio_weights(),
        portfolio_value=portfolio.total_value,
        w_new=strategy.weights,
        add_value=0
    )

    trade_handler.create_trade_instructions()
    logger.info("Trade instruction calculated.")
    logger.info(trade_handler.trade_instructions)

    # place orders
    logger.info("Placing orders ...")
    alpaca.place_multi_order(trade_handler.trade_instructions)


if __name__ == "__main__":
    main()
