from abc import ABC, abstractmethod
import pandas as pd

from Logger.config_logger import setup_logger

logger = setup_logger(__name__)


class DataService(ABC):
    """Abstract base class for data services."""

    def __init__(self):
        # metadata for DataServices
        self.name = None
        self.homepage = None
        self.data_category = None
        self.data_types = None
        self.min_limit = None
        self.day_limit = None
        self.API_KEY = None

    @classmethod
    def get_methods(cls):
        """Returns a list of all methods of a DataService."""
        methods = [attribute for attribute in dir(cls)
                   if callable(getattr(cls, attribute))
                   and attribute.startswith('__') is False]
        return methods

    @staticmethod
    def check_output_frame(func):
        """Decorator function to check output of methods for na-values.
        """
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if isinstance(res, pd.DataFrame):
                na_columns = res.columns[res.isnull().any()].to_list()
                if na_columns:
                    logger.warning("The output dataframe contains empty values"
                                   " in the columns %s", na_columns)
            return res
        return wrapper

    def __repr__(self):
        return f"<DataService: {self.name} ({self.homepage}) - Category {self.data_category}>"


class FinancialDataService(DataService, ABC):
    """Base class for data services used for financial data requests."""

    @abstractmethod
    def ticker_data_historic(self, *args, **kwargs):
        """Get historical ticker data."""
        raise NotImplementedError("Method hasn't been implemented yet.")
    
    @staticmethod
    def get_constituents(exchange: str):
        """ Get the list of constituents for a given exchange.

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
                'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]["Symbol"]
        elif exchange == "NASDAQ100":
            constituents = pd.read_html(
                'https://en.wikipedia.org/wiki/Nasdaq-100')[4]["Ticker"]
        else:
            raise NotImplementedError(
                f"Exchange {exchange} is not implemented.")
        return list(constituents)
