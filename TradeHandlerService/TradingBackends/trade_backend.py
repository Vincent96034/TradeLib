from typing import Union
from abc import ABC, abstractmethod


class TradeBackend(ABC):
    """Base class for trading backends. Includes all necessary methods."""

    @abstractmethod
    def get_positions(self, **kwargs):
        """Get all positions of trading account."""
        raise NotImplementedError("`get_positions` is not implemented.")

    @abstractmethod
    def get_orders(self, **kwargs):
        """Get all trades of trading account."""
        raise NotImplementedError("`get_trades` is not implemented.")

    @abstractmethod
    def place_order(self,
                    symbol: str,
                    side: str,
                    quantity: Union[int, float],
                    quantity_type: str,
                    order_type: str = "market_order",
                    **kwargs):
        """Place an order."""
        raise NotImplementedError("`place_order` is not implemented.")

    @abstractmethod
    def place_multi_order(self, order_list):
        """Place multiple orders."""
        raise NotImplementedError("`place_multi_order` is not implemented.")

    @staticmethod
    @abstractmethod
    def _create_order_obj(order):
        """Returns an Order object."""
        raise NotImplementedError("`_create_order_obj` is not implemented.")
