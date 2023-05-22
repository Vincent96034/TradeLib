"""Module that holds the portfolio class."""
from __future__ import annotations
import pandas as pd
from typing_extensions import Literal

from Utils.singleton import Singleton
from TradeHandlerService.data_objects import Position, Trade

# TODO: fix moving this out of data_objects.py

class Portfolio(metaclass = Singleton):
    """Class to hold the data for trading operations."""

    def __init__(self, trading_backend) -> None:
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.trading_backend: Literal['TradeBackend'] = trading_backend
        self.total_value: float = 0.0
        self.update()

    def get_portfolio_weights(self) -> dict:
        """Retrieves the user's portfolio as a pd.Dataframe.
        """
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
            [position.market_value for position in self.positions])
        return self.total_value

    def update(self):
        """Update portfolio data"""
        self.positions = self.trading_backend.get_positions()
        self.trades = self.trading_backend.get_trades()
        self.total_value = self.get_total_value()

    def __repr__(self) -> str:
        return f'Portfolio({len(self.positions)} positions, {len(self.trades)} trades, ' \
            f'total_value={self.total_value}, backend={self.trading_backend.__class__.__name__})'
