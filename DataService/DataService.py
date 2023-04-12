import pandas as pd
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class DataService:
    def __init__(self):
        # metadata for DataServices
        self.name = None
        self.homepage = None
        self.data_category = None
        self.data_types = None
        self.min_limit = None
        self.day_limit = None
        self.API_KEY = None
    
    def ticker_data_historic(self, *args, **kwargs):
        raise NotImplementedError("Method hasn't been implemented yet.")

    @classmethod
    def get_methods(cls):
        methods = [attribute for attribute in dir(cls)
                    if callable(getattr(cls, attribute))
                        and attribute.startswith('__') is False]
        return methods

    @staticmethod
    def check_output_frame(func):
        """ Decorator function to check output of methods for na-values. """
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if isinstance(res, pd.DataFrame):
                na_columns = res.columns[res.isnull().any()].to_list()
                if na_columns:
                    logger.warn("The output dataframe contains empty values in" \
                                f" the columns {na_columns}")
            return res
        return wrapper
    
    def __repr__(self):
        return f"<DataService: {self.name} ({self.homepage}) - Category {self.data_category}>"



# To be Implemented:
# - YFinance
# - iexfinance
# - Fama & French
# - 