import math
import numpy as np
import pandas as pd
from datetime import datetime as dt
from typing import Union
from dateutil.relativedelta import relativedelta
from sklearn.decomposition import PCA

from StrategyService.StrategyClass import Strategy
from DataService.DataServices.YFinance import YFinance
from DataService.DataServices.FamaFrench import FamaFrench
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class PCA_Strategy(Strategy):
    """ Class for implementing a PCA-based trading strategy that selects a subset of companies
        in a given company pool to form a portfolio based on their sensitivity to the first
        principal component of their returns.

        Args:
        ratio (float): The ratio of companies to select for the portfolio based on their sensitivity
            to the first principal component.
        company_pool (Union[str, list]): The pool of companies from which to select a portfolio. Can
            be either 'S&P500', 'NASDAQ100' or a list of company tickers. Default is 'S&P500'.
        portfolio_type (str): The type of portfolio to construct. Can be either 'head', 'tail' or 'hedge'.
            Default is 'tail'.
        factor_estimate_cov (bool): Whether to estimate covariance matrix based on Fama-French factors.
            Default is True.
        data_service: Object for accessing stock data. Default is YFinance.
        famafrench_data: Object for accessing Fama-French data. Default is FamaFrench.

        Attributes:
        name (str): Name of the trading strategy.
        _valid_inputs (dict): Dictionary containing valid inputs for the company_pool and portfolio_type
            arguments.
        ratio (float): The ratio of companies to select for the portfolio based on their sensitivity to
            the first principal component.
        company_pool (Union[str, list]): The pool of companies from which to select a portfolio.
        portfolio_type (str): The type of portfolio to construct.
        factor_estimate_cov (bool): Whether to estimate covariance matrix based on Fama-French factors.
        data_service: Object for accessing stock data.
        famafrench_data: Object for accessing Fama-French data.
        loadings (list): The loadings on the first principal component of the returns data.
        sign_ratio (float): The ratio of companies with negative loadings to those with positive loadings.
        weights (dict): The weights assigned to each company in the portfolio.
        _df_returns (pd.DataFrame): The returns data of the selected companies.
        _df_factors (pd.DataFrame): The Fama-French factors data used to estimate covariance matrix.
        _covM (np.array): The covariance matrix of the returns data.

        Methods:
        _get_returns_data(start_date: str, stop_date: Union[str, None], OHLC_spec: str) -> pd.DataFrame:
            Downloads and returns historical stock returns data of companies in the company_pool.
        _get_factor_data(start_date: str) -> Tuple[pd.DataFrame, str]:
            Downloads and returns Fama-French factors data.
        run_strategy(train_period: int = 24) -> dict:
            Runs the PCA-based trading strategy and returns the weights assigned to each company in the
            portfolio.
        loadings_to_weights(loadings: list, col_names: list, portfolio_type: str, n: int) -> dict:
            Converts the loadings on the first principal component of the returns data to weights assigned
            to each company in the portfolio.
        estimate_cov_with_factors(X: np.array, F: np.array, K: int) -> np.array:
            Estimates the covariance matrix of the returns data using Fama-French factors.
    """
    def __init__(self,
                 ratio: float = 0.1,
                 company_pool: Union[str, list] = "S&P500",
                 portfolio_type: str = "tail",
                 factor_estimate_cov: bool = True,
                 data_service = YFinance(),
                 famafrench_data = FamaFrench()) -> None:
        super().__init__()
        self.name = "PCA-Strategy"
        self._valid_inputs = {
            "company_pool": ["S&P500", "NASDAQ100"],
            "portfolio_type": ["head", "tail", "hedge"]
        }
        self.ratio = ratio
        self.company_pool = company_pool
        self.portfolio_type = portfolio_type
        self.factor_estimate_cov = factor_estimate_cov
        self.data_service = data_service
        self.famafrench_data = famafrench_data
        self.loadings = []
        self.sign_ratio = None
        self.weights = {}
        self._df_returns = None
        self._df_factors = None
        self._covM = None

    def _get_returns_data(self, start_date: str, stop_date: Union[str, None] = None, OHLC_spec: str = "Adj Close"):
        cp = self.company_pool
        if cp == "S&P500":
            companies = self.data_service.get_constituents(cp)
        elif cp == "NASDAQ100":
            companies = self.data_service.get_constituents(cp)
        else:
            companies = self.company_pool
        logger.info("Now downloading returns data.")
        df_returns = self.data_service.ticker_data_historic(companies, start=start_date, end=stop_date, pct_change=True)[OHLC_spec]
        self._df_returns = df_returns
        return df_returns.dropna()

    def _get_factor_data(self, start_date):
        df_factors = self.famafrench_data.famafrench_data_historic(start_date)
        self._df_factors = df_factors
        return df_factors, self.famafrench_data.latest_date

    def run_strategy(self, train_period: int = 24):
        ''' Run PCA-Strategy. '''
        start_date = (dt.today() - relativedelta(months=train_period)).strftime('%Y-%m-%d')
        # first downlaod factor data and check latest available data
        if self.factor_estimate_cov:
            factor_df, latest_avail_factor_data = self._get_factor_data(start_date=start_date)
        else:
            latest_avail_factor_data = None
        returns_df = self._get_returns_data(start_date=start_date, stop_date=latest_avail_factor_data)
        # calculate covariance matrix needed for PCA
        if self.factor_estimate_cov:
            # fit both datasets to same lenght and calculate covariance matrix
            factor_df = factor_df.loc[returns_df.index, :]
            covM = self.estimate_cov_with_factors(
                X=np.array(returns_df),
                F=np.array(factor_df.loc[:, ["Mkt-RF", "SMB", "HML"]]),
                K=3)
        else:
            covM = returns_df.cov()
        self._covM = covM
        # Calculating PC1 loadings: they express the market sensitivity
        pca = PCA(n_components=1)
        pca.fit(covM)
        loadings = pca.components_[0] # retain 1st Principal Component
        n = math.ceil(len(returns_df.columns) * self.ratio) # number of companies in portfolio
        weights = self.loadings_to_weights(loadings=loadings,
                                 col_names=list(returns_df.columns),
                                 portfolio_type=self.portfolio_type,
                                 n=n)
        self.weights = weights
        return weights

    @staticmethod
    def loadings_to_weights(loadings: list, col_names: list, portfolio_type: str, n: int):
        # used to be able to construct a portfolio after components initial sorting is lost
        loadings_dict = {i[0]: i[1] for i in zip(loadings, col_names)}
        # sign ratio: the majority of stocks should move in the same direction
        sign_ratio = (len(loadings) - sum(np.sign(loadings) > 0))/len(loadings)
        if sign_ratio > 0.5:
            hedge_loadings = loadings[np.where(loadings >= 0)]
            loadings = loadings[np.where(loadings < 0)]
        else:
            hedge_loadings = loadings[np.where(loadings < 0)]
            loadings = loadings[np.where(loadings >= 0)]
        if abs(sign_ratio - 0.5) < 0.2:
            logger.warn("No clear majority sign in PC1.")
        loadings_sorted = sorted(loadings, key=abs, reverse=True)
        if portfolio_type == "head":
            pf_loadings = loadings_sorted[0:n]
        elif portfolio_type == "tail":
            pf_loadings = loadings_sorted[-n:len(col_names)+1]
        else:
            pf_loadings = sorted(hedge_loadings, key=abs, reverse=True)
        # weight each company by its loading to PC1
        pf_weights = [abs(i) / sum(list(map(abs, pf_loadings))) for i in pf_loadings]
        pf_constituents = [loadings_dict[i] for i in pf_loadings]
        return {symb: w for symb, w in zip(pf_constituents, pf_weights)}

    @staticmethod
    def estimate_cov_with_factors(X, F, K):
        """ Estimates the covariance matrix based on the Farma & French Factor Model.

        Args:
            X (np.array): Array of N stock returns of shape (T,N)
            F (np.array): Array of K factors of shape (T,K)
            K (int): Number of factors used

        Returns:
            Covariance Matrix of shape (N,N)

        Sources:
            https://palomar.home.ece.ust.hk/MAFS6010R_lectures/Rsession_factor_models.html
            https://docs.mosek.com/portfolio-cookbook/factormodels.html
        """
        N = X.shape[1] # number of stocks
        T = X.shape[0] # Time
        # Fama French data with intercept
        F_ = np.insert(F, 0, np.ones(T), axis=1)   # (T, K+1)
        # Estimated parameters per company
        Gamma = X.T @ F_ @ np.linalg.inv(F_.T @ F_)   # (N, K+1)
        # Estimated Parameters
        # Alpha = Gamma[:,0]    # (N,)
        Betas = Gamma[:,1:]   # (N, K)
        # Residuals
        E = (X.T - Gamma @ F_.T).T
        # Degrees of freedom (4 estimated parameters)
        free = K+1
        # Covariance matrix of Residuals
        Psi = (1/(T-free)) * E.T @ E    # (N,N)
        # Covariance matrix of data
        Sigma = Betas @ np.cov(F.T) @ Betas.T + np.diag(np.diag(Psi))   # (N, N)
        return Sigma

    @property
    def ratio(self):
        return self._ratio
    
    @ratio.setter
    def ratio(self, value):
        if not isinstance(value, (float, int)):
            raise TypeError("`ratio` must be of type float or int")
        if (value <= 0) or (value > 1):
            raise ValueError("`ratio` must be greater than 0 and smaller or equal to 1.")
        self._ratio = value

    @property
    def company_pool(self):
        return self._company_pool
    
    @company_pool.setter
    def company_pool(self, value):
        if isinstance(value, list):
            if non_valid_symbols := [symbol for symbol in value if not isinstance(symbol, str)]:
                raise TypeError("Not all symbols in `ticker_symbols` are of type string. The"\
                                " following non valid symbols have been provided:"\
                                f" {non_valid_symbols}.")
        elif isinstance(value, str):
            if value not in self._valid_inputs["company_pool"]:
                raise ValueError(f"`company_pool` must be one of {self._valid_inputs['company_pool']}"\
                                 f" or a list of ticker symbols. Received {value}")
        else:
            raise TypeError("`company_pool` must be of type str or list.")
        self._company_pool = value

    @property
    def portfolio_type(self):
        return self._portfolio_type
    
    @portfolio_type.setter
    def portfolio_type(self, value):
        if not isinstance(value, str):
            raise TypeError("`portfolio_type` must be of type str.")
        if value not in self._valid_inputs["portfolio_type"]:
            raise ValueError(f"`portfolio_type` must be one of {self._valid_inputs['portfolio_type']}."\
                             f" Received {value}")
        self._portfolio_type = value

    @property
    def factor_estimate_cov(self):
        return self._factor_estimate_cov
    
    @factor_estimate_cov.setter
    def factor_estimate_cov(self, value):
        if not isinstance(value, bool):
            raise TypeError("`factor_estimate_cov` must be of type bool.")
        self._factor_estimate_cov = value
