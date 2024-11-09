from typing import List, Dict, Any, Union, Optional
from datetime import datetime
import yfinance as yf

from tradelib.trading.clients.base import TradeBackend
from tradelib.model import Position, Order, Trade
from tradelib.model.enums import OrderType, OrderSide
from tradelib.utils import setup_logger

logger = setup_logger(__name__)


class SandboxBackend(TradeBackend):
    def __init__(self, initial_cash: float = 100000.0, transaction_fee: float = 0.0):
        self.cash = initial_cash
        self.transaction_fee = transaction_fee
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.trades: Dict[str, Trade] = {}
        self.next_order_id = 1
        self.next_trade_id = 1

    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        return {
            "cash": self.cash,
            "positions": self.get_positions(),
            "orders": self.get_orders(),
            "trades": self.get_trades(),
        }

    def get_positions(self) -> List[Position]:
        """Get all positions of trading account."""
        return list(self.positions.values())

    def get_orders(self) -> List[Order]:
        """Get all orders of trading account."""
        return list(self.orders.values())

    def get_trades(self) -> List[Trade]:
        """Get all trades of trading account."""
        return list(self.trades.values())

    def get_cash(self) -> float:
        """Get cash balance of trading account."""
        return self.cash

    def place_order(self, order: Union[Order, Dict[str, Any]]) -> Order:
        """Place an order."""
        if isinstance(order, dict):
            order = Order(**order)
        order_id = f"ORD-{self.next_order_id}"
        self.next_order_id += 1
        order.order_id = order_id
        self.orders[order_id] = order
        # Simulate order execution
        self._execute_order(order)
        return order

    def cancel_order(self, order_id: str) -> List[Order]:
        """Cancel one or multiple orders."""
        order = self.orders.get(order_id)
        if order and order.status == "OPEN":
            order.status = "CANCELED"
        return order

    def place_bulk_orders(
        self, order_list: List[Union[Order, Dict[str, Any]]]
    ) -> List[Order]:
        """Place multiple orders."""
        return [self.place_order(order) for order in order_list]

    def cancel_bulk_orders(self, order_ids: List[str]) -> List[Order]:
        """Cancel multiple orders."""
        return [self.cancel_order(order_id) for order_id in order_ids]

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get status of an order."""
        return self.orders.get(order_id)

    def _execute_order(self, order: Order):
        """Simulate order execution."""
        # Fetch current price
        current_price = self._get_current_price(order.asset.symbol)
        if current_price is None:
            logger.info(f"Price for {order.asset.symbol} not available.")
            return

        executed = False

        if order.order_type == OrderType.MARKET:
            executed = True
            execution_price = current_price
        elif order.order_type == OrderType.LIMIT:
            if (
                order.order_side == OrderSide.BUY and current_price <= order.limit_price
            ) or (
                order.order_side == OrderSide.SELL
                and current_price >= order.limit_price
            ):
                executed = True
                execution_price = order.limit_price
        elif order.order_type == OrderType.STOP:
            if (
                order.order_side == OrderSide.BUY and current_price >= order.stop_price
            ) or (
                order.order_side == OrderSide.SELL and current_price <= order.stop_price
            ):
                executed = True
                execution_price = current_price
        elif order.order_type == OrderType.STOP_LIMIT:
            # Stop price triggers the limit order
            if (
                order.order_side == OrderSide.BUY and current_price >= order.stop_price
            ) or (
                order.order_side == OrderSide.SELL and current_price <= order.stop_price
            ):
                # Now check if limit price condition is met
                if (
                    order.order_side == OrderSide.BUY
                    and current_price <= order.limit_price
                ) or (
                    order.order_side == OrderSide.SELL
                    and current_price >= order.limit_price
                ):
                    executed = True
                    execution_price = order.limit_price

        if executed:
            trade_id = f"TRD-{self.next_trade_id}"
            self.next_trade_id += 1
            fees = self._calculate_fees(order.quantity, execution_price)
            trade = Trade(
                order=order,
                execution_price=execution_price,
                execution_quantity=order.quantity,
                execution_time=datetime.utcnow(),
                fees=fees,
                id=trade_id,
            )
            self.trades[trade_id] = trade
            order.status = "FILLED"
            self._update_position(trade)
            self._update_cash(trade)
            logger.info(f"Order {order.order_id} executed at price {execution_price}")
        else:
            logger.info(f"Order {order.order_id} is pending.")

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Fetch current market price for the asset."""
        try:
            data = yf.Ticker(symbol)
            price = data.history(period="1d", interval="1m").Close[-1]
            return price
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    def _update_position(self, trade: Trade):
        """Update positions based on executed trade."""
        symbol = trade.order.asset.symbol
        position = self.positions.get(symbol)
        quantity = (
            trade.execution_quantity
            if trade.order.order_side == OrderSide.BUY
            else -trade.execution_quantity
        )

        if position:
            total_quantity = position.quantity + quantity
            if total_quantity == 0:
                # Remove position if quantity is zero
                del self.positions[symbol]
            else:
                # Update average price
                total_cost = (
                    position.average_price * position.quantity
                    + trade.execution_price * quantity
                )
                position.quantity = total_quantity
                position.average_price = total_cost / position.quantity
        else:
            # Create new position
            self.positions[symbol] = Position(
                asset=trade.order.asset,
                quantity=quantity,
                average_price=trade.execution_price,
            )

    def _update_cash(self, trade: Trade):
        """Update cash balance after trade execution."""
        total_cost = trade.execution_price * trade.execution_quantity + trade.fees
        if trade.order.order_side == OrderSide.BUY:
            self.cash -= total_cost
        else:
            self.cash += total_cost

    def _calculate_fees(self, quantity: float, price: float) -> float:
        """Calculate transaction fees."""
        return self.transaction_fee
