import json
import pathlib
import logging
import sys


def get_logger(name, verbosity=1):
    """
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(module)s: %(message)s')
    handler.setFormatter(formatter)
    if not len(logger.handlers):
        logger.addHandler(handler)

    if verbosity == 0:
        logger.setLevel(logging.WARN)
    elif verbosity == 1:  # default
        logger.setLevel(logging.INFO)
    elif verbosity > 1:
        logger.setLevel(logging.DEBUG)

    return logger


def check_path(path):
    p = pathlib.Path(path)
    if p.exists():
        if not p.is_absolute():
            p = p.resolve()
        #print(p)
        return p
    else:
        print("ERROR: Specified path does not exist.")
        return None


def load_json(path):
    path = check_path(path)
    data = None
    if path:
        with path.open(mode="r") as f:
            data = json.load(f)
    return data
