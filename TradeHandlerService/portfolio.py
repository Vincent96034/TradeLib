"""Module that holds the portfolio class."""
from dataclasses import asdict
from typing import List

import pandas as pd
from typing_extensions import Literal

from Utils.singleton import Singleton
from TradeHandlerService.data_model import Position, Trade

# TODO: fix moving this out of data_models.py


class Portfolio(metaclass=Singleton):
    """Class to hold the data for trading operations."""

    def __init__(self, trading_backend) -> None:
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.trading_backend: Literal['TradeBackend'] = trading_backend
        self.total_value: float = 0.0
        self.update()

    def get_portfolio_weights(self) -> dict:
        """Retrieves the user's portfolio as a pd.Dataframe."""
        positions = []
        for pos in self.positions:
            positions.append(list(asdict(pos).values()))
        positions = pd.DataFrame(positions, columns=["asset_id", "side",
                                                     "quantity", "qty_available", "buy_price_avg",
                                                     "current_price", "market_value", "symbol"])
        pf_value = positions["market_value"].sum()
        positions["w"] = positions["market_value"] / pf_value
        portfolio = positions.set_index(["asset_id"]).to_dict(orient="index")
        return portfolio

    def get_total_value(self) -> float:
        """Get toatal value of the portfolio"""
        self.total_value = sum(
            position.market_value for position in self.positions)
        return self.total_value

    def update(self):
        """Update portfolio data"""
        self.positions = self.trading_backend.get_positions()
        self.trades = self.trading_backend.get_orders()  # TODO: naming: trades/orders
        self.total_value = self.get_total_value()

    def __repr__(self) -> str:
        return f'Portfolio({len(self.positions)} positions, {len(self.trades)} trades, ' \
            f'total_value={self.total_value}, backend={self.trading_backend.__class__.__name__})'


# artefact of data-models
# def get_buy_price_avg(self) -> float:
#     """Returns the average buy price of the position. This is used to
#     calculate the performance of a position."""
#     return np.mean([trade.price for trade in self.trades])

# def get_quantity(self):
#     """Returns the total quantity (number of fractional stocks) of the
#     position."""
#     return sum(trade.order.quantity for trade in self.trades)

# def get_rel_performance(self):
#     """Returns the relative performance of the position."""
#     return (self.current_price / self.get_buy_price_avg) - 1

# def get_abs_performance(self):
#     """Returns the absolute performance of the position."""
#     return self.market_value - (self.get_buy_price_avg * self.get_quantity)
