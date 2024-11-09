import os
from dotenv import load_dotenv


def find_in_env(env_var: str, env_file: str = ".env") -> str:
    """Function to find a variable in the environment or raise an error."""
    load_dotenv(env_file)
    try:
        return os.environ[env_var]
    except KeyError:
        raise KeyError(f"Environment variable `{env_var}` not found in `{env_file}`.")
