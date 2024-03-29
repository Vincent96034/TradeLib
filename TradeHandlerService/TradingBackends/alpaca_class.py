from datetime import datetime, timezone
import time
from typing import Union

from alpaca.trading.models import (
    Order as AlpacaOrder,
    Position as AlpacaPosition)
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import (MarketOrderRequest,
                                     LimitOrderRequest,
                                     StopLimitOrderRequest,
                                     TrailingStopOrderRequest)

from TradeHandlerService.data_model import Position, Asset, Order
from TradeHandlerService.TradingBackends.trade_backend import TradeBackend
from Logger.config_logger import setup_logger

logger = setup_logger(__name__)


class Alpaca(TradeBackend):
    """TradeBackend implementation for Alpaca Trading API."""

    def __init__(self, alpaca_secret: str, alpaca_key: str, alpaca_paper: bool):
        self.alpaca_secret = alpaca_secret
        self.alpaca_key = alpaca_key
        self.alpaca_paper = alpaca_paper
        self.trading_client = TradingClient(
            api_key=self.alpaca_key,
            secret_key=self.alpaca_secret,
            paper=alpaca_paper)

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
        response = self.trading_client.get_all_positions()
        return [self._create_position_obj(alpaca_pos) for alpaca_pos in response]

    def get_specific_position(self, asset_or_symbol_id):
        """Returns the current position for a specific asset/symbol.

        Args:
            asset_or_symbol_id: Symbol or asset id to retrieve the position for.
        """
        alpaca_position = self.trading_client.get_open_position(
            asset_or_symbol_id)
        return self._create_position_obj(alpaca_position)

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
        response = self.trading_client.get_orders(filter_request)
        return [self._create_order_obj(alpaca_order) for alpaca_order in response]

    @staticmethod
    def check_place_order_args(kwargs):
        """Decorator for the place_order function to check input args."""
        if not isinstance(kwargs.get("symbol"), str):
            raise TypeError("'isin' must be an string.")
        if kwargs.get("side") not in ["buy", "sell"]:
            raise ValueError("'side' must be either 'buy' or 'sell'.")
        if not isinstance(kwargs.get("quantity"), (float, int)):
            raise TypeError("'quantity' must be an float or integer.")
        if kwargs.get("quantity_type") not in ["amount", "value"]:
            raise ValueError("`quantity_type` must be 'amount' or 'value'")
        ord_type_set = ("market_order", "limit_order",
                        "stop_order", "trailing_stop_order")
        if order_type := kwargs.get("order_type") not in ord_type_set:
            raise ValueError(f"`{order_type}` must be in {ord_type_set}")
        # def wrapper(self, *args, **kwargs):
        #    return func(self, *args, **kwargs)
        # return wrapper

    # @check_place_order_args
    def place_order(self,
                    symbol: str,
                    side: str,
                    quantity: Union[int, float],
                    quantity_type: str,
                    order_type: str = "market_order",
                    **kwargs,
                    ) -> dict:
        # todo: force keyword args
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
        # get function arguments to check for validity
        function_args = locals()
        kwargs_data = function_args.pop('kwargs')
        function_args.update(kwargs_data)
        self.check_place_order_args(kwargs=function_args)

        close_all = False
        qty, notional = self._order_quantity_translator(
            quantity_type=quantity_type, quantity=quantity)
        if side == "sell":  # check if portfolio holds enough of stock
            close_all = self._check_sell_order(
                quantity_type=quantity_type, qty=qty, notional=notional, symbol=symbol)
        else:
            close_all = False
        self.check_market_status()
        if close_all:
            response = self.trading_client.close_position(
                symbol_or_asset_id=symbol)
        else:
            OrderReq = self._order_type_factory(order_type)
            order_data = OrderReq(
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
            response = self.trading_client.submit_order(order_data=order_data)
        logger.info(f"Created {side}-order for {symbol}")
        return self._create_order_obj(response)

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
                order_type=order.get("order_type", "market_order"),
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

    def liquidate_minimum_positions(self):
        """Liquidates all Positions that dont fulfill the minimum pricing
        criteria, e.g. do not have a notional value above 1$."""
        pass  # todo

    @staticmethod
    def _order_quantity_translator(quantity_type, quantity):
        """Mapps TradeLib quantity logic to Alpaca's quantiy logic.

        Alpaca uses qty for amount of stocks and notional for fractional shares
        of a stock. Before this function is called, the 'quantity_type' arg must
        be checked for correct values.

        Args:
            quantiy_type (str): One of 'amount' or 'value'.
            quantity (float): Quantity of the request.

        Returns: 
            Tuple(qty, notional): Quantity for amount or value. One of
            (qty, notional) is always 'None'.
        """
        if quantity_type == "amount":
            qty = round(quantity, 2)
            notional = None
        else:  # quantity_type == "value":
            qty = None
            notional = round(quantity, 2)
        return qty, notional

    def _check_sell_order(self, quantity_type, qty, notional, symbol):
        close_all = False
        amount_available = self.get_specific_position(symbol)
        match quantity_type:
            case "amount":
                if qty >= float(amount_available.qty_available):
                    logger.warning(
                        "Order quant %s not available in PF.", qty)
                    # qty = float(amount_available.qty_available)
                    close_all = True
            case "value":
                if notional >= float(amount_available.market_value):
                    logger.warning(
                        "Order value %s not available in PF.", notional)
                    # notional = float(amount_available.market_value)
                    close_all = True
        return close_all

    def _order_type_factory(self, order_type):
        order_req_dict = {
            "market_order": self._market_order,
            "limit_order": self._limit_order,
            "stop_order": self._stop_order,
            "trailing_stop_order": self._trailing_stop_order
        }
        return order_req_dict.get(order_type, self._market_order)

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
    def _create_position_obj(position: AlpacaPosition):
        """Returns TradeLib Order object from Alpaca Order object."""
        asset_id = str(position.asset_id)
        return Position(
            position_id=asset_id,
            asset=Asset(
                asset_id=asset_id,
                symbol=position.symbol,
                symbol_title=None,
                asset_class=position.asset_class.value
            ),
            current_price=float(position.current_price),
            market_value=float(position.market_value)
        )

    @staticmethod
    def _create_order_obj(order: AlpacaOrder):
        """Returns TradeLib Order object from Alpaca Order object."""
        asset_id = str(order.asset_id)
        return Order(
            order_id=str(order.id),
            asset=Asset(
                asset_id=str(asset_id),
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

    @staticmethod
    def _create_trade_obj(_):
        """Unused"""

    @staticmethod
    def _create_asset_obj(_):
        """Unused"""
