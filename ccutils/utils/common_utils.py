import json
import pathlib
import logging
import sys
import re
from collections import OrderedDict


class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass


class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))


def get_logger(name, verbosity=4):
    """
    """

    verbosity_map = {
        1: logging.CRITICAL,
        2: logging.ERROR,
        3: logging.WARNING,
        4: logging.INFO,
        5: logging.DEBUG
    }

    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]\t[%(module)s][%(funcName)s]\t%(message)s')
    handler.setFormatter(formatter)
    if not len(logger.handlers):
        logger.addHandler(handler)
    logger.setLevel(verbosity_map[verbosity])

    # To be removed
    # TODO: Remove
    # if verbosity == 0:
    #     logger.setLevel(logging.WARN)
    # elif verbosity == 1:  # default
    #     logger.setLevel(logging.INFO)
    # elif verbosity > 1:
    #     logger.setLevel(logging.DEBUG)

    return logger


logger = get_logger(__name__, verbosity=3)


def load_json(path):
    path = check_path(path)
    data = None
    if path:
        with path.open(mode="r") as f:
            data = json.load(f)
    return data


def split_interface_name(interface: str):
    """
    This function takes in interface string such as "GigabitEthernet0/10" and returns a list containing name and number,
    such as ["GigabitEthernet", "0/10"]

    Args:
        interface (str): Interface to perform split on

    Returns:
        list: List containing name and number of interface, such as ``["GigabitEthernet", "0/10"]``

    """
    #pattern = re.compile(pattern=r"(?P<name>^[A-z\-]+(?=\d))(?P<number>[\d+\/]+)")
    pattern = re.compile(pattern=r"(?P<name>[A-z]{2,}(?:[A-z\-])*)(?P<number>\d+(?:\/\d+)*(?:\:\d+)?(?:\.\d+)?)")
    try:
        match = re.match(pattern=pattern, string=interface)
    except TypeError as e:
        logger.error("Expected string or bytes-like object, cannot match on '{}'".format(type(interface)))
        return None
    if match:
        return [match.group("name"), match.group("number")]
    else:
        logger.error("Given interface {} did not match parsing pattern.".format(interface))
        return None


def convert_interface_name(interface: str, out: str="long"):
    """
    This function converts interface names between long and short variants.
    For example Fa0/1 -> FastEthernet0/1 or the other way around.

    :param interface:
    :param out:
    :rtype: str
    :return: Interface string
    """
    short = [
        "Eth", "Et", "Se", "Fa", "Gi", "Te", "Twe", "Fo", "Hu", "Po", "Tu", "Vl", "Lo", "pw"
    ]
    long = [
        "Ethernet", "Ethernet", "Serial", "FastEthernet", "GigabitEthernet",
        "TenGigabitEthernet", "TwentyFiveGigE", "FortyGigabitEthernet", "HundredGigE", "Port-channel", "Tunnel",
        "Vlan", "Loopback", "pseudowire"
    ]
    interface_s = split_interface_name(interface)
    if interface_s is None:
        logger.error("Cannot convert given interface.")
        return interface
    else:
        given_form = None
        index = None
        name, number = interface_s
        if name in short:
            given_form = "short"
            index = short.index(name)
        elif name in long:
            given_form = "long"
            index = long.index(name)
        else:
            given_form = "unknown"
            logger.warning("Got unknown interface name: '{}'".format(name))

        if out == "long":
            # Return full version
            if given_form == "long":
                return interface
            elif given_form == "short":
                return long[index] + number
            else:
                # Error
                return interface
        elif out == "short":
            # Return full version
            if given_form == "short":
                return interface
            elif given_form == "long":
                return short[index] + number
            else:
                # Error
                return interface
        else:
            return interface


def match_to_json(match, groups):
    """
    This function converts `re` match object to dict

    :param match: re.match object
    :param groups: list
    :rtype: dict
    :return: Dictionary with matched groups
    """
    result = {k: None for k in groups}
    for group in groups:
        try:
            result[group] = match.group(group)
        except Exception:
            pass
    return result


def remove_empty_values(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if v is not None}


def strip_none(data):
    # https://stackoverflow.com/questions/20558699/python-how-recursively-remove-none-values-from-a-nested-data-structure-lists-a
    if isinstance(data, dict):
        return {k: strip_none(v) for k, v in data.items() if k is not None and v is not None}
    elif isinstance(data, list):
        return [strip_none(item) for item in data if item is not None]
    elif isinstance(data, tuple):
        return tuple(strip_none(item) for item in data if item is not None)
    elif isinstance(data, set):
        return {strip_none(item) for item in data if item is not None}
    else:
        return data


def value_to_bool(entry: dict, keys: list, keep_none=False) -> dict:
    if not isinstance(keys, list):
        keys = list[keys]
    for key in keys:
        if key not in entry.keys():
            continue
        if entry[key] is not None:
            entry[key] = True
        else:
            if keep_none:
                continue
            else:
                entry[key] = False
        return entry


def check_path(path, create=False):
    """

    :param path:
    :param create:
    :return:
    """
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


def interface_sort(crange, name):
    index = crange._list.index(name)
    return crange._list.index(name)


def jprint(data, indent=2):
    print(json.dumps(obj=data, indent=indent))

def has_old_pyyaml():
    try:
        from packaging import version
    except ModuleNotFoundError:
        logger.error("Cannot determine version o PyYAML, missing 'packaging' package. Acting like PyYAML >= 5.1")
        version = None
        return False
    try:
        import yaml
    except ImportError:
        logger.error("Missing Package PyYAML")
        return False

    return version.parse(yaml.__version__) < version.parse("5.1")

def load_excel_sheet(file, sheet_name):
    try:
        import pandas as pd
    except ImportError:
        print("To use 'load_excel_sheet' function you need to have 'pandas' installed.")
        pd = None
    if pd:
        file = check_path(file)
        if not file:
            return None
        df = pd.read_excel(io=file, sheet_name=sheet_name)
        df = df.where((pd.notnull(df)), None)
        data = {}
        for column in df.columns:
            data[column] = list(df[column])
        return data
    else:
        return None

