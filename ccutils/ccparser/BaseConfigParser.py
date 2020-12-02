import pathlib
import os
import re
import json
import timeit
from ccutils.utils.common_utils import get_logger
from ccutils.ccparser import BaseConfigLine
from ccutils.ccparser import BaseInterfaceLine
from ccutils.utils import CiscoRange
import functools

re._MAXCACHE = 1024


class BaseConfigParser(object):
    """
    Base Configuration Parser object used for loading configuration files.
    """

    PATTERN_TYPE = type(re.compile(pattern=""))
    INTERFACE_LINE_CLASS = BaseInterfaceLine

    # Patterns
    _vlan_configuration_regex = re.compile(pattern=r"^vlan configuration (?P<vlan_range>[\d\-,]+)", flags=re.MULTILINE)
    _device_tracking_attach_policy_regex = re.compile(pattern=r"^ device-tracking attach-policy (?P<policy>\S+)")

    def __init__(self, config=None, verbosity=4, name="BaseConfigParser", **kwargs):
        """
        Base class for parsing Cisco-like configs

        Args:
            config (:obj:`pathlib.Path` or `str` or `list`): Config file in a form of `pathlib.Path`, or `string`
                containing the entire config or list of lines of the config file
            verbosity (:obj:`int`, optional): Determines the verbosity of logging output, defaults to 4: Info

        Attributes:
            lines (list): Contains list of all config lines stored as objects (see :class:`ccutils.ccparser.BaseConfigLine`)
            config_lines_str (list): Contains list of all config lines stored as strings

        Examples:

            Possible config inputs::

                # Using pathlib
                config_file = pathlib.Path("/path/to/config_file.txt")
                config = BaseConfigParser(config=config_file)

                # Using string
                config_string = '''
                hostname RouterA
                !
                interface Ethernet0/0
                 description Test Interface
                 ip address 10.0.0.1 255.255.255.0
                !
                end
                '''
                config = BaseConfigParser(config=config_string)

                # Using list
                config_list = [
                "hostname RouterA",
                    "!",
                    "interface Ethernet0/0",
                    " description Test Interface",
                    " ip address 10.0.0.1 255.255.255.0",
                    "!",
                    "end"
                ]
                config = BaseConfigParser(config=config_list)

        """
        self.verbosity = verbosity
        self.logger = get_logger(name=name, verbosity=verbosity)
        self.config = config
        self.path = self._check_path(kwargs.get("filepath", None)) if kwargs.get("filepath", None) else None

        self.minimal_results = True
        #: This is a URI.
        self.lines = []
        self.config_lines_str = []
        self.parse()

    @property
    def config_lines_obj(self):
        """
        Kept for backwards compatibility, will be removed in future versions.

        Returns:
            list: BaseConfigParser.lines

        """
        self.logger.warning("DEPRECATED: You are using deprecated property .config_lines_obj use .lines instead.")
        return self.lines

    def parse(self):
        """
        Entry function which triggers the parsing process. Called automatically when instantiating the object.

        :return: ``None``
        """
        if self.config:
            config_lines = []
            # Determine Config Type
            if isinstance(self.config, list):
                self.logger.debug(msg="Treating config as list of config lines.")
                config_lines = [x for x in self.config if (isinstance(x, str) and x != "")]
            elif isinstance(self.config, str):
                path = None
                if os.path.exists(self.config):
                    path = pathlib.Path(self.config)
                if path and path.exists():
                    self.logger.debug(msg="Treating config as filepath.")
                    path = self._check_path(filepath=path)
                    if path:
                        config_lines = [x for x in path.read_text().split("\n") if x != ""]
                else:
                    self.logger.debug(msg="Treating config as multi-line string.")
                    config_lines = [x for x in self.config.split("\n") if x != ""]
            elif isinstance(self.config, pathlib.Path):
                self.logger.debug(msg="Treating config as pathlib Path.")
                path = self._check_path(filepath=self.config)
                if path:
                    config_lines = [x for x in path.read_text().split("\n") if x != ""]
            else:
                self.logger.error("Invalid value passed as config argument.")
                raise ValueError("Invalid value passed as config argument.")
            self.config_lines_str = config_lines
            self.fix_indents()
            self._create_cfg_line_objects()
        else:
            self._get_clean_config()
            self.fix_indents()
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

    def fix_indents(self):
        """
        Function for fixing the indentation level of config lines.

        :return:
        """
        indent_map = list(map(self._get_indent, self.config_lines_str))
        fixed_indent_map = []
        for i in range(len(indent_map)):
            if i == 0:
                fixed_indent_map.append(0)
                continue
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
        """
        Function for generating ``self.lines``.

        """
        start = timeit.default_timer()
        for number, text in enumerate(self.config_lines_str):
            if re.match(pattern=r"^interface\s\S+", string=text, flags=re.MULTILINE):
                self.lines.append(self.INTERFACE_LINE_CLASS(number=number, text=text, config=self, verbosity=self.verbosity).return_obj())
            else:
                self.lines.append(BaseConfigLine(number=number, text=text, config=self, verbosity=self.verbosity).return_obj())
        for line in self.lines:
            line.type = line.get_type
        self.logger.debug(msg="Created {} ConfigLine objects in {} ms.".format(len(self.lines), (timeit.default_timer()-start)*1000))

    def _compile_regex(self, regex, flags=re.MULTILINE):
        """
        Helper function for compiling `re` patterns from string.

        :param str regex: Regex string
        :param flags: Flags for regex pattern, default is re.MULTILINE
        :return:
        """
        pattern = None
        try:
            pattern = re.compile(pattern=regex, flags=flags)
        except Exception as e:
            self.logger.error(msg="Error while compiling regex '{}'. Exception: {}".format(regex, repr(e)))
        return pattern

    def find_objects(self, regex, flags=re.MULTILINE):
        """
        Function for filtering Config Lines Objects based on given regex.

        Args:
            regex (:obj:`re.Pattern` or `str`): Regex based on which the search is done
            flags (:obj:`int`, optional): Set custom flags for regex, defaults to ``re.MULTILINE``

        Examples:

            Example::

                # Initialize the object
                config = BaseConfigParser(config="/path/to/config_file.cfg")

                # Define regex for matching config lines
                interface_regex = r"^ interface"

                # Apply the filter
                interface_lines = config.find_objects(regex=interface_regex)

                # Returns subset of ``self.lines`` which match specified regex

        """
        pattern = None
        if not isinstance(regex, self.PATTERN_TYPE):
            pattern = self._compile_regex(regex=regex, flags=flags)
        else:
            pattern = regex
        results = []
        for line in self.lines:
            if re.search(pattern=pattern, string=line.text):
                results.append(line)
        self.logger.debug(msg="Matched {} lines for query '{}'".format(len(results), regex))
        return results

    def get_section_by_parents(self, parents):
        if not isinstance(parents, list):
            parents = list(parents)
        section = list(self.lines)
        for parent in parents:
            section = [x.get_children() for x in section if bool(x.is_parent and x.re_match(parent))]
            if len(section) == 1:
                section = section[0]
            elif len(section) > 1:
                self.logger.error("Multiple lines matched parent statement. Cannot determine config section.")
                return []
            else:
                self.logger.error("No lines matched parent statement. Cannot determine config section.")
                return []
        return section

    def match_to_dict(self, line, patterns):
        """

        Args:
            line: Instance of `BaseConfigLine` object
            patterns: List of compiled `re` patterns
            minimal_result: Bool, if True, omits keys with value `None`

        Returns:
            dict: Dictionary containing named groups across all provided patterns

        """
        entry = {}

        for pattern in patterns:
            match_result = line.re_search(regex=pattern, group="ALL")
            if match_result is not None:
                entry.update(match_result)
            else:
                if self.minimal_results:
                    continue
                else:
                    entry.update({k: None for k in pattern.groupindex.keys()})
        return entry

    def property_autoparse(self, candidate_pattern, patterns):
        """
        Function for searching multiple patterns across all occurrences of lines that matched candidate_pattern
        Args:
            candidate_pattern:
            patterns:

        Returns:

        """
        properties = None
        candidates = self.find_objects(regex=candidate_pattern)
        if len(candidates):
            properties = []
        else:
            return properties
        for candidate in candidates:
            properties.append(self.match_to_dict(line=candidate, patterns=patterns))
        return properties

    def section_property_autoparse(self, parent, patterns, return_with_line=False):
        entries = None
        if isinstance(parent, BaseConfigLine):
            candidates = [parent]
        elif isinstance(parent, (str, self.PATTERN_TYPE)):
            candidates = self.find_objects(regex=parent)
        if len(candidates):
            entries = []
        else:
            return entries
        for candidate in candidates:
            entry = {}
            if isinstance(parent, (str, self.PATTERN_TYPE)):
                entry.update(self.match_to_dict(line=candidate, patterns=[parent]))
            for pattern in patterns:
                updates = candidate.re_search_children(regex=pattern, group="ALL")
                if len(updates) == 1:
                    entry.update(updates[0])
                elif len(updates) == 0:
                    if self.minimal_results:
                        continue
                    else:
                        entry.update({k: None for k in pattern.groupindex.keys()})
                else:
                    self.logger.warning("Multiple possible updates found for Pattern: '{}' on Candidate: '{}'".format(pattern, candidate))
            if return_with_line:
                entries.append((candidate, entry))
            else:
                entries.append(entry)
        return entries

    @property
    @functools.lru_cache()
    def hostname(self):
        hostname = None
        regex = r"^hostname\s(\S+)"
        candidates = self.find_objects(regex=regex)
        if len(candidates):
            hostname = candidates[0].re_search(regex=regex, group=1)
        return hostname

    @property
    @functools.lru_cache()
    def cdp(self):
        if len(self.find_objects(regex="^no cdp run")):
            return False
        else:
            return True

    @property
    def domain_name(self):
        domain_name = None
        domain_name_regex = re.compile(pattern=r"^ip domain.name (?P<domain_name>\S+)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=domain_name_regex)
        if len(candidates):
            domain_name = candidates[0].re_search(regex=domain_name_regex, group="domain_name")
        return domain_name

    @property
    @functools.lru_cache()
    def name_servers(self):
        name_servers = []
        name_servers_regex = re.compile(pattern=r"^ip name.server (?P<name_servers>(?:\d{1,3}\.){3}\d{1,3}(?: (?:\d{1,3}\.){3}\d{1,3})*)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=name_servers_regex)
        for candidate in candidates:
            name_servers.extend(re.findall(pattern=r"(?:\d{1,3}\.){3}\d{1,3}", string=candidate.text))
        return name_servers

    @property
    def vlans(self):
        vlans = {}
        # Basic VLAN Definition
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
        # VLAN Configuration
        candidates = self.find_objects(regex=self._vlan_configuration_regex)
        for candidate in candidates:
            vlan_range = CiscoRange(candidate.re_search(regex=self._vlan_configuration_regex, group="vlan_range"))
            policy = candidate.re_search_children(regex=self._device_tracking_attach_policy_regex, group="policy")
            if len(policy):
                for vlan_id in vlan_range:
                    vlans[vlan_id]["device_tracking_policy"] = policy[0]
        return vlans

    @property
    def vlan_groups(self):
        vlan_group_regex = re.compile(pattern=r"^vlan group (?P<group>\S+) vlan-list (?P<vlan_id>\d+)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=vlan_group_regex)
        return [x.re_search(regex=vlan_group_regex, group="ALL") for x in candidates]

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

    @property
    def interface_lines(self):
        return (x for x in self.lines if x.is_interface)

