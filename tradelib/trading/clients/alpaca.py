import time
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce, AssetClass
from alpaca.trading.models import (
    Order as AlpacaOrder,
    Position as AlpacaPosition,
    Asset as AlpacaAsset,
)
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    TrailingStopOrderRequest,
)

from tradelib.model.enums import OrderStatus, QuantityMode
from tradelib.model import Position, Asset, Order, Trade, Equity, Crypto, Option
from tradelib.trading.clients.base import TradeBackend
from tradelib.utils import setup_logger, find_in_env

logger = setup_logger(__name__)


ASSET_CLASS_STR_MAP = {
    "us_equity": "Equity",
    "crypto": "Crypto",
    "us_option": "Option",
}

ASSET_CLASS_OBJ_MAP = {
    "Equity": Equity,
    "us_equity": Equity,
    "Crypto": Crypto,
    "crypto": Crypto,
    "Option": Option,
    "us_option": Option,
}

ORDER_STATUS_MAP = {
    "new": OrderStatus.PENDING,
    "partially_filled": OrderStatus.PENDING,
    "filled": OrderStatus.FILLED,
    "done_for_day": OrderStatus.FILLED,
    "canceled": OrderStatus.CANCELED,
    "expired": OrderStatus.EXPIRED,
    "replaced": OrderStatus.PENDING,
    "pending_cancel": OrderStatus.PENDING,
    "pending_replace": OrderStatus.PENDING,
    "pending_review": OrderStatus.PENDING,
    "accepted": OrderStatus.FILLED,
    "pending_new": OrderStatus.PENDING,
    "accepted_for_bidding": OrderStatus.PENDING,
    "stopped": OrderStatus.PENDING,
    "rejected": OrderStatus.REJECTED,
    "suspended": OrderStatus.PENDING,
    "calculated": OrderStatus.PENDING,
    "held": OrderStatus.PENDING,
}

ORDER_TYPE_MAP = {
    "market": MarketOrderRequest,
    "limit": LimitOrderRequest,
    "stop": StopOrderRequest,
    "stop_limit": StopLimitOrderRequest,
    "trailing_stop": TrailingStopOrderRequest,
}


