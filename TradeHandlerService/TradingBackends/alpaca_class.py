from datetime import datetime, timezone
import time
from typing import Union

from alpaca.trading.models import Order as AlpacaOrder
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import (MarketOrderRequest,
                                     LimitOrderRequest,
                                     StopLimitOrderRequest,
                                     TrailingStopOrderRequest)

from TradeHandlerService.data_model import Trade, Position, Asset, Order
from TradeHandlerService.TradingBackends.trade_backend import TradeBackend
from Logger.config_logger import setup_logger

logger = setup_logger(__name__)


class Alpaca(TradeBackend):
    """TradeBackend implementation for Alpaca Trading API."""

    def __init__(self, alpaca_secret: str, alpaca_key: str, alpaca_paper: str):
        self.alpaca_secret = alpaca_secret
        self.alpaca_key = alpaca_key
        self.alpaca_paper = alpaca_paper
        self.trading_client = TradingClient(
            api_key=self.alpaca_key,
            secret_key=self.alpaca_secret,
            paper=alpaca_paper)
        self.order_type_factory = {
            "market_order": self._market_order,
            "limit_order": self._limit_order,
            "stop_order": self._stop_order,
            "trailing_stop_order": self._trailing_stop_order}

    def check_market_status(self):
        """Checks market availability and waits till markets are open."""
        status = self.trading_client.get_clock()
        now = datetime.now(timezone.utc)
        # if market closes in less than 5 minutes or is closed already, wait
        # till market opens again
        if ((status.next_close - now).total_seconds() < (5*60)) or (not status.is_open):
            wait = (status.next_open - datetime.now(timezone.utc)).total_seconds()
            logger.info("Market is closed or closing soon, waiting %s hours"
                        " till next open period.", round(wait/(60*60), 2))
            time.sleep(wait)

    def get_account(self):
        """Method returns AlpacaAccount object."""
        return self.trading_client.get_account()

    def get_assets(self, active: bool = True):
        """Returns a list of AlpacaAsset objects. This list can include
        non-tradeable assets.

        Args:
            active (bool, optional): Whether to return only the list of active
                assets. Defaults to True.
        """
        if active:
            asset_status = AssetStatus.ACTIVE
        else:
            asset_status = None
        search_params = GetAssetsRequest(status=asset_status)
        return self.trading_client.get_all_assets(search_params)

    def get_positions(self, **kwargs):
        """Returns a list of all positions.

        Returns:
            list: A list of custom positions objects.
        """
        positions = []
        response = self.trading_client.get_all_positions()
        for pos in response:
            positions.append(
                Position(
                    asset_id=str(pos.asset_id),
                    side=pos.side.value,
                    quantity=float(pos.qty),
                    qty_available=float(pos.qty_available),
                    buy_price_avg=float(pos.avg_entry_price),
                    current_price=float(pos.current_price),
                    market_value=float(pos.market_value),
                    symbol=str(pos.symbol),
                )
            )
        return positions

    def get_specific_position(self, asset_or_symbol_id):
        """Returns the current position for a specific asset/symbol.

        Args:
            asset_or_symbol_id: Symbol or asset id to retrieve the position for.
        """
        pos = self.trading_client.get_open_position(asset_or_symbol_id)
        return Position(
            asset_id=str(pos.asset_id),
            side=pos.side.value,
            quantity=float(pos.qty),
            qty_available=float(pos.qty_available),
            buy_price_avg=float(pos.avg_entry_price),
            current_price=float(pos.current_price),
            market_value=float(pos.market_value),
            symbol=str(pos.symbol),
        )

    def get_specific_order(self, order_id):
        """Retrieves a specific order by its ID.

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            Order: A TradeLib Order object representing the specific order.
        """
        alpaca_order = self.trading_client.get_order_by_id(order_id=order_id)
        return self._create_order_obj(alpaca_order)

    def get_orders(self, order_status: str = "closed", **kwargs) -> list:
        """Returns a list of all trades filtered by status.

        Args:
            order_status (str, optional): The status of the orders to retrieve.
                Valid values are 'closed', 'open' or 'all'. Defaults to
                'closed'.

        Returns:
            list: A list of Trade objects representing the trades.
        """
        if order_status == "closed":
            status = QueryOrderStatus.CLOSED
        elif order_status == "open":
            status = QueryOrderStatus.OPEN
        else:
            status = QueryOrderStatus.ALL
        filter_request = GetOrdersRequest(status=status)
        return self.trading_client.get_orders(filter_request)

    def place_order(self,
                    symbol: str,
                    side: str,
                    quantity: Union[int, float],
                    quantity_type: str,
                    order_type: str = "market_order",
                    **kwargs,
                    ) -> dict:
        """Function to place an order for a given symbol.

        Args:
            symbol (str): Symbol of the asset to be traded.
            side (str): Side of the trade, either 'buy' or 'sell'.
            quantity (Union[int, float]): Quantity of the asset to be traded.
            quantity_type (str): Type of the quantity value, either 'amount' or
                'value'.
            order_type (str, optional): Type of order, defaults to
                'market_order'.
            **kwargs: Additional arguments to customize the order.

        Returns:
            dict: A dictionary with the order_id and the order_obj as Trade
                object.
        """
        if not isinstance(symbol, str):
            raise TypeError("'isin' must be an string.")
        if not side in ["buy", "sell"]:
            raise ValueError("'side' must be either 'buy' or 'sell'.")
        if not isinstance(quantity, (float, int)):
            raise TypeError("'quantity' must be an float or integer.")
        if quantity_type == "amount":
            qty = quantity
            notional = None
        elif quantity_type == "value":
            qty = None
            notional = quantity
        else:
            raise ValueError("`quantity_type` must be 'amount' or 'value'.")
        ord_type_set = ("market_order", "limit_order",
                        "stop_order", "trailing_stop_order")
        if order_type not in ord_type_set:
            raise ValueError(f"`order_type` must be in {ord_type_set}")
        if side == "sell":  # check if portfolio holds enough of stock
            amount_available = self.get_specific_position(symbol)
            match quantity_type:
                case "amount":
                    if qty > float(amount_available.qty_available):
                        logger.warning(
                            "Order quant %s not available in PF.", qty)
                        qty = float(amount_available.qty_available)
                case "value":
                    if notional > float(amount_available.market_value):
                        logger.warning(
                            "Order value %s not available in PF.", notional)
                        notional = float(amount_available.market_value)
        if qty and (qty <= 0):
            logger.warning("Order quant is less than or equal to zero."
                           "Order will be dismissed %s.", symbol)
            return {"order_id": None, "order_obj": None}

        order_data = self.order_type_factory.get(order_type)
        order_data = order_data(
            symbol=symbol,
            side=side,
            qty=qty,
            notional=notional,
            time_in_force=kwargs.get("time_in_force") or TimeInForce.DAY,
            extended_hours=kwargs.get("extended_hours"),
            client_order_id=kwargs.get("client_order_id"),
            order_class=kwargs.get("order_class"),
            take_profit=kwargs.get("take_profit"),
            stop_loss=kwargs.get("stop_loss"),
            limit_price=kwargs.get("limit_price"),
            stop_price=kwargs.get("stop_price"),
            trail_price=kwargs.get("trail_price"),
            trail_percent=kwargs.get("trail_percent")
        )
        self.check_market_status()
        response = self.trading_client.submit_order(order_data=order_data)
        return {
            "order_id": str(response.id),
            "order_obj": Trade(
                trade_id=str(response.id),
                asset_id=str(response.asset_id),
                created_at=response.created_at,
                quantity=None,
                quantity_type=None,
                price=None,
                side=response.side.value,
                expires_at=None,
                symbol_title=None,
                symbol=response.symbol,
                status=response.status.value,
                order_type=order_type,
                limit_price=response.limit_price,
                stop_price=response.stop_price,
                trail_percent=response.trail_percent,
                trail_price=response.trail_price)
        }

    def place_multi_order(self, order_list: list) -> dict:
        """Function to place multiple orders for different symbols.

        Args:
            order_list (list): A list of orders, where each order is a
                dictionary containing the following keys: 'symbol', 'side',
                'quantity', and 'quantity_type'. Additional keys can be added
                to customize the order.

        Returns:
            dict: A dictionary containing the response of each order.
        """
        order_responses = []
        for order in order_list:
            for key in ["symbol", "side", "quantity", "quantity_type"]:
                if key not in order:
                    raise ValueError(f"Required key '{key}' is missing.")

            order_response = self.place_order(
                symbol=order.get("symbol"),
                side=order.get("side"),
                quantity=order.get("quantity"),
                quantity_type=order.get("quantity_type"),
                take_profit=order.get("take_profit"),
                stop_loss=order.get("stop_loss"),
                limit_price=order.get("limit_price"),
                stop_price=order.get("stop_price"),
                trail_price=order.get("trail_price"),
                trail_percent=order.get("trail_percent")
            )
            order_responses.append(order_response)
        logger.info(
            "Created %s orders.", len([x for x in order_responses if x is not None]))
        return order_responses

    def _market_order(self, **kwargs):
        """Create market order object."""
        return MarketOrderRequest(
            symbol=kwargs.get("symbol"),
            qty=kwargs.get("qty"),
            notional=kwargs.get("notional"),
            side=self._get_side(kwargs.get("side")),
            time_in_force=TimeInForce.DAY,
            extended_hours=None,
            client_order_id=None,
            order_class=None,
            take_profit=None,
            stop_loss=None
        )

    def _limit_order(self, **kwargs):
        """Create limit order object."""
        return LimitOrderRequest(
            symbol=kwargs.get("symbol"),
            qty=kwargs.get("qty"),
            notional=kwargs.get("notional"),
            side=self._get_side(kwargs.get("side")),
            time_in_force=TimeInForce.DAY,
            extended_hours=None,
            client_order_id=None,
            order_class=None,
            take_profit=None,
            stop_loss=None,
            limit_price=kwargs.get("limit_price")
        )

    def _stop_order(self, **kwargs):
        """Create stop order object."""
        return StopLimitOrderRequest(
            symbol=kwargs.get("symbol"),
            qty=kwargs.get("qty"),
            notional=kwargs.get("notional"),
            side=self._get_side(kwargs.get("side")),
            time_in_force=TimeInForce.DAY,
            extended_hours=None,
            client_order_id=None,
            order_class=None,
            take_profit=None,
            stop_loss=None,
            stop_price=kwargs.get("stop_price"),
            limit_price=kwargs.get("limit_price")
        )

    def _trailing_stop_order(self, **kwargs):
        """Create trailing stop order object."""
        return TrailingStopOrderRequest(
            symbol=kwargs.get("symbol"),
            qty=kwargs.get("qty"),
            notional=kwargs.get("notional"),
            side=self._get_side(kwargs.get("side")),
            time_in_force=TimeInForce.DAY,
            extended_hours=None,
            client_order_id=None,
            order_class=None,
            take_profit=None,
            stop_loss=None,
            trail_price=kwargs.get("trail_price"),
            trail_percent=kwargs.get("trail_percent")
        )

    @staticmethod
    def _get_side(side: str):
        """Get side object from string."""
        if side == "buy":
            return OrderSide.BUY
        if side == "sell":
            return OrderSide.SELL
        raise ValueError(f"`side` must be 'buy' or 'sell', not {side}")

    @staticmethod
    def _create_order_obj(order: AlpacaOrder):
        """Returns TradeLib Order object from Alpaca Order object."""
        return Order(
            order_id=str(order.id),
            asset=Asset(
                asset_id=str(order.asset_id),
                symbol=order.symbol,
                symbol_title=None,
                asset_class=order.asset_class.value),
            created_at=order.created_at,
            quantity=float(order.filled_qty),
            quantity_type="amount" if order.notional is None else "value",
            side=order.side.value,
            expires_at=order.expired_at,
            status=order.status.value,
            order_type=order.order_type.value,
            stop_price=order.stop_price,
            limit_price=None,
            trail_percent=order.trail_percent,
            trail_price=order.trail_price,
        )
