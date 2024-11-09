from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, field

from .asset import Asset
from .enums import OrderSide, OrderStatus, OrderType, QuantityMode


@dataclass
class Order:
    asset: Asset
    quantity: float
    order_side: OrderSide
    quantity_mode: QuantityMode = QuantityMode.NOTIONAL
    id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    order_type: OrderType = OrderType.MARKET
    stop_price: Optional[float] = None
    limit_price: Optional[float] = None
    trailing_price: Optional[float] = None
    trailing_percent: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate the order and raise exceptions if invalid."""
        if self.quantity < 0:
            raise ValueError("Order quantity must be positive")
        if self.limit_price is not None and self.limit_price < 0:
            raise ValueError("Limit price must be positive")
        if self.stop_price is not None and self.stop_price < 0:
            raise ValueError("Stop price must be positive")
        if self.order_type in {OrderType.LIMIT} and self.limit_price is None:
            raise ValueError("Limit order requires a limit price")
        if self.order_type in {OrderType.STOP} and self.stop_price is None:
            raise ValueError("Stop order requires a stop price")
        if self.order_type is OrderType.STOP_LIMIT and (
            self.stop_price is None or self.limit_price is None
        ):
            raise ValueError("Stop-limit order requires both stop and limit prices")

    def __post_init__(self):
        self.validate()
        self.order_side = OrderSide(self.order_side)
        self.quantity_mode = QuantityMode(self.quantity_mode)
        self.status = OrderStatus(self.status)
        self.order_type = OrderType(self.order_type)

    def __repr__(self):
        return f"Order({self.order_type.value}-{self.order_side.value} {self.asset.symbol}: {self.quantity} ({self.quantity_mode.value}) [{self.status.value}])"


@dataclass
class Trade:
    order: Order
    execution_price: float
    execution_quantity: float
    quantity_mode: QuantityMode = QuantityMode.NOTIONAL
    id: Optional[str] = None
    execution_time: datetime = field(default_factory=datetime.now)
    fees: float = 0.0
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def cost(self) -> float:
        return self.execution_price * self.execution_quantity + self.fees

    def validate(self) -> None:
        if self.execution_quantity < 0:
            raise ValueError("Trade quantity must be positive")
        if self.execution_price < 0:
            raise ValueError("Trade price must be positive")
        if self.fees < 0:
            raise ValueError("Trade fees must be non-negative")

    def __post_init__(self):
        self.validate()

    def __repr__(self):
        return f"Trade({self.order} @ {self.execution_price} (qty: {self.execution_quantity}) [{self.execution_time}])"


@dataclass
class Position:
    asset: Asset
    quantity: float = 0.0
    average_price: float = 0.0
    metadata: Dict[str, any] = field(default_factory=dict)

    def update(self, trade: Trade):
        if not isinstance(trade, Trade):
            raise ValueError("Position update must be a Trade object")
        if trade.order.order_side == OrderSide.BUY:
            total_cost = self.average_price * self.quantity
            trade_cost = trade.execution_price * trade.execution_quantity
            self.quantity += trade.execution_quantity
            self.average_price = (total_cost + trade_cost) / self.quantity
        else:  # SELL
            self.quantity -= trade.execution_quantity
            if self.quantity == 0:
                self.average_price = 0.0
        # Average price remains unchanged on sell

    def __repr__(self):
        return f"Position({self.asset.symbol}, {self.quantity}, {self.average_price})"
