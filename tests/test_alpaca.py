import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    AssetClass as AlpacaAssetClass,
    OrderSide as AlpacaOrderSide,
    OrderStatus as AlpacaOrderStatus,
    OrderType as AlpacaOrderType,
)
from alpaca.trading.models import Asset as AlpacaAsset
from alpaca.trading.models import Position as AlpacaPosition
from alpaca.trading.models import Order as AlpacaOrder

from tradelib.model.enums import OrderSide, QuantityMode
from tradelib.model import Asset, Order, Position
from tradelib.trading.clients.alpaca import Alpaca


@pytest.fixture
def mock_trading_client():
    return Mock(spec=TradingClient)


@pytest.fixture
def mock_alpaca_asset():
    mock = Mock(
        spec=AlpacaAsset,
        symbol="AAPL",
        id="123",
        asset_class=AlpacaAssetClass.US_EQUITY,
    )
    mock.name = "Apple Inc"
    return mock


@pytest.fixture
def mock_alpaca_position():
    return Mock(
        spec=AlpacaPosition,
        symbol="AAPL",
        asset_id="123",
        asset_class=AlpacaAssetClass.US_EQUITY,
        qty="100",
        avg_entry_price="150.00",
        exchange="NASDAQ",
        asset_marginable=True,
    )


@pytest.fixture
def mock_alpaca_order():
    order = Mock(
        spec=AlpacaOrder,
        symbol="AAPL",
        asset_id="123",
        asset_class=AlpacaAssetClass.US_EQUITY,
        qty="100",
        notional=None,
        side=AlpacaOrderSide.BUY,
        id="order123",
        status=AlpacaOrderStatus.FILLED,
        order_type=AlpacaOrderType.MARKET,
        created_at=datetime.now(timezone.utc),
        stop_price=1.0,
        limit_price=1.0,
        trail_price=1.0,
        trail_percent=0.1,
        filled_avg_price="150.00",
        filled_qty="100",
        filled_at=datetime.now(timezone.utc),
    )
    return order


@pytest.fixture
def alpaca_client(mock_trading_client):
    with patch(
        "tradelib.trading.clients.alpaca.TradingClient",
        return_value=mock_trading_client,
    ):
        return Alpaca(
            alpaca_key="test", alpaca_secret="test", market_close_handle="wait"
        )


@pytest.fixture
def mock_market_status():
    # Create a mock for the status returned by `get_clock`
    mock_status = Mock()
    mock_status.next_close = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_status.next_open = datetime.now(timezone.utc) + timedelta(hours=2)
    return mock_status


def test_init():
    """Test Alpaca client initialization."""
    with patch("tradelib.trading.clients.alpaca.TradingClient") as _:
        alpaca = Alpaca(alpaca_secret="test", alpaca_key="test", alpaca_paper=True)
        assert alpaca.paper is True
        assert alpaca.order_fee == 1.0
        assert alpaca.market_close_handle == "wait"
        assert alpaca.market_close_offset == 2


def test_check_market_status(alpaca_client, mock_trading_client):
    """Test market status check functionality."""
    mock_clock = Mock(
        is_open=True,
        next_close=datetime.now(timezone.utc) + timedelta(milliseconds=1),
        next_open=datetime.now(timezone.utc) + timedelta(milliseconds=2),
    )
    mock_trading_client.get_clock.return_value = mock_clock

    alpaca_client.check_market_status()
    assert mock_trading_client.get_clock.called


def test_get_tradeable_assets(alpaca_client, mock_trading_client, mock_alpaca_asset):
    """Test retrieving tradeable assets."""
    mock_trading_client.get_all_assets.return_value = [mock_alpaca_asset]

    assets = alpaca_client.get_tradeable_assets()
    assert len(assets) == 1
    assert isinstance(assets[0], Asset)
    assert assets[0].symbol == "AAPL"


def test_get_positions(alpaca_client, mock_trading_client, mock_alpaca_position):
    """Test retrieving positions."""
    mock_trading_client.get_all_positions.return_value = [mock_alpaca_position]

    positions = alpaca_client.get_positions()
    assert len(positions) == 1
    assert isinstance(positions[0], Position)
    assert positions[0].asset.symbol == "AAPL"
    assert positions[0].quantity == 100.0


def test_place_order(
    alpaca_client, mock_trading_client, mock_alpaca_order, mock_market_status
):
    """Test placing orders."""
    # Mock the `get_clock` call to return the mock status
    mock_trading_client.get_clock.return_value = mock_market_status
    mock_trading_client.submit_order.return_value = mock_alpaca_order

    order = Order(
        asset=Asset(symbol="AAPL", asset_type="Equity"),
        quantity=100,
        order_side=OrderSide.BUY,
    )

    result = alpaca_client.place_order(order)

    assert isinstance(result, Order)
    assert result.asset.symbol == "AAPL"
    assert mock_trading_client.submit_order.called


def test_cancel_order(alpaca_client, mock_trading_client):
    """Test canceling orders."""
    alpaca_client.cancel_order("order123")
    mock_trading_client.cancel_order_by_id.assert_called_with("order123")


def test_get_trades(alpaca_client, mock_trading_client, mock_alpaca_order):
    """Test retrieving trades."""
    mock_alpaca_order.metadata = {
        "filled_avg_price": "150.00",
        "filled_qty": "100",
        "filled_at": datetime.now(timezone.utc),
    }
    mock_trading_client.get_orders.return_value = [mock_alpaca_order]
    trades = alpaca_client.get_trades()
    assert len(trades) == 1
    assert trades[0].execution_price == 150.0
    assert trades[0].execution_quantity == 100.0


def test_order_quantity_translator():
    """Test order quantity translation helper."""
    shares, notional = Alpaca._order_quantity_translator(100, QuantityMode.SHARES)
    assert shares == 100
    assert notional is None

    shares, notional = Alpaca._order_quantity_translator(1000, QuantityMode.NOTIONAL)
    assert shares is None
    assert notional == 1000

    with pytest.raises(ValueError):
        Alpaca._order_quantity_translator(100, "invalid")


def test_create_asset(mock_alpaca_asset):
    """Test asset creation from Alpaca asset."""
    asset = Alpaca._create_asset(mock_alpaca_asset)
    assert isinstance(asset, Asset)
    assert asset.symbol == "AAPL"
    assert asset.id == "123"
    assert asset.name == "Apple Inc"


def test_create_position_obj(mock_alpaca_position):
    """Test position creation from Alpaca position."""
    position = Alpaca._create_position_obj(mock_alpaca_position)
    assert isinstance(position, Position)
    assert position.asset.symbol == "AAPL"
    assert position.quantity == 100.0
    assert position.average_price == 150.0


def test_create_order_obj(mock_alpaca_order):
    """Test order creation from Alpaca order."""
    order = Alpaca._create_order_obj(mock_alpaca_order)
    assert isinstance(order, Order)
    assert order.asset.symbol == "AAPL"
    assert order.quantity == 100.0
    assert order.order_side == OrderSide.BUY
