from __future__ import annotations
from typing import List, Optional, Union

from dataclasses import dataclass, asdict
import datetime as dt
import pandas as pd
from typing_extensions import Literal


@dataclass
class Position:
    """Class representing a stock position."""
    asset_id: str
    side: str
    quantity: float
    qty_available: float
    buy_price_avg: float
    current_price: float
    market_value: float
    symbol: Optional[str]

    def get_rel_performance(self):
        """Returns the relative performance of the position."""
        return (self.current_price / self.buy_price_avg) - 1

    def get_abs_performance(self):
        """Returns the absolute performance of the position."""
        return self.market_value - (self.buy_price_avg * self.quantity)

@dataclass
class Order:
    """Class representing a order. This is just a base class, every order
    should also be a trade. A trade can also be an unsuccessful order."""

@dataclass
class Trade:
    """Class representing a trade or order."""
    trade_id: str
    asset_id: str  # e.g. isin
    created_at: dt.Datetime
    quantity: Optional[Union[int, float]]
    quantity_type: Optional[str]
    price: Optional[float]
    side: Optional[str]
    expires_at: Optional[dt.Datetime]
    symbol_title: Optional[str]
    symbol: Optional[str]
    status: Optional[str]
    order_type: Optional[str]
    limit_price: Optional[str]
    stop_price: Optional[str]
    trail_percent: Optional[float]
    trail_price: Optional[float]

    def get_total_price(self) -> float:
        """Get total price of the trade."""
        return self.quantity * self.price

    def __repr__(self) -> str:
        attrs = {
            "asset_id": self.asset_id,
            "created_at": self.created_at,
            "quantity": self.quantity,
            "quantity_type": self.quantity_type,
            "price": self.price,
            "side": self.side,
            "expires_at": self.expires_at,
            "symbol_title": self.symbol_title,
            "symbol": self.symbol,
            "status": self.status,
            "order_type": self.order_type,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "trail_percent": self.trail_percent,
            "trail_price": self.trail_price,
        }
        parts = [f"<Trade {self.trade_id}"]
        for attr, value in attrs.items():
            if value is not None:
                parts.append(f"{attr}: {value}")
        return "\n   ".join(parts) + "\n>"


class Portfolio:
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
