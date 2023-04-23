from Logger.config_logger import setup_logger
from UserSettings.Configuration import RunConfiguration
from StrategyService.Strategies.PCA_Strategy import PCA_Strategy
from TradeHandlerService.TradingBackends.LemonClass import Lemon
from TradeHandlerService.TradeData import Portfolio
from TradeHandlerService.TradeTranslator import TradeHandler



def main():
    logger = setup_logger(__name__)

    settings_source = "usersettings.json"
    config = RunConfiguration(settings_source)
    trade_backend = Lemon(config.LM_data_key, config.LM_trading_key, config.LM_trading_type)

    portfolio = Portfolio(
        positions = trade_backend.get_positions(),
        trades = trade_backend.get_trades(),
        trading_backend=trade_backend
    )

    # run strategy
    strategy = PCA_Strategy(
        ratio=0.12,
        company_pool="S&P500",
        portfolio_type="tail",
        factor_estimate_cov=True
    )

    # translate to trade instructions
    pf_dict, pf_value = portfolio.get_portfolio()
    trade_handler = TradeHandler()
    trade_handler.create_rebalance_frame(
        portfolio_dict=pf_dict,
        portfolio_value=pf_value,
        w_new=strategy.weights,
        add_value=0
    )
    trade_handler.create_trade_instructions()

    # place orders
    trade_backend.place_multi_order(trade_handler.trade_instructions, pf_dict)




if __name__ == "__main__":
    main()