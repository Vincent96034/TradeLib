import json
import os
from typing import Union
from dotenv import load_dotenv


class RunConfiguration:
    """ RunConfiguration class is used to load usersettings and variables from.json file.
    When the class is initialized, it will load the usersettings from the.json file and 
    check for validity.
    """
    def __init__(self, dict_source: Union[str, dict]):
        # load usersettings from specified file
        if isinstance(dict_source, str):
            with open(dict_source) as json_file:
                config = json.load(json_file)
        elif isinstance(dict_source, dict):
            config = dict_source
        else:
            raise TypeError(f"Expecting path to .json usersettings or dict, received {type(dict_source)}.")       
        # load variables from specified .env file
        if config["environment"].get("env_path"):
            load_dotenv(config["environment"].get("env_path"))

        # load strategy-configurations
        self.strategy = config["strategy"].get("name") or "hold"
        self._check_strategy_settings()

        # load lemon.markets-configurations
        self.LM_data_key = os.environ.get("LM_data_key") or config["lemon.markets"].get("LM_data_key")
        self.LM_trading_key = os.environ.get("LM_trading_key") or config.get("lemon.markets")["LM_trading_key"]
        self.LM_trading_type = config["lemon.markets"].get("LM_trading_type") or "paper" # or live
        self._check_LM_settings()

    
    def _check_strategy_settings(self) -> None:
        """ Function to check if strategy-settings are valid. """
        valid_strategies = ["hold", "pca"]
        if self.strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy: {self.strategy}. Valid strategies are: {valid_strategies}")
        
    
    def _check_LM_settings(self):
        """ Function to check if lemon.markets-configurations are valid. """
        if not isinstance(self.LM_data_key, str):
            raise TypeError(f"LM_data_key must be a string, received {type(self.LM_data_key)}.")
        if self.LM_data_key is None:
            raise ValueError("LM_data_key is not set.")
        if not isinstance(self.LM_trading_key, str):
            raise TypeError(f"LM_trading_key must be a string, received {type(self.LM_trading_key)}.")
        if self.LM_trading_key is None:
            raise ValueError("LM_trading_key is not set.")
        valid_trading_types = ["paper", "live"]
        if self.LM_trading_type not in valid_trading_types:
            raise ValueError(f"""LM_trading_type must be one of {valid_trading_types},
            received {self.LM_trading_type}.""")
        