class Alpaca(TradeBackend):
    """TradeBackend implementation for Alpaca Trading API."""

    def __init__(
        self,
        alpaca_secret: Optional[str] = None,
        alpaca_key: Optional[str] = None,
        alpaca_paper: bool = True,
        market_close_handle="wait",
        market_close_offset=2,
    ):
        """Initializes the Alpaca Trading API client."""
        if not alpaca_secret:
            alpaca_secret = find_in_env("alpaca_secret")
        if not alpaca_key:
            alpaca_key = find_in_env("alpaca_key")
        self.trading_client = TradingClient(
            api_key=alpaca_key, secret_key=alpaca_secret, paper=alpaca_paper
        )
        self.market_close_handle = market_close_handle
        self.market_close_offset = market_close_offset
        self.paper = alpaca_paper
        self.order_fee = 1.0  # Alpaca charges $1 per order (non-paper)

    def check_market_status(self) -> None:
        """Checks market availability and waits till markets are open."""
        status = self.trading_client.get_clock()
        now = datetime.now(timezone.utc)
        next_close_seconds = (status.next_close - now).total_seconds()
        next_open_seconds = (status.next_open - now).total_seconds()
        next_open_stdout = round(next_open_seconds / (60 * 60), 2)

        if status.is_open and next_close_seconds > self.market_close_offset * 60:
            logger.debug("Market is open.")
            return
        if self.market_close_handle == "wait":
            logger.info(f"Market is closed, waiting {next_open_stdout}h till next open")
            time.sleep(next_open_seconds)
        elif self.market_close_handle == "raise":
            raise ValueError(
                f"Market is closed, cannot place order till in {next_open_stdout}h. "
            )
        elif self.market_close_handle == "ignore":
            logger.debug(f"Market is closed for {next_open_stdout}h, ignoring...")
            pass

    def get_account(self) -> dict:
        """Method returns AlpacaAccount object."""
        return self.trading_client.get_account()

    def get_cash(self) -> float:
        return float(self.get_account().cash)

    def get_tradeable_assets(self) -> List[Asset]:
        """Returns a list of all tradeable assets."""
        assets = self.trading_client.get_all_assets(
            GetAssetsRequest(status=AssetStatus.ACTIVE)
        )
        return [self._create_asset(asset) for asset in assets]

    def get_positions(self, **kwargs) -> List[Position]:
        """Returns a list of all positions.

        Returns:
            list: A list of custom positions objects.
        """
        response = self.trading_client.get_all_positions(**kwargs)
        return [self._create_position_obj(alpaca_pos) for alpaca_pos in response]

    def get_position(self, asset_or_symbol_id: str) -> Position:
        """Returns the current position for a specific asset/symbol.

        Args:
            asset_or_symbol_id: Symbol or asset id to retrieve the position for .
        """
        alpaca_position = self.trading_client.get_open_position(asset_or_symbol_id)
        return self._create_position_obj(alpaca_position)

    def get_order(self, order_id: str) -> Order:
        """Retrieves a specific order by its ID.

        Args:
            order_id(str): The ID of the order to retrieve.

        Returns:
            Order: A TradeLib Order object representing the specific order.
        """
        alpaca_order = self.trading_client.get_order_by_id(order_id=order_id)
        return self._create_order_obj(alpaca_order)

    def get_orders(
        self, order_status: Optional[str] = None, limit: int = 500, **kwargs
    ) -> List[Order]:
        """Returns a list of all trades filtered by status.

        Args:
            order_status(str, optional): The status of the orders to retrieve.
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
        filter_request = GetOrdersRequest(status=status, limit=limit, **kwargs)
        response = self.trading_client.get_orders(filter_request)
        return [self._create_order_obj(alpaca_order) for alpaca_order in response]

    def place_order(self, order: Order | dict, **kwargs) -> Order:
        if isinstance(order, dict):
            order = Order(**order)
        shares, notional = self._order_quantity_translator(
            order.quantity, order.quantity_mode
        )
        if self._check_sell_all_order(order):
            self.check_market_status()
            response = self.trading_client.close_position(
                symbol_or_asset_id=order.symbol
            )
        else:
            args = {**order.metadata, **kwargs}
            data = {
                "symbol": order.asset.symbol,
                "qty": shares,
                "notional": notional,
                "side": order.order_side.value,
                "type": order.order_type.value,
                "time_in_force": TimeInForce.DAY,
                "extended_hours": args.get("extended_hours"),
                "client_order_id": args.get("client_order_id"),
                "order_class": args.get("order_class"),
                "take_profit": args.get("take_profit"),
                "stop_loss": args.get("stop_loss"),
                "stop_price": order.stop_price,
                "position_intent": args.get("position_intent"),
                "limit_price": order.limit_price,
                "trail_price": order.trailing_price,
                "trail_percent": order.trailing_percent,
            }
            logger.debug(f"Order data: {data}")
            AlpacaOrderRequest = ORDER_TYPE_MAP[order.order_type.value]
            order_data = AlpacaOrderRequest(**data)
            logger.debug(f"Order data (Alpaca): {order_data}")
            self.check_market_status()
            response = self.trading_client.submit_order(order_data=order_data)
        logger.info(f"Created {order.order_side}-order for {order.asset.symbol}")
        return self._create_order_obj(response)

    def place_bulk_orders(self, orders: List[Order | dict], **kwargs) -> List[Order]:
        """Place multiple orders at once.

        Args:
            orders(list): A list of orders to place. Each order can be either
                a dictionary or an Order object.

        Returns:
            list: A list of Order objects representing the placed orders.
        """
        order_responses = [self.place_order(order, **kwargs) for order in orders]
        logger.info("Created %s orders.", len([order_responses]))
        return order_responses

    def cancel_order(self, order_id: str):
        return self.trading_client.cancel_order_by_id(order_id)

    def cancel_bulk_orders(self, order_ids: List[str]):
        return [self.cancel_order(order_id) for order_id in order_ids]

    def get_order_status(self, order_id: str):
        order = self.get_order(order_id)
        return order.status

    def get_trades(self):
        closed_orders = [
            order
            for order in self.get_orders(order_status="closed")
            if order.status.value != "canceled"
        ]
        logger.info(f"Found {len(closed_orders)} trades.")
        return [
            Trade(
                order=order,
                execution_price=float(order.metadata.get("filled_avg_price")),
                execution_quantity=float(order.metadata.get("filled_qty")),
                quantity_mode=QuantityMode.SHARES,
                id=order.id,
                execution_time=order.metadata.get("filled_at"),
                fees=0.0 if self.paper else self.order_fee,
                metadata=order.metadata,
            )
            for order in closed_orders
        ]

    @staticmethod
    def _order_quantity_translator(
        quantity: int | float, quantity_mode: QuantityMode
    ) -> Tuple[float, float]:
        """Translates the quantity and quantity_mode to `shares` and `notional`.

        Returns:
            Tuple[shares, notional]: A tuple containing the quantity and notional.
        """
        if quantity_mode == QuantityMode.SHARES:
            return quantity, None
        elif quantity_mode == QuantityMode.NOTIONAL:
            return None, quantity
        raise ValueError(
            f"Invalid quantity_mode '{quantity_mode}', must be 'shares' or 'notional'."
        )

    def _check_sell_all_order(self, order: Order) -> bool:
        """Check if the order is a sell-all order (close entire position)."""
        if order.order_side != OrderSide.SELL:
            return False
        pos = self.get_specific_position(order.symbol)
        available = pos.qty_available or pos.market_value
        if order.quantity >= float(available):
            logger.info(
                f"Sell-Order quantity ({order.quantity_mode}) of {order.quantity} not "
                f"available quantity of {available}"
            )
            return True

    @staticmethod
    def _create_asset(asset: AlpacaAsset) -> Asset:
        """Returns TradeLib Asset object from Alpaca Asset object."""
        asset_kwargs = {
            "symbol": asset.symbol,
            "id": str(asset.id),
            "name": asset.name,
            "metadata": asset.__dict__,
        }
        if asset.asset_class == AssetClass.US_OPTION:
            asset_kwargs.update(
                {
                    "underlying": Equity(
                        name=asset.underlying_symbol,
                        symbol=asset.underlying_symbol,
                        id=asset.underlying_asset_id,
                    ),
                    "option_type": asset.type,
                    "strike_price": asset.strike_price,
                    "expiry_date": asset.expiration_date,
                }
            )
        return ASSET_CLASS_OBJ_MAP[asset.asset_class.value](**asset_kwargs)

    @staticmethod
    def _create_position_obj(position: AlpacaPosition):
        """Returns TradeLib Order object from Alpaca Order object."""
        return Position(
            asset=Asset(
                symbol=position.symbol,
                id=str(position.asset_id),
                asset_type=ASSET_CLASS_STR_MAP[position.asset_class.value],
                metadata={
                    "exchange": position.exchange,
                    "asset_class": position.asset_class,
                    "asset_marginable": position.asset_marginable,
                },
            ),
            quantity=float(position.qty),
            average_price=float(position.avg_entry_price),
            metadata=position.__dict__,
        )

    @staticmethod
    def _create_order_obj(order: AlpacaOrder):
        """Returns TradeLib Order object from Alpaca Order object."""
        return Order(
            asset=Asset(
                symbol=order.symbol,
                id=str(order.asset_id),
                asset_type=ASSET_CLASS_STR_MAP[order.asset_class.value],
                metadata={
                    "asset_class": order.asset_class,
                },
            ),
            quantity=float(order.qty or 0.0) if order.qty else float(order.notional),
            quantity_mode=QuantityMode.NOTIONAL
            if order.notional
            else QuantityMode.SHARES,
            order_side=order.side.value,
            id=str(order.id),
            status=ORDER_STATUS_MAP[order.status.value],
            order_type=order.order_type.value,
            stop_price=order.stop_price,
            limit_price=order.limit_price,
            trailing_price=order.trail_price,
            trailing_percent=order.trail_percent,
            timestamp=order.created_at,
            metadata=order.__dict__,
        )
