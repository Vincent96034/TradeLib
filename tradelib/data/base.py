from abc import ABC, abstractmethod
import pandas as pd
from enum import Enum
from typing import Any, Dict, Optional

from tradelib.utils.config_logger import setup_logger

logger = setup_logger(__name__)


class DataType(Enum):
    HISTORICAL = "historical"
    LIVE = "live"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    FACTOR = "factor"


class DataService(ABC):
    data_type: DataType

    @abstractmethod
    def get(self, *args, **kwargs) -> Any:
        """
        Abstract method to retrieve data. Specific subclasses will implement this method.
        """
        pass


class PriceDataService(DataService, ABC):
    data_type: DataType = DataType.HISTORICAL

    @abstractmethod
    def get(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Retrieve historical price data for a given symbol within a date range.
        :param symbol: Asset symbol for which data is requested.
        :param start_date: Start date for the historical data.
        :param end_date: End date for the historical data.
        :return: A DataFrame containing historical price data.
        """
        pass


class LivePriceDataService(DataService, ABC):
    data_type: DataType = DataType.LIVE

    @abstractmethod
    def get(self, symbol: str, **kwargs) -> float:
        """
        Retrieve the current live price for a given asset symbol.
        :param symbol: Asset symbol for which live price is requested.
        :return: The current price of the asset.
        """
        pass


class FundamentalsDataService(DataService, ABC):
    data_type: DataType = DataType.FUNDAMENTALS

    @abstractmethod
    def get(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """
        Retrieve fundamental data for a given asset symbol.
        :param symbol: Asset symbol for which fundamental data is requested.
        :return: A dictionary containing fundamental data.
        """
        pass


class NewsDataService(DataService, ABC):
    data_type: DataType = DataType.NEWS

    @abstractmethod
    def get(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Retrieve news articles or headlines related to a given asset symbol.
        :param symbol: Asset symbol for which news data is requested.
        :param start_date: Start date for filtering news data.
        :param end_date: End date for filtering news data.
        :return: A DataFrame containing news data.
        """
        pass


class FactorDataService(DataService, ABC):
    data_type: DataType = DataType.FACTOR

    @abstractmethod
    def get(
        self,
        factors: Optional[list] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Retrieve factor data, such as Fama-French factors.
        :param factors: List of factor names to retrieve.
        :param start_date: Start date for filtering factor data.
        :param end_date: End date for filtering factor data.
        :return: A DataFrame containing factor data.
        """
        pass


class FinancialDataService(DataService, ABC):
    """Base class for data services used for financial data requests."""

    @abstractmethod
    def ticker_data_historic(self, *args, **kwargs):
        """Get historical ticker data."""
        raise NotImplementedError("Method hasn't been implemented yet.")

    @staticmethod
    def get_constituents(exchange: str):
        """Get the list of constituents for a given exchange.

        Args:
        exchange (str): The name of the exchange for which the constituents are
            requested. Only "S&P500" and "NASDAQ100" are supported.

        Returns:
        list: A list of stock symbols that represent the constituents of the
            specified exchange.
        """
        if not isinstance(exchange, str):
            raise TypeError("`exchange` must be of type str.")
        if exchange == "S&P500":
            constituents = pd.read_html(
                "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            )[0]["Symbol"]
        elif exchange == "NASDAQ100":
            constituents = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4][
                "Ticker"
            ]
        else:
            raise NotImplementedError(f"Exchange {exchange} is not implemented.")
        return list(constituents)
