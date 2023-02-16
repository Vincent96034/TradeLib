import json
import os
from typing import Union
from dotenv import load_dotenv



class RunConfiguration:

    def __init__(self, dict_source: Union[str, dict]):

        if isinstance(dict_source, str):
            with open(dict_source) as json_file:
                config = json.load(json_file)

        elif isinstance(dict_source, dict):
            config = dict_source
        else:
            raise TypeError(f"Expecting path to .json usersettings or dics, received {type(dict_source)}.")       

        # load variables from specified .env file
        load_dotenv(config["env_path"])

        # TODO: method that catches exeptions where optional usersettings parameters are not provided at all

        # load configurations
        self.strategy = config["strategy"] or "hold"
        self.LM_data_key = os.environ.get("LM_data_key") or config["LM_data_key"]
        self.LM_trading_key = os.environ.get("LM_trading_key") or config["LM_trading_key"]
        self.LM_trading_type = config["LM_trading_type"] or "paper" # or live

        