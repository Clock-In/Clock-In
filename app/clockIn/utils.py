
import os
import logging

def must_get_env(key: str) -> str:
    var = os.getenv(key)
    if var is None:
        logging.fatal(f"Required environment variable {key} not set.")
        return ""
    return var
