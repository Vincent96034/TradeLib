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

        # load configurations
        self.strategy = config["strategy"]
        self.LM_client_id = os.environ.get("LM_client_id") or config["LM_client_id"]
        self.LM_client_secret = os.environ.get("LM_client_secret") or config["LM_client_secret"]

        