
import datetime
import os
import logging

def must_get_env(key: str) -> str:
    var = os.getenv(key)
    if var is None:
        logging.fatal(f"Required environment variable {key} not set.")
        return ""
    return var

def int_or_zero(string: str) -> int:
    try:
        return int(string)
    except ValueError:
        return 0

def query_timestamp(req, key: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(int_or_zero(req.GET.get(key, 0))).astimezone(datetime.UTC)
