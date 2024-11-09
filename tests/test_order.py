import pytest
from datetime import datetime

from tradelib.model.order import (
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Trade,
    Position,
)


############################## Order() ##############################


def test_order_creation_defaults(mock_asset):
    order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)
    assert order.status == OrderStatus.PENDING
    assert order.order_type == OrderType.MARKET
    assert order.stop_price is None
    assert order.limit_price is None


def test_order_creation_custom(mock_asset):
    order = Order(
        asset=mock_asset,
        quantity=100,
        order_side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        limit_price=150.0,
    )
    assert order.order_side == OrderSide.SELL
    assert order.order_type == OrderType.LIMIT
    assert order.limit_price == 150.0


def test_invalid_quantity(mock_asset):
    with pytest.raises(ValueError):
        Order(asset=mock_asset, quantity=-10, order_side=OrderSide.BUY)


def test_invalid_limit_price(mock_asset):
    with pytest.raises(ValueError):
        Order(
            asset=mock_asset,
            quantity=100,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            limit_price=-1,
        )


def test_invalid_stop_price(mock_asset):
    with pytest.raises(ValueError):
        Order(
            asset=mock_asset,
            quantity=100,
            order_side=OrderSide.BUY,
            order_type=OrderType.STOP,
            stop_price=-1,
        )


def test_market_order_validation(basic_order):
    basic_order.validate()  # Should not raise any exception


def test_limit_order_validation(mock_asset):
    # Valid limit order
    order1 = Order(
        asset=mock_asset,
        quantity=100,
        order_side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        limit_price=150.0,
    )
    order1.validate()  # Should not raise any exception

    # Invalid limit order (missing limit price)
    with pytest.raises(ValueError):
        Order(
            asset=mock_asset,
            quantity=100,
            order_side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
        )


def test_stop_order_validation(mock_asset):
    # Valid stop order
    order1 = Order(
        asset=mock_asset,
        quantity=100,
        order_side=OrderSide.BUY,
        order_type=OrderType.STOP,
        stop_price=150.0,
    )
    order1.validate()  # Should not raise any exception

    # Invalid stop order (missing stop price)
    with pytest.raises(ValueError):
        Order(
            asset=mock_asset,
            quantity=100,
            order_side=OrderSide.BUY,
            order_type=OrderType.STOP,
        )


def test_stop_limit_order_validation(mock_asset):
    # Valid stop-limit order
    order1 = Order(
        asset=mock_asset,
        quantity=100,
        order_side=OrderSide.BUY,
        order_type=OrderType.STOP_LIMIT,
        stop_price=150.0,
        limit_price=145.0,
    )
    order1.validate()  # Should not raise any exception

    # Invalid stop-limit order (missing prices)
    with pytest.raises(ValueError):
        Order(
            asset=mock_asset,
            quantity=100,
            order_side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
        )


############################## Trade() ##############################


def test_trade_creation_defaults(basic_trade):
    assert basic_trade.execution_price == 150.0
    assert basic_trade.execution_quantity == 100.0
    assert basic_trade.fees == 0.0
    assert isinstance(basic_trade.execution_time, datetime)
    assert isinstance(basic_trade.metadata, dict)


def test_trade_creation_custom(mock_asset):
    order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)
    trade = Trade(
        order=order,
        execution_price=150.0,
        execution_quantity=50.0,
        fees=2.5,
        metadata={"exchange": "NYSE"},
    )
    assert trade.execution_price == 150.0
    assert trade.execution_quantity == 50.0
    assert trade.fees == 2.5
    assert trade.metadata["exchange"] == "NYSE"


def test_trade_cost_calculation(basic_trade):
    # Test without fees
    expected_cost = 150.0 * 100.0  # price * quantity
    assert basic_trade.cost == expected_cost

    # Test with fees
    basic_trade.fees = 10.0
    expected_cost_with_fees = (150.0 * 100.0) + 10.0
    assert basic_trade.cost == expected_cost_with_fees


def test_trade_validation(mock_asset):
    order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)

    # Test negative execution price
    with pytest.raises(ValueError):
        Trade(order=order, execution_price=-1.0, execution_quantity=100.0)

    # Test negative execution quantity
    with pytest.raises(ValueError):
        Trade(order=order, execution_price=150.0, execution_quantity=-1.0)

    # Test negative fees
    with pytest.raises(ValueError):
        Trade(order=order, execution_price=150.0, execution_quantity=100.0, fees=-1.0)


############################## Position() ##############################


def test_position_creation_defaults(basic_position):
    assert basic_position.quantity == 0.0
    assert basic_position.average_price == 0.0
    assert isinstance(basic_position.metadata, dict)


def test_position_update_buy(mock_asset):
    position = Position(asset=mock_asset)
    order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)
    trade = Trade(order=order, execution_price=150.0, execution_quantity=100.0)

    position.update(trade)
    assert position.quantity == 100.0
    assert position.average_price == 150.0


def test_position_update_multiple_buys(mock_asset):
    position = Position(asset=mock_asset)

    # First buy: 100 shares @ 150
    order1 = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)
    trade1 = Trade(order=order1, execution_price=150.0, execution_quantity=100.0)
    position.update(trade1)

    # Second buy: 50 shares @ 160
    order2 = Order(asset=mock_asset, quantity=50, order_side=OrderSide.BUY)
    trade2 = Trade(order=order2, execution_price=160.0, execution_quantity=50.0)
    position.update(trade2)

    assert position.quantity == 150.0
    assert position.average_price == (100 * 150 + 50 * 160) / 150


def test_position_update_sell(mock_asset):
    # Initialize position with 100 shares @ 150
    position = Position(asset=mock_asset, quantity=100.0, average_price=150.0)

    # Sell 50 shares @ 160
    order = Order(asset=mock_asset, quantity=50, order_side=OrderSide.SELL)
    trade = Trade(order=order, execution_price=160.0, execution_quantity=50.0)

    position.update(trade)
    assert position.quantity == 50.0
    assert position.average_price == 150.0  # Average price remains same for sells


def test_position_close_to_zero(mock_asset):
    position = Position(asset=mock_asset)

    # Buy 100 shares @ 150
    buy_order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.BUY)
    buy_trade = Trade(order=buy_order, execution_price=150.0, execution_quantity=100.0)
    position.update(buy_trade)

    # Sell all 100 shares @ 160
    sell_order = Order(asset=mock_asset, quantity=100, order_side=OrderSide.SELL)
    sell_trade = Trade(
        order=sell_order, execution_price=160.0, execution_quantity=100.0
    )
    position.update(sell_trade)

    assert position.quantity == 0.0
    assert position.average_price == 0.0
