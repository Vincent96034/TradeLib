from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class QuantityMode(Enum):
    SHARES = "shares"  # Number of shares of the asset
    NOTIONAL = "notional"  # Total investment amount in currency


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OptionType(Enum):
    CALL = "call"
    PUT = "put"
