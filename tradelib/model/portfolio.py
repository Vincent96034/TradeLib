from typing import List, Literal
import pandas as pd


class Portfolio:
    """Class to hold the data for trading operations."""

    def __init__(self, trading_backend) -> None:
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.trading_backend: Literal["TradeBackend"] = trading_backend
        self.total_value: float = 0.0
        self.initialize()

    def get_portfolio_weights(self) -> dict:
        """Retrieves the user's portfolio as a pd.Dataframe."""
        df = pd.DataFrame.from_records([p.to_dict() for p in self.positions])
        pf_value = df["market_value"].sum()
        df["w"] = df["market_value"] / pf_value
        return df.set_index(["asset_id"]).to_dict(orient="index")

    def get_total_value(self) -> float:
        """Get toatal value of the portfolio"""
        self.total_value = sum(position.market_value for position in self.positions)
        return self.total_value

    def initialize(self):
        """Update portfolio data"""
        self.positions = self.trading_backend.get_positions()
        self.trades = self.trading_backend.get_orders()  # TODO: naming: trades/orders
        self.total_value = self.get_total_value()

    def __repr__(self) -> str:
        return (
            f"Portfolio({len(self.positions)} positions, {len(self.trades)} trades, "
            f"total_value={self.total_value}, backend={self.trading_backend.__class__.__name__})"
        )


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
