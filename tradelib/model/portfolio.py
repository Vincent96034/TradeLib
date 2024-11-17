from datetime import datetime
from typing import List, Dict, Optional

from tradelib.utils import logger
from tradelib.model import (
    OrderSide,
    Trade,
    Position,
    CashFlow,
    QuantityMode,
)


class Portfolio:
    def __init__(
        self,
        initial_cash: float = 0.0,
        events: Optional[List[Trade | CashFlow]] = None,
    ):
        """Initialize a Portfolio object.

        :param initial_cash: The starting cash balance of the portfolio.
        :param events: An optional list of events (trades and cash flows) to initialize the portfolio state.
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.history: List[Dict[str, any]] = []

        if events:
            # Sort events by timestamp to ensure correct state of the portfolio
            events = sorted(events, key=lambda event: event.timestamp)
            for event in events:
                if isinstance(event, Trade):
                    self.add_trade(event)
                elif isinstance(event, CashFlow):
                    self.add_cash_flow(event)

        for _, position in self.positions.items():
            if position.quantity < 0:
                logger.warning(f"Found position with negative quantity: {position}.")

    def add_cash_flow(self, cash_flow: CashFlow):
        """Add a cash flow to the portfolio and update cash.

        :param cash_flow: The CashFlow object to be added.
        """
        self.cash += cash_flow.amount
        self._record_portfolio_state(cash_flow.timestamp)

    def add_trade(self, trade: Trade):
        """Add a trade to the portfolio and update positions and cash.

        :param trade: The Trade object to be added.
        """
        symbol = trade.order.asset.symbol

        # Calculate the cost of the trade
        if trade.quantity_mode == QuantityMode.SHARES:
            trade_cost = trade.execution_price * trade.execution_quantity
        else:  # NOTIONAL
            trade_cost = trade.execution_quantity

        # Update cash based on the trade
        if trade.order.order_side == OrderSide.BUY:
            self.cash -= trade_cost + trade.fees
        else:  # SELL
            self.cash += trade_cost - trade.fees

        # Update or create the position based on the trade
        if symbol not in self.positions:
            self.positions[symbol] = Position(asset=trade.order.asset)

        self.positions[symbol].update(trade)
        self.trades.append(trade)

        # Remove the position if it becomes zero after updating
        if abs(self.positions[symbol].quantity) < 0.00001:
            del self.positions[symbol]

        # Record the state of the portfolio after this trade
        self._record_portfolio_state(trade.timestamp)

    def _record_portfolio_state(self, timestamp: datetime):
        """Record the current state of the portfolio at a given timestamp.

        :param timestamp: The datetime at which the state is recorded.
        """
        state = {
            "timestamp": timestamp,
            "cash": self.cash,
            "positions": {
                symbol: (pos.quantity, pos.average_price)
                for symbol, pos in self.positions.items()
            },
        }
        self.history.append(state)

    def get_positions(self) -> Dict[str, Position]:
        """Get the current positions in the portfolio.

        :return: A dictionary of current positions.
        """
        return self.positions

    def get_portfolio_history(self) -> List[Dict[str, any]]:
        """Get the historical states of the portfolio.

        :return: A list of dictionaries representing the portfolio's state over time.
        """
        return self.history

    def total_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate the total value of the portfolio, including cash and positions.

        :param current_prices: A dictionary of current market prices for each asset.
        :return: The total value of the portfolio.
        """
        total_value = self.cash
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, 0.0)
            total_value += position.quantity * current_price
        return total_value

    def __repr__(self):
        positions_summary = ", ".join(
            [
                f"{symbol}: {pos.quantity} units at {pos.average_price:.2f}"
                for symbol, pos in self.positions.items()
            ]
        )
        return f"Portfolio(cash: {self.cash:.2f}, positions: [{positions_summary}])"
