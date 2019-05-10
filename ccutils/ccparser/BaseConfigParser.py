import pathlib
import re
import json
import timeit
from ccutils.utils.common_utils import get_logger
from ccutils.ccparser import BaseConfigLine
from ccutils.ccparser import BaseInterfaceLine


class BaseConfigParser(object):

    def __init__(self, filepath, verbosity=1):
        self.verbosity = verbosity
        self.logger = get_logger(name="ConfigParser", verbosity=verbosity)
        self.path = self._check_path(filepath=filepath)
        self.config_lines_str = []
        self.config_lines_obj = []

        self._get_clean_config()
        self._create_cfg_line_objects()
        

    def _check_path(self, filepath):
        path = None
        if not isinstance(filepath, pathlib.Path):
            path = pathlib.Path(filepath)
        else:
            path = filepath
        if not path.exists():
            self.logger.error(msg="Path '{}' does not exist.".format(filepath))
            return None
        if not path.is_file():
            self.logger.error(msg="Path '{}' is not a file.".format(filepath))
        if not path.is_absolute():
            path = path.resolve()
            self.logger.debug("Path '{}' is existing file.".format(filepath))
            return path
        else:
            self.logger.debug("Path '{}' is existing file.".format(filepath))
            return path

    def _get_indent(self, line):
        indent_size = len(line) - len(line.lstrip(" "))
        return indent_size

    def _get_clean_config(self, first_line_regex=r"^version \d+\.\d+", last_line_regex=r"^end"):
        first_regex = re.compile(pattern=first_line_regex, flags=re.MULTILINE)
        last_regex = re.compile(pattern=last_line_regex, flags=re.MULTILINE)
        all_lines = self.path.read_text().split("\n")
        first = None
        last = None
        for i in range(len(all_lines)):
            if not first:
                if re.match(pattern=first_regex, string=all_lines[i]):
                    first = i
                    self.logger.debug(msg="Found first config line: '{}'".format(all_lines[first]))
            if not last:
                if re.match(pattern=last_regex, string=all_lines[i]):
                    last = i
                    self.logger.debug(msg="Found last config line: '{}'".format(all_lines[last]))
                    break
        if not first or not last:
            self.config_lines_str = []
            self.logger.error(msg="No valid config found!")
        else:
            self.config_lines_str = all_lines[first:last + 1]
            self.logger.info(msg="Loading {} config lines.".format(len(self.config_lines_str)))
        # Fix indent
        indent_map = list(map(self._get_indent, self.config_lines_str))
        fixed_indent_map = []
        for i in range(len(indent_map)):
            if indent_map[i] == 0:
                fixed_indent_map.append(0)
                continue
            if indent_map[i] == indent_map[i-1]:
                fixed_indent_map.append(fixed_indent_map[-1])
            elif indent_map[i] > indent_map[i-1]:
                fixed_indent_map.append(fixed_indent_map[-1]+1)
            elif indent_map[i] < indent_map[i-1]:
                fixed_indent_map.append(fixed_indent_map[-1]-1)
        for i, val in enumerate(fixed_indent_map):
            self.config_lines_str[i] = " "*val + self.config_lines_str[i].strip()
            #print(val, "'{}'".format(self.config_lines_str[i]))

    def _create_cfg_line_objects(self):
        start = timeit.default_timer()
        for number, text in enumerate(self.config_lines_str):
            if re.match(pattern=r"^interface\s\S+", string=text, flags=re.MULTILINE):
                self.config_lines_obj.append(BaseInterfaceLine(number=number, text=text, config=self, verbosity=self.verbosity).return_obj())
            else:
                self.config_lines_obj.append(BaseConfigLine(number=number, text=text, config=self, verbosity=self.verbosity).return_obj())
        for line in self.config_lines_obj:
            line.type = line.get_type
        self.logger.debug(msg="Created {} ConfigLine objects in {} ms.".format(len(self.config_lines_obj), (timeit.default_timer()-start)*1000))

    def _compile_regex(self, regex, flags=re.MULTILINE):
        pattern = None
        try:
            pattern = re.compile(pattern=regex, flags=flags)
        except Exception as e:
            self.logger.error(msg="Error while compiling regex '{}'. Exception: {}".format(regex, repr(e)))
        return pattern

    def find_objects(self, regex, flags=re.MULTILINE):
        pattern = None
        if not isinstance(regex, re._pattern_type):
            pattern = self._compile_regex(regex=regex, flags=flags)
        else:
            pattern = regex
        results = []
        for line in self.config_lines_obj:
            if re.search(pattern=pattern, string=line.text):
                results.append(line)
        self.logger.debug(msg="Matched {} lines for query '{}'".format(len(results), regex))
        return results


    def get_hostname(self):
        hostname = None
        regex = r"^hostname\s(\S+)"
        candidates = self.find_objects(regex=regex)
        if len(candidates):
            hostname = candidates[0].re_search(regex=regex, group=1)
        return hostname

    @property
    def cdp(self):
        if len(self.find_objects(regex="^no cdp run")):
            return False
        else:
            return True
    
    @property
    def domain_name(self):
        domain_name = None
        domain_name_regex = re.compile(pattern=r"^ip domain-name (?P<domain_name>\S+)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=domain_name_regex)
        if len(candidates):
            domain_name = candidates[0].re_search(regex=domain_name_regex, group="domain_name")
        return domain_name
    
    @property
    def name_servers(self):
        name_servers = []
        name_servers_regex = re.compile(pattern=r"^ip name-server (?P<name_server>(?:\d{1,3}\.){3}\d{1,3})", flags=re.MULTILINE)
        candidates = self.find_objects(regex=name_servers_regex)
        for candidate in candidates:
            name_servers.append(candidate.re_search(regex=name_servers_regex, group="name_server"))
        return name_servers

    @property
    def vlans(self):
        vlans = {}
        vlan_id_regex = re.compile(pattern=r"^vlan (?P<vlan_id>\d+)", flags=re.MULTILINE)
        vlan_name_regex = re.compile(pattern=r"^ name (?P<vlan_name>\S+)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=vlan_id_regex)
        for candidate in candidates:
            vlan_id = candidate.re_search(regex=vlan_id_regex, group="vlan_id")
            vlan_name = None
            vlan_name_candidate = candidate.re_search_children(regex=vlan_name_regex, group="vlan_name")
            if len(vlan_name_candidate):
                vlan_name = vlan_name_candidate[0]
            vlans[vlan_id] = {"name": vlan_name}
        return vlans

    @property
    def vrfs(self):
        vrfs = None
        vrf_name_regex = re.compile(pattern=r"^(?:ip )?vrf(?: definition)? (?P<vrf_name>\S+)", flags=re.MULTILINE)
        rd_regex = re.compile(pattern=r"^ rd (?P<rd>\S+)", flags=re.MULTILINE)
        description_regex = re.compile(pattern=r"^ description (?P<description>.*)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=vrf_name_regex)
        if len(candidates):
            vrfs = {}
        for candidate in candidates:
            vrf_name = candidate.re_search(regex=vrf_name_regex, group="vrf_name")
            if vrf_name:
                vrfs[vrf_name] = {}
            else:
                continue
            rd_candidates = candidate.re_search_children(regex=rd_regex, group="rd")
            if len(rd_candidates):
                vrfs[vrf_name]["rd"] = rd_candidates[0]
            else:
                vrfs[vrf_name]["rd"] = None
            description_candidates = candidate.re_search_children(regex=description_regex, group="description")
            if len(description_candidates):
                vrfs[vrf_name]["description"] = description_candidates[0]
            else: 
                vrfs[vrf_name]["description"] = None
        return vrfs

    @property
    def static_routes(self):
        # TODO: Add parsing for static routes
        pass


