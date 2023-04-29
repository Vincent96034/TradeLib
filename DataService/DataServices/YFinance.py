from typing import Union
import yfinance as yf
import pandas as pd

from DataService.DataService import FinancialDataService
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class YFinance(FinancialDataService):
    def __init__(self):
        super().__init__()
        self.name = "Yahoo Finance"
        self.homepage = "https://finance.yahoo.com/"
        self.data_category = "Financial"
        self.data_types = ["daily", "fundamental"]
        self.min_limit = 33
        logger.warning("The 'Yahoo! finance API' is intended for personal use "
                       "only. You should refer to Yahoo!'s terms of use for "
                       "details on your rights to use the actual data "
                       "downloaded rights to use the actual data downloaded "
                       " (https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html).")

    def create_tickers(self, ticker_symbols: list, session=None) -> dict:
        """ Creates a dictionary of yf.Ticker objects for the given list of
        ticker symbols.

            Args:
                ticker_symbols (list): A list of ticker symbols as strings.
                    session (requests.Session, optional): A requests.Session
                    object to use for the HTTP requests. Defaults to None.

            Returns:
                dict: A dictionary of Ticker objects, where the keys are the
                    ticker symbols and  the values are Ticker objects.
        """
        if not isinstance(ticker_symbols, list):
            raise TypeError("`ticker_symbols` must be of type list.")
        if non_valid_symbols := [symbol for symbol in ticker_symbols if not isinstance(symbol, str)]:
            raise TypeError("Not all symbols in `ticker_symbols` are of type"
                            " string. The following non valid symbols have been"
                            f" provided: {non_valid_symbols}")
        try:
            return yf.Tickers(ticker_symbols, session).tickers
        except TimeoutError:
            request = {}
            logger.warning("Encountered TimeoutError, retrying now ...")
            for chunk in self.split_lst(ticker_symbols, 3):
                request = {**request, **yf.Tickers(chunk, session).tickers}
            return request

    @FinancialDataService.check_output_frame
    def ticker_data_historic(self,
                             ticker_symbols: list,
                             pct_change: bool = False,
                             **kwargs
                             ) -> pd.DataFrame:
        """ Returns historic data for the given ticker symbols.

            Args:
                ticker_symbols (list): A list of ticker symbols as strings.

            Keyword Args:
                start (str or None): The start date for the data in the format
                    'YYYY-MM-DD'.
                end (str or None): The end date for the data in the format
                    'YYYY-MM-DD'.
                interval (str or None): The frequency of the data, either '1d'
                    (daily) or '1wk' (weekly).
                group_by (str or None): The grouping of the data, either
                    `ticker` or `column`.
                [...]

            Returns:
                pandas.DataFrame: A pandas DataFrame with the historic data for
                the given ticker symbols.
                    The DataFrame has the following columns for each ticker
                        symbol:
                        - `Open`: the opening price for each trading day.
                        - `High`: the highest price reached during each trading
                            day.
                        - `Low`: the lowest price reached during each trading
                            day.
                        - `Close`: the closing price for each trading day.
                        - `Adj Close`: the adjusted closing price for each
                            trading day.
                        - `Volume`: the trading volume for each trading day.

            Example Output:

                            Open           High             
                            AAPL   MSFT    AAPL   MSFT      [...]
                Date ____________________________________________                                                                
                2023-04-10  150.5  62.1    152.0  63.2      
                2023-04-11  151.0  62.5    152.8  63.6      [...]
                2023-04-12  151.3  63.0    153.0  64.0      

        """
        if not isinstance(ticker_symbols, list):
            raise TypeError("`ticker_symbols` must be of type list.")
        if non_valid_symbols := [symbol for symbol in ticker_symbols if not isinstance(symbol, str)]:
            raise TypeError("Not all symbols in `ticker_symbols` are of type"
                            " string. The following non valid symbols have "
                            f" been provided: {non_valid_symbols}")
        if not isinstance(kwargs.get('start'), (str, type(None))):
            raise TypeError(
                "`start` must be of type string in the format YYYY-MM-DD.")
        if not isinstance(kwargs.get('end'), (str, type(None))):
            raise TypeError(
                "`end` must be of type string in the format YYYY-MM-DD.")
        # kwargs specified in yf.download()
        df = yf.download(ticker_symbols, **kwargs)
        if pct_change:
            for col_tuple in df.columns:
                df.loc[:, col_tuple] = df.loc[:, col_tuple].pct_change()
            df = df.iloc[1:]  # remove first row (nan)
        return df

    def symbol_to_isin(self, tickers: dict) -> dict:
        """ Returns a dictionary of ISIN codes for the given ticker symbols.

            Args:
                tickers (dict): A dictionary of ticker symbols and yf.Ticker
                    objects.

            Returns:
                dict: A dictionary of ISIN codes, where the keys are the ticker
                    symbols and the values are the corresponding ISIN codes as
                    strings. If the ISIN code is not available, the
                    corresponding value is an empty string.
        """
        if not isinstance(tickers, dict):
            raise TypeError("`ticker_symbols` must be of type dict.")
        if non_valid := [tickers[ticker] for ticker in tickers if not isinstance(tickers[ticker], yf.Ticker)]:
            raise TypeError("Not all symbols in `tickers` are of type "
                            " yf.Ticker; The following non valid tickers have"
                            f" been provided: {non_valid}")
        return {symb: (tickers[symb].isin if tickers[symb].isin != "-" else "") for symb in tickers}

    @staticmethod
    def split_lst(lst, n):
        """ Splits a list `lst` into `n` roughly equal parts."""
        k, m = divmod(len(lst), n)
        return (lst[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


# TODO: error handling of yf specific errors (there are many)
