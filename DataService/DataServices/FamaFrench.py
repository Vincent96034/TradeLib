import os
import zipfile
import urllib.request
import pandas as pd
import datetime as dt
from typing import Union
from urllib.error import URLError

from DataService.DataService import DataService
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class FamaFrench(DataService):
    def __init__(self):
        super().__init__()
        self.name = "Fama & French Factor Data"
        self.homepage = "http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/index.html"
        self.data_category = "Financial"
        self.data_types = ["monthly", "factors"]
        self._ff_df = pd.DataFrame()
        self.latest_date = None

    def _download_and_prepare_data(self) -> None:
        """ Downloads Fama & French data from the web and prepares it for further processing.

            Raises:
                URLError: If an error occurs while downloading the Fama & French data.
                OSError: If an error occurs while deleting the temporary files created during the process.
        """
        try:
            logger.info("Downloading `Fama & French` data from the web ...")
            ff_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
            urllib.request.urlretrieve(ff_url,'DataService/DataServices/temp/fama_french.zip')
        except URLError as url_e:
            logger.error(f"An URL-Error occured when downloading `Fama & French` data: {url_e}")
        # open zip file in temp folder, create .csv, create pandas df, delete files again
        with zipfile.ZipFile('DataService/DataServices/temp/fama_french.zip', 'r') as z_file:
            z_file.extractall("DataService/DataServices/temp/")
            ff_factors =  pd.read_csv('DataService/DataServices/temp/F-F_Research_Data_Factors.csv', skiprows = 3)
        try:
            os.remove('DataService/DataServices/temp/fama_french.zip')
            os.remove('DataService/DataServices/temp/F-F_Research_Data_Factors.csv')
        except OSError as e:
            logger.error(f"Could not delete temp files of `Fama & French` data.")
        # process df
        ff_factors = ff_factors.rename(columns={"Unnamed: 0": "date"})
        ff_factors["date"] = pd.to_numeric(ff_factors["date"], errors="coerce")
        ff_factors = ff_factors[ff_factors["date"] > 99999] # remove annual data
        ff_factors = ff_factors.astype({"date": int, "Mkt-RF": float, "SMB": float, "HML": float, "RF": float})
        ff_factors.index = ff_factors["date"]
        ff_factors = ff_factors.drop(labels="date", axis="columns")
        ff_factors.index = pd.to_datetime(ff_factors.index, format= '%Y%m')
        ff_factors.index = ff_factors.index + pd.offsets.MonthEnd()
        ff_factors = ff_factors.apply(lambda x: x/ 100)
        self._ff_df = ff_factors
        self.latest_date = str(ff_factors.index[-1].date())

    def famafrench_data_historic(self,
                                 start: Union[None, str] = None,
                                 stop: Union[None, str] = None,
                                 update: bool = False) -> pd.DataFrame:
        """ Retrieves historic Fama & French data in the specified date range, or the
        entire dataset if no date range is specified.

        Args:
            self: Instance of the class.
            start: Start date of the desired date range in 'YYYY-MM-DD' format.
                Defaults to None.
            stop: End date of the desired date range in 'YYYY-MM-DD' format.
                Defaults to None.
            update: If True, downloads and updates the Fama & French data before
                returning the results. Defaults to False.

        Returns:
            A pandas DataFrame containing the Fama & French data in the specified
            date range, or the entire dataset if no date range is specified.

        Example Ouput:
                    Mkt-RF	SMB	    HML	    RF
        date				
        1926-07-31	0.0296	-0.0256	-0.0243	0.0022
        1926-08-31	0.0264	-0.0117	0.0382	0.0025
        1926-09-30	0.0036	-0.0140	0.0013	0.0023
        """
        if start:
            self._validate_date(start)
        if stop:
            self._validate_date(stop)
        if self._ff_df.empty or (update):
            self._download_and_prepare_data()
        return self._ff_df.loc[start:stop]
    
    @staticmethod
    def _validate_date(date_string):
        """ Validates a date string in 'YYYY-MM-DD' format. """
        if not isinstance(date_string, str):
            raise TypeError("Input must be of type string.")
        try:
            dt.date.fromisoformat(date_string)
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")
