from typing import List, Dict, Any
from abc import ABC, abstractmethod

from tradelib.model import Position, Order, Trade, Asset


class TradeBackend(ABC):
    """Base class for trading backends. Includes all necessary methods."""

    @abstractmethod
    def get_account(self, **kwargs) -> Dict[str, Any]:
        """Get account information."""
        raise NotImplementedError("`get_account` is not implemented.")

    @abstractmethod
    def get_cash(self, **kwargs) -> float:
        """Get cash balance of trading account."""
        raise NotImplementedError("`get_cash` is not implemented.")

    @abstractmethod
    def get_positions(self, **kwargs) -> List[Position]:
        """Get all positions of trading account."""
        raise NotImplementedError("`get_positions` is not implemented.")

    @abstractmethod
    def get_orders(self, **kwargs) -> List[Order]:
        """Get all trades of trading account."""
        raise NotImplementedError("`get_trades` is not implemented.")

    @abstractmethod
    def get_trades(self, **kwargs) -> List[Trade]:
        """Get all trades of trading account."""
        raise NotImplementedError("`get_trades` is not implemented.")

    @abstractmethod
    def place_order(self, order: Order | Dict[str, Any], **kwargs) -> Order:
        """Place an order."""
        raise NotImplementedError("`place_order` is not implemented.")

    @abstractmethod
    def cancel_order(self, order_id: str, **kwargs) -> Order:
        """Cancel an order."""
        raise NotImplementedError("`cancel_order` is not implemented.")

    @abstractmethod
    def place_bulk_orders(self, orders: List[Order | Dict[str, Any]]) -> List[Order]:
        """Place multiple orders."""
        raise NotImplementedError("`place_multi_order` is not implemented.")

    @abstractmethod
    def cancel_bulk_orders(self, order_ids: List[str]) -> List[Order]:
        """Cancel multiple orders."""
        raise NotImplementedError("`cancel_multi_order` is not implemented.")

    @abstractmethod
    def get_order_status(self, order_id: str, **kwargs) -> Order:
        """Get status of an order."""
        raise NotImplementedError("`get_order_status` is not implemented.")

    @abstractmethod
    def get_tradeable_assets(self, **kwargs) -> List[Asset]:
        """Get all tradeable assets."""
        raise NotImplementedError("`tradeable_assets` is not implemented.")
