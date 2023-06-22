from dataclasses import dataclass
from typing import List
import datetime as dt

from sqlalchemy import Column, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


@dataclass
class Asset(Base):
    """Class representing an asset."""
    __tablename__ = 'asset'
    # ids & relations
    asset_id: Mapped[str] = mapped_column(primary_key=True)
    positions: Mapped[List["Position"] | None] = relationship(
        "Position", back_populates="asset")
    orders: Mapped[List["Order"] | None] = relationship(
        "Order", back_populates="asset")
    prices: Mapped[List["StockPrice"] | None] = relationship(
        "StockPrice", back_populates="asset")
    # fields
    symbol: Mapped[str | None] = mapped_column(default=None)
    symbol_title: Mapped[str | None] = mapped_column(default=None)
    asset_class: Mapped[str | None] = mapped_column(default=None)


@dataclass
class StockPrice(Base):
    """Class representing a stock price."""
    __tablename__ = 'prices'
    # ids & relations
    stock_time_id: Mapped[str] = mapped_column(primary_key=True)
    asset_id = Column(String, ForeignKey('asset.asset_id'))
    asset: Mapped[Asset] = relationship("Asset", back_populates="prices")
    # fields
    timestamp: Mapped[dt.datetime] = mapped_column()
    adj_close: Mapped[float | None] = mapped_column(default=None)
    open_price: Mapped[float | None] = mapped_column(default=None)
    close_price: Mapped[float | None] = mapped_column(default=None)
    high_price: Mapped[float | None] = mapped_column(default=None)
    low_price: Mapped[float | None] = mapped_column(default=None)
    volume: Mapped[float | None] = mapped_column(default=None)


@dataclass
class Order(Base):
    """Class representing an order."""
    __tablename__ = 'order'
    # ids & relations
    order_id: Mapped[str] = mapped_column(primary_key=True)
    asset_id = Column(String, ForeignKey('asset.asset_id'))
    asset: Mapped[Asset] = relationship("Asset", back_populates="orders")
    # trade_id = Column(String, ForeignKey('trade.trade_id'))
    trade: Mapped["Trade"] = relationship(
        "Trade", back_populates="order")
    # fields
    created_at: Mapped[dt.datetime] = mapped_column()
    quantity: Mapped[float | None] = mapped_column(default=None)
    quantity_type: Mapped[str | None] = mapped_column(default=None)
    side: Mapped[str | None] = mapped_column(default=None)
    expires_at: Mapped[dt.datetime | None] = mapped_column(default=None)
    status: Mapped[str | None] = mapped_column(default=None)
    order_type: Mapped[str | None] = mapped_column(default=None)
    limit_price: Mapped[str | None] = mapped_column(default=None)
    stop_price: Mapped[str | None] = mapped_column(default=None)
    trail_percent: Mapped[float | None] = mapped_column(default=None)
    trail_price: Mapped[float | None] = mapped_column(default=None)


@dataclass
class Trade(Base):
    """Class representing a trade."""
    __tablename__ = 'trade'
    # ids & relations
    trade_id: Mapped[str] = mapped_column(primary_key=True)
    order_id = Column(String, ForeignKey('order.order_id'))
    order: Mapped[Order] = relationship("Order", back_populates="trade")
    position_id = Column(String, ForeignKey('position.position_id'))
    position: Mapped["Position"] = relationship(
        "Position", back_populates="trades")
    # fields
    trade_price: Mapped[float] = mapped_column()
    status: Mapped[str | None] = mapped_column(default=None)
    commment: Mapped[str | None] = mapped_column(default=None)


@dataclass
class Position(Base):
    """Class representing an asset position."""
    __tablename__ = 'position'
    # ids & relations
    position_id: Mapped[str] = mapped_column(primary_key=True)
    asset_id = Column(String, ForeignKey('asset.asset_id'))
    asset: Mapped[Asset] = relationship("Asset", back_populates="positions")
    trades: Mapped[List["Trade"]] = relationship(
        "Trade", back_populates="position")
    # fields
    current_price: Mapped[float | None] = mapped_column(default=None)
    market_value: Mapped[float | None] = mapped_column(default=None)

    def to_dict(self):
        """Creates a dictionary of the Position Object."""
        return {
            "position_id": self.position_id,
            "asset_id": self.asset.asset_id,
            "symbol": self.asset.symbol,
            "symbol_title": self.asset.symbol_title,
            "asset_class": self.asset.asset_class,
            "current_price": self.current_price,
            "market_value": self.market_value
        }


# Create the engine and tables
engine = create_engine("sqlite:///Database/mydb.sqlite")
Base.metadata.create_all(engine)
