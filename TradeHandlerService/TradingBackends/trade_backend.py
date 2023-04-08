import datetime as dt
from typing import Optional, Union
from TradeHandlerService.TradeData import Position, Trade


class TradeBackend:
    def get_positions(self):
        raise NotImplementedError("`get_positions` is not implemented.")
    
    def get_trades(self):
        raise NotImplementedError("`get_trades` is not implemented.")

    def place_order(self):
        raise NotImplementedError("`place_order` is not implemented.")
    
    def place_multi_order(self):
        raise NotImplementedError("`place_multi_order` is not implemented.")
    
    @staticmethod
    def _create_position_object(
        isin: str,
        quantity: int,
        buy_price_avg: float,
        estimated_price: Optional[float] = None,
        isin_title: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Position:
        """ Create a Position object with the given input values.

        Args:
            isin (str): The International Securities Identification Number (ISIN) for the security.
            quantity (int): The number of units of the security.
            buy_price_avg (float): The average price per unit of the security at the time of purchase.
            estimated_price (float): The estimated price per unit of the security at the time of creation.
            isin_title (Optional[str]): The title or name of the security, if available.
            symbol (Optional[str]): The ticker symbol of the security, if available.

        Returns:
            Position: A Position object initialized with the input values.
        """
        if not isin:
            raise ValueError("`isin` cannot be empty.")
        if quantity <= 0:
            raise ValueError("`qantity` must be a positive integer.")
        if buy_price_avg <= 0:
            raise ValueError("`buy_price_avg` must be a positive float.")
        if estimated_price <= 0:
            raise ValueError("`estimated_price` must be a positive float.")
        
        return Position(
            isin=isin,
            quantity=quantity,
            buy_price_avg=buy_price_avg,
            estimated_price=estimated_price,
            isin_title=isin_title,
            symbol=symbol
        )

    @staticmethod
    def _create_trade_object(
        id_: str,
        isin: str,
        created_at: dt.datetime,
        quantity: Union[int, float],
        price: float,
        expires_at: Optional[dt.datetime] = None,
        isin_title: Optional[str] = None,
        symbol: Optional[str] = None,
        status: Optional[str] = None
    ) -> Trade:
        """ Create a Trade object with the given input values.

        Args:
            id (str): The unique identifier for the trade.
            isin (str): The International Securities Identification Number (ISIN) for the security.
            created_at (datetime.datetime): The datetime when the trade was created.
            quantity (Union[int, float]): The number of units of the security to be traded.
            price (float): The price per unit of the security for the trade.
            expires_at (Optional[datetime.datetime]): The datetime when the trade will expire, if any.
            isin_title (Optional[str]): The title or name of the security, if available.
            symbol (Optional[str]): The ticker symbol of the security, if available.
            status (Optional[str]): The status of the trade, if any.

        Returns:
            Trade: A Trade object initialized with the input values.
        """
        if not id_:
            raise TypeError("`id_` of trade cannot be empty.")
        if not isin:
            raise TypeError("`isin` cannot be empty.")
        if not created_at:
            raise TypeError("`created_at` datetime cannot be empty.")
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise TypeError("`quantity` must be a positive integer or float.")
        if price <= 0:
            raise TypeError("`price` must be a positive float.")
        if expires_at and expires_at < created_at:
            raise TypeError("`expires_at` datetime must be after created at datetime.")
        
        return Trade(
            id=id_,
            isin=isin,
            created_at=created_at,
            quantity=quantity,
            price=price,
            expires_at=expires_at,
            isin_title=isin_title,
            symbol=symbol,
            status=status
        )