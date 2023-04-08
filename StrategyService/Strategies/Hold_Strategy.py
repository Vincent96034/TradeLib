from StrategyService.StrategyClass import Strategy


class Hold_Strategy:
    ''' Just hold all funds and do nothing; used as a fallback '''

    def __init__(self, StrategyCls: Strategy):
        self.weights = {}
        self.StrategyCls = StrategyCls

    def strategy_run(self) -> dict:
        ''' Generic function for every strategy class: runs strategy '''
        w = self.StrategyCls.portfolio.get_portfolio()
        self.weights = w[0]
        return w
