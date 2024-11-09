import pytest

from tradelib.model.enums import OrderSide
from tradelib.model import Asset, Order, Position, Trade


@pytest.fixture
def mock_asset():
    return Asset(symbol="AAPL", name="Apple Inc.", asset_type="STOCK")


@pytest.fixture
def basic_order(mock_asset):
    return Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)


@pytest.fixture
def basic_trade(mock_asset):
    order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)
    return Trade(order=order, execution_price=150.0, execution_quantity=100.0)


@pytest.fixture
def basic_position(mock_asset):
    return Position(asset=mock_asset)
