import json
import pathlib
import logging
import sys
import pandas as pd
import re


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

def load_json(path):
    path = check_path(path)
    data = None
    if path:
        with path.open(mode="r") as f:
            data = json.load(f)
    return data

def split_interface_name(interface):
    pattern = re.compile(pattern=r"(?P<name>[A-z-]+)(?P<number>[\d\/]+)")
    match = re.match(pattern=pattern, string=interface)
    if match:
        return [match.group("name"), match.group("number")]
    else:
        return None

def match_to_json(match, groups):
    result = {k:None for k in groups}
    for group in groups:
        try:
            result[group] = match.group(group)
        except Exception:
            pass
    return result

def check_path(path, create=False):
    return_path = None
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)
    if path.exists():
        if path.is_file():
            return_path = path
        elif path.is_dir():
            return_path = path
    else:
        if create:
            if "." not in path.name[1:]:
                # Path is a folder
                path.mkdir(parents=True)
                if path.exists():
                    return_path = path
            else:
                # Path is a file
                if path.parent.exists():
                    path.touch()
                    return_path = path
                else:
                    path.parent.mkdir()
                    if path.parent.exists():
                        path.touch()
                        return_path = path
    return return_path

def jprint(data, indent=2):
    print(json.dumps(obj=data, indent=indent))

def load_excel_sheet(file, sheet_name):
    file = check_path(file)
    if not file:
        return None
    df = pd.read_excel(io=file, sheet_name=sheet_name)
    df = df.where((pd.notnull(df)), None)
    data = {}
    for column in df.columns:
        data[column] = list(df[column])
    return data

