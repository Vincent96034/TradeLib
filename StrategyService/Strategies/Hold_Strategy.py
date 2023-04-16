from StrategyService.StrategyClass import Strategy
from TradeHandlerService.TradeData import Portfolio


class Hold_Strategy(Strategy):
    ''' Just hold all funds and do nothing; used as a fallback '''

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__()
        self.strategy_name = "Buy-And-Hold"
        self.portfolio = portfolio

    def strategy_run(self) -> dict:
        ''' Run buy-and-hold strategy. '''
        w = self.portfolio.get_portfolio()
        self.weights = w[0]
        return w
