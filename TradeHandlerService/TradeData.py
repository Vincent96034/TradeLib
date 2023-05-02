from __future__ import annotations
from typing import List, Optional, Union

from dataclasses import dataclass
import datetime as dt
import pandas as pd
from typing_extensions import Literal


@dataclass
class Position:
    """Class representing a stock position."""
    asset_id: str
    quantity: int
    buy_price_avg: float
    estimated_price: float
    isin_title: Optional[str]
    symbol: Optional[str]

    def get_estimated_price_total(self) -> float:
        """Get total estimated price of the position."""
        return self.quantity * self.buy_price_avg

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

    def __init__(self) -> None:
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.trading_backend: Literal['TradeBackend'] = None
        self.total_value: float = 0.0

    def get_portfolio(self) -> dict:
        """Retrieves the user's portfolio and its total value.

        Returns:
            Tuple[Dict[str, Dict[str, float]], float]: A tuple containing a
                dictionary with the user's portfolio where each key is an ISIN
                and the value is a dictionary with the keys "quantity",
                "buy_price_avg", "estimated_price_total", "estimated_price",
                and "w", and the total value of the portfolio.
        """
        positions = []
        for pos in self.positions:
            positions.append(
                [pos.isin, pos.quantity, pos.buy_price_avg,
                    pos.get_estimated_price_total(), pos.estimated_price]
            )
        positions = pd.DataFrame(positions, columns=[
                                 "isin", "quantity", "buy_price_avg",
                                 "estimated_price_total", "estimated_price"])
        pf_value = positions["estimated_price_total"].sum()
        positions["w"] = positions["estimated_price_total"] / pf_value
        portfolio = positions.set_index(["isin"]).to_dict(orient="index")
        return portfolio, pf_value

    def update(self):
        """Update portfolio data"""
        self.positions = self.trading_backend.get_positions()
        self.trades = self.trading_backend.get_trades()

    def get_total_value(self) -> float:
        """Get toatal value of the portfolio"""
        self.total_value = sum(
            [position.estimated_price_total for position in self.positions])
        return self.total_value

    def __repr__(self) -> str:
        return f'Portfolio({len(self.positions)} positions, {len(self.trades)} trades, ' \
            f'total_value={self.total_value}, backend={self.trading_backend.__class__.__name__})'
