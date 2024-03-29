from typing import Union, List
from abc import ABC, abstractmethod

from pandas.errors import AbstractMethodError

from TradeHandlerService.data_model import Position, Order, Asset, Trade


class TradeBackend(ABC):
    """Base class for trading backends. Includes all necessary methods."""

    @abstractmethod
    def get_positions(self, **kwargs) -> List[Position]:
        """Get all positions of trading account."""
        raise NotImplementedError("`get_positions` is not implemented.")

    @abstractmethod
    def get_orders(self, **kwargs) -> List[Order]:
        """Get all trades of trading account."""
        raise NotImplementedError("`get_trades` is not implemented.")

    @abstractmethod
    def place_order(self,
                    symbol: str,
                    side: str,
                    quantity: Union[int, float],
                    quantity_type: str,
                    order_type: str = "market_order",
                    **kwargs) -> Order:
        """Place an order."""
        raise NotImplementedError("`place_order` is not implemented.")

    @abstractmethod
    def place_multi_order(self, order_list) -> List[Order]:
        """Place multiple orders."""
        raise NotImplementedError("`place_multi_order` is not implemented.")

    @staticmethod
    @abstractmethod
    def _create_position_obj(position) -> Position:
        """Returns an Order object."""
        raise NotImplementedError("`_create_position_obj` is not implemented.")

    @staticmethod
    @abstractmethod
    def _create_order_obj(order) -> Order:
        """Returns an Order object."""
        raise NotImplementedError("`_create_order_obj` is not implemented.")

    @staticmethod
    @abstractmethod
    def _create_trade_obj(trade) -> Trade:
        """Returns an Trade object."""
        raise NotImplementedError("`_create_trade_obj` is not implemented.")

    @staticmethod
    @abstractmethod
    def _create_asset_obj(asset) -> Asset:
        """Returns an Order object."""
        raise NotImplementedError("`_create_asset_obj` is not implemented.")
