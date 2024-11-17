from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from tradelib.data.base import DataService
from tradelib.model import (
    Portfolio,
    OrderSide,
    Order,
    OrderType,
    QuantityMode,
    Trade,
    Asset,
)
from tradelib.utils import setup_logger

logger = setup_logger(__name__)


class Strategy(ABC):
    def __init__(
        self,
        portfolio: Portfolio,
        data_source: Optional[DataService] = None,
        **parameters,
    ):
        """Initialize a strategy with a given portfolio and optional parameters.

        :param portfolio: A Portfolio object to manage positions and cash.
        :param parameters: A dictionary of strategy-specific parameters.
        """
        self.portfolio = portfolio
        self.data_source = data_source
        self.parameters = parameters
        self.trade_log: List[Dict[str, Any]] = []

    @abstractmethod
    def generate_signals(self, market_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate buy/sell/hold signals based on the provided market data.

        :param market_data: A dictionary of market data keyed by asset symbol.
        :return: A dictionary of signals keyed by asset symbol, with values like 'BUY', 'SELL', or 'HOLD'.
        """
        pass

    def execute_trade(self, symbol: str, action: str, quantity: float, price: float):
        """
        Execute a trade based on the action ('BUY' or 'SELL') and update the portfolio.

        :param symbol: The symbol of the asset to trade.
        :param action: 'BUY' or 'SELL'.
        :param quantity: Number of shares or units to trade.
        :param price: Execution price.
        """
        if action not in {"BUY", "SELL"}:
            raise ValueError("Action must be 'BUY' or 'SELL'")

        order_side = OrderSide.BUY if action == "BUY" else OrderSide.SELL
        order = Order(
            asset=Asset(symbol=symbol),
            quantity=quantity,
            order_side=order_side,
            order_type=OrderType.MARKET,
            quantity_mode=QuantityMode.UNITS,
        )
        trade = Trade(
            order=order,
            execution_price=price,
            execution_quantity=quantity,
            timestamp=datetime.now(),
        )

        # Update portfolio and log the trade
        self.portfolio.add_trade(trade)
        self.trade_log.append(
            {
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": price,
                "timestamp": datetime.now(),
            }
        )

    def backtest(self, historical_data: Dict[str, List[Dict[str, Any]]]):
        """
        Run a backtest by generating signals and executing trades on historical data.

        :param historical_data: A dictionary where each key is an asset symbol and
                                each value is a list of price data dictionaries.
        """
        for date, data_point in historical_data.items():
            signals = self.generate_signals(data_point)
            for symbol, signal in signals.items():
                if signal != "HOLD":
                    price = data_point[symbol]["close"]
                    quantity = self.calculate_position_size(price, symbol, signal)
                    self.execute_trade(symbol, signal, quantity, price)
            # Optionally, record the portfolio state at each step

    def calculate_position_size(self, price: float, symbol: str, action: str) -> float:
        """
        Calculate the position size based on risk management rules.

        :param price: The current price of the asset.
        :param symbol: The symbol of the asset.
        :param action: The trade action ('BUY' or 'SELL').
        :return: The quantity of shares or units to trade.
        """
        max_allocation = self.parameters.get("max_allocation", 0.1)  # 10% of portfolio
        position_value = self.portfolio.total_value({symbol: price}) * max_allocation
        return position_value / price

    def log_trade(self, symbol: str, action: str, quantity: float, price: float):
        """
        Log a trade for performance analysis.

        :param symbol: The symbol of the asset.
        :param action: The trade action ('BUY' or 'SELL').
        :param quantity: The quantity traded.
        :param price: The execution price.
        """
        self.trade_log.append(
            {
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": price,
                "timestamp": datetime.now(),
            }
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(parameters={self.parameters})"
