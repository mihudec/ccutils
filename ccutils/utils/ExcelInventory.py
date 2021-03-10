import pathlib
import unicodedata
import yaml
import re
from ccutils.utils.common_utils import get_logger, interface_sort
from ccutils.utils.CiscoRange import CiscoRange
from ccutils.utils.CustomAnsibleDumper import CustomAnsibleDumper
from collections import OrderedDict
from pprint import pprint


try:
    import pandas as pd
except ImportError:
    print("To use 'ExcelInventory' function you need to have 'pandas' installed.")
    pd = None

class GroupDoesNotExist(Exception):
    pass

class HostDoesNotExist(Exception):
    pass

class ObjectNotFound(object):
    pass

    def __repr__(self):
        return "[ObjectNotFound]"

    def __str__(self):
        return "[ObjectNotFound]"

    def __bool__(self):
        return False

class ExcelInventory(object):
    pass

    def __init__(self, input_file, output_dir, verbosity=4):
        self.logger = get_logger(name="ExcelInventory", verbosity=verbosity)
        self.input_file = self.check_path(path=input_file, mode="file")
        self.output_dir = self.check_path(path=output_dir, mode="directory")
        self.host_vars = {}
        self.group_vars = {}
        self.hosts = {}

    def check_path(self, path, mode):
        """
        """
        self.logger.info("Checking Path: '{}'".format(path))
        try:
            if not isinstance(path, pathlib.Path):
                path = pathlib.Path(path)
            if path.exists():
                if path.is_file() and mode == "file":
                    self.logger.info("Path: '{}' Exists: File.".format(path))
                elif path.is_file() and mode == "directory":
                    self.logger.critical("Path: '{}' Exists but is not a file!".format(path))
                    path = None
                elif not path.is_file() and mode == "directory":
                    self.logger.info("Path: '{}' Exists: Directory.".format(path))
                elif not path.is_file() and mode == "file":
                    self.logger.critical("Path: '{}' Exists but is not a directory!".format(path))
                    path = None
                else:
                    self.logger.critical("Path: '{}' Unhandled error!".format(path))
            else:
                self.logger.critical("Path: '{}' Does not exist!".format(path))
        except Exception as e:
            self.logger.critical("Could not determine valid path for '{}'. Exception: {}".format(path, repr(e)))
        finally:
            return path

    def load_excel(self, path, sheet_name, index_column=None, columns_rename=None, **kwargs):
        self.logger.info("Loading file: '{}' Sheet: '{}' as DF".format(path, sheet_name))
        df = pd.read_excel(io=path, sheet_name=sheet_name, index_col=index_column, engine="openpyxl", **kwargs)
        df = df.where(pd.notnull(df), None)
        if columns_rename is not None:
            df = df.rename(columns=columns_rename)
        return df

    def duplicates_check(self, df, columns):
        results = []
        for column_name in columns:
            duplicates = df.duplicated(subset=[column_name])
            results.append(any(duplicates))
            if results[-1]:
                self.logger.warning(
                    "Found duplicated values in column '{0}': {1}".format(column_name, df[duplicates][column_name]))
        return results

    @staticmethod
    def replace_cz_chars(line):
        line = unicodedata.normalize('NFKD', line)
        output = ''
        for c in line:
            if not unicodedata.combining(c):
                output += c
        return output

    def _finditem(self, obj, key):
        if key in obj:
            return obj
        for k, v in obj.items():
            if isinstance(v, dict):
                return self._finditem(v, key)  # added return statement
        return ObjectNotFound()

    def recursive_parent_lookup(self, key, obj):
        if key in obj:
            return obj
        for v in obj.values():
            if isinstance(v, dict):
                a = self.recursive_parent_lookup(key=key, obj=v)
                if not isinstance(a, ObjectNotFound):
                    return a
        return ObjectNotFound()

    def get_ordered_interfaces(self, host):
        """
        Return interfaces as OrderedDict

        Returns:
            (:obj:`OrderedDict`): Interface section as OrderedDict

        """
        if host not in self.host_vars.keys():
            msg = "Host '{}' does not exist".format(host)
            raise HostDoesNotExist(msg)
        if "interfaces" not in self.host_vars[host].keys():
            return OrderedDict()
        interfaces_crange = CiscoRange(list(self.host_vars[host]["interfaces"].keys()))
        ordered_interfaces = OrderedDict(sorted(self.host_vars[host]["interfaces"].items(), key=lambda x: interface_sort(crange=interfaces_crange, name=x[0])))
        return ordered_interfaces

    def dump_hosts(self, outputfile):
        self.logger.info("Storing hosts as YAML file.")
        with self.output_dir.joinpath(outputfile).open(mode="w") as f:
            yaml.dump(data=self.hosts, stream=f, Dumper=CustomAnsibleDumper)

    def dump_hostvars(self, nested=False):
        self.logger.info("Storing host_vars as YAML files.")
        if self.output_dir is not None:
            host_vars_path = self.output_dir.joinpath("host_vars")
            host_vars_path.mkdir(exist_ok=True)
        for hostname, host_vars in self.host_vars.items():
            if not nested:
                path = host_vars_path.joinpath("{}.yml".format(hostname))
                with path.open(mode="w") as f:
                    data = dict(host_vars)
                    data["interfaces"] = self.get_ordered_interfaces(host=hostname)
                    yaml_string = yaml.dump(data=data, Dumper=CustomAnsibleDumper)
                    yaml_string = re.sub("'\"(.*)\"'", '"\\1"', yaml_string)
                    f.write(yaml_string)
                    # yaml.dump(data=host_vars, stream=f, Dumper=CustomAnsibleDumper)
            else:
                host_path = host_vars_path.joinpath(hostname)
                host_path.mkdir(exist_ok=True)
                general_path = host_path.joinpath("{}.yml".format(hostname))
                interfaces_path = host_path.joinpath("interfaces.yml")
                data = dict(host_vars)
                # Interfaces Section
                interfaces_data = {"interfaces": self.get_ordered_interfaces(host=hostname)}
                with interfaces_path.open(mode="w") as f:
                    yaml_string = yaml.dump(data=interfaces_data, Dumper=CustomAnsibleDumper)
                    yaml_string = re.sub("'\"(.*)\"'", '"\\1"', yaml_string)
                    f.write(yaml_string)

                # General Section
                general_data = data
                del general_data["interfaces"]
                with general_path.open(mode="w") as f:
                    yaml_string = yaml.dump(data=general_data, Dumper=CustomAnsibleDumper)
                    yaml_string = re.sub("'\"(.*)\"'", '"\\1"', yaml_string)
                    f.write(yaml_string)

    def dump_groupvars(self, nested=False):
        self.logger.info("Storing group_vars as YAML files.")
        if self.output_dir is not None:
            group_vars_path = self.output_dir.joinpath("group_vars")
            group_vars_path.mkdir(exist_ok=True)
        for groupname, group_vars in self.group_vars.items():
            if not nested:
                path = group_vars_path.joinpath("{}.yml".format(groupname))
                with path.open(mode="w") as f:
                    yaml.dump(data=group_vars, stream=f, Dumper=CustomAnsibleDumper)
            else:
                group_path = group_vars_path.joinpath(groupname)
                group_path.mkdir(exist_ok=True)
                general_path = group_path.joinpath("{}.yml".format(groupname))
                with general_path.open(mode="w") as f:
                    yaml.dump(data=group_vars, stream=f, Dumper=CustomAnsibleDumper)

