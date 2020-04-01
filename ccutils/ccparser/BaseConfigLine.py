import pathlib
import re
import json
import timeit
from ccutils.utils.common_utils import get_logger


class BaseConfigLine(object):

    PATTERN_TYPE = type(re.compile(pattern=""))
    _parent_indent_regex = re.compile(pattern=r"[^! ]", flags=re.MULTILINE)
    _child_indent_regex = re.compile(pattern=r"^ \S", flags=re.MULTILINE)
    _grandchild_indent_regex = re.compile(pattern=r"^  \S", flags=re.MULTILINE)
    comment_regex = re.compile(pattern=r"^(\s+)?!", flags=re.MULTILINE)
    _interface_regex = re.compile(pattern=r"^interface\s(\S+)", flags=re.MULTILINE)

    def __init__(self, number, text, config, verbosity=3):
        """
        **This class is not meant to be instantiated directly, but only from BaseConfigParser instance.**

        Args:
            number (int): Index of line in config
            text (str): Text of the config line
            config (:obj:`BaseConfigParser`): Reference to the parent BaseConfigParser object
            verbosity (:obj:`int`, optional): Logging output level, defaults to 3: Warning

        """
        self.logger = get_logger(name="BaseConfigLine", verbosity=verbosity)
        #print(self.logger.handlers)
        self.config = config
        self.config_lines_obj = self.config.lines
        self.number = number
        self.text = text
        self.indent = len(self.text) - len(self.text.lstrip(" "))
        self.type = None

    def return_obj(self):
        return self

    def _compile_regex(self, regex, flags=re.MULTILINE):
        pattern = None
        try:
            pattern = re.compile(pattern=regex, flags=flags)
        except Exception as e:
            self.logger.error(msg="Error while compiling regex '{}'. Exception: {}".format(regex, repr(e)))
        return pattern

    def get_children(self):
        """
        Return all children lines (all following lines with larger indent)

        Returns:
            list: List of child config lines (objects)

        """
        children = []
        line_num = int(self.number) + 1
        print(len(self.config.lines))
        while line_num <= len(self.config.lines) - 1:   # Avoid IndexError
            if self.config.lines[line_num].indent <= self.indent:
                break
            else:
                children.append(self.config.lines[line_num])
                line_num += 1
        return children

    def re_search_children(self, regex, group=None):
        """
        Search all children for given regex.

        Args:
            regex (:obj:`re.Pattern` or ``str``): Regex to search for
            group (:obj:`str` or ``int``, optional): Return only specific (named or numbered) group of given regex.
                If set to "ALL", return value will be a dictionary with all named groups of the regex.

        Returns:
            list: List of all child object which match given regex, or, if `group` was provided, returns
            list containing matched grop across all children.

                Example::

                    # Given following config section, interface line stored in `line` variable
                    config = '''
                    interface Ethernet0/0
                     description Test Interface
                     ip address 10.0.0.1 255.255.255.0
                     ip address 10.0.1.1 255.255.255.0 secondary
                    !
                    '''
                    pattern = r"^ ip address (?P<ip>\S+) (?P<mask>\S+)"

                    result = line.re_search_children(regex=pattern)
                    print(result)
                    # Returns: [
                    #   [BaseConfigLine #2 (child): ip address 10.0.0.1 255.255.255.0],
                    #   [BaseConfigLine #3 (child): ip address 10.0.1.1 255.255.255.0 secondary]
                    # ]

                    result = line.re_search_children(regex=pattern, group="ip")
                    print(result)
                    # Returns: [
                    #   "10.0.0.1",
                    #   "10.0.1.1"
                    # ]

                    result = line.re_search_children(regex=pattern, group="ALL")
                    print(result)
                    # Returns: [
                    #   {"ip": "10.0.0.1", "mask": "255.255.255.0"},
                    #   {"ip": "10.0.1.1", "mask": "255.255.255.0"}
                    # ]


        """
        pattern = None
        if not isinstance(regex, self.PATTERN_TYPE):
            pattern = self._compile_regex(regex=regex)
        else:
            pattern = regex
        if not pattern:
            return []
        children = self.get_children()
        result = list(filter(lambda x: bool(re.search(pattern=pattern, string=x.text)), children))
        if group:
            result = [x.re_search(regex=pattern, group=group) for x in result]
        return result

    def re_search(self, regex, group=None):
        """
        Search config line for given regex

        Args:
            regex (:obj:`re.Pattern` or ``str``): Regex to search for
            group (:obj:`str` or ``int``, optional): Return only specific (named or numbered) group of given regex.
                If set to "ALL", return value will be a dictionary with all named groups of the regex.

        Examples:

            Example::

                # Given the following line stored in `line` variable
                # " ip address 10.0.0.1 255.255.255"
                pattern = r"^ ip address (?P<ip>\S+) (?P<mask>\S+)"

                # Basic search
                result = line.re_search(regex=pattern)
                print(result)
                # Returns: " ip address 10.0.0.1 255.255.255"

                # Search for specific group
                result = line.re_search(regex=pattern, group="ip")
                print(result)
                # Returns: "10.0.0.1"

                # Get all named groups
                result = line.re_search(regex=pattern, group="ALL")
                print(result)
                # Returns: {"ip": "10.0.0.1", "mask": "255.255.255"}


        Returns:
            str: String that matched given regex, or, if `group` was provided, returns only specific group.

            Returns ``None`` if regex did not match.

        """
        pattern = None
        if not isinstance(regex, self.PATTERN_TYPE):
            pattern = self._compile_regex(regex=regex)
        else: 
            pattern = regex

        if pattern is None:
            self.logger.warning("Got invalid regex {}".format(regex))
            return None
        m = re.search(pattern=pattern, string=self.text)
        if m:
            if group is None:
                return m.group(0)
            elif isinstance(group, int):
                if group <= pattern.groups:
                    return m.group(group)
                else:
                    self.logger.error(msg="Given regex '{}' does not contain required group '{}'".format(regex, group))
                    return None
            elif isinstance(group, str):
                if group in pattern.groupindex.keys():
                    return m.group(group)
                elif group == "ALL":
                    all_groups = list(pattern.groupindex.keys())
                    result = {k: None for k in all_groups}
                    for group in all_groups:
                        try:
                            result[group] = m.group(group)
                        except Exception as e:
                            pass
                    return result
                        
                else:
                    self.logger.error(msg="Given regex '{}' does not contain required group '{}'".format(regex, group))
                    return None
        else:
            self.logger.info(msg="Given regex '{}' did not match.".format(regex))
            return None

    def re_match(self, regex, group=None):
        pattern = None
        if not isinstance(regex, self.PATTERN_TYPE):
            pattern = self._compile_regex(regex=regex)
        else:
            pattern = regex

        if pattern is None:
            return None
        m = re.match(pattern=pattern, string=self.text)
        if m:
            if group is None:
                return m.group(0)
            elif isinstance(group, int):
                if group <= pattern.groups:
                    return m.group(group)
                else:
                    self.logger.error(msg="Given regex '{}' does not contain required group '{}'".format(regex, group))
                    return None
            elif isinstance(group, str):
                if group in pattern.groupindex.keys():
                    return m.group(group)
                else:
                    self.logger.error(msg="Given regex '{}' does not contain required group '{}'".format(regex, group))
                    return None
        else:
            self.logger.info(msg="Given regex '{}' did not match.".format(regex))
            return None

    @property
    def get_type(self):
        """
        Return `types` of config line. Used mostly for filtering purposes.

        Currently available values are:

        - ``parent``
        - ``child``
        - ``interface``
        - ``comment``

        Returns:
            list: List of types

        """
        types = []
        if self.is_parent:
            types.append("parent")
        if self.is_child:
            types.append("child")
        if self.is_interface:
            types.append("interface")
        if re.match(self.comment_regex, self.text):
            types.append("comment")
        return types

    @property
    def is_parent(self):
        """
        Check whether this line is a parent

        Returns:
            bool: True if line is a parent line, False otherwise

        """
        if self.number < len(self.config.lines)-1:
            if self.config.lines[self.number+1].indent > self.indent:
                return True
            else:
                return False
        else:
            return False

    @property
    def is_child(self):
        """
           Check whether this line is a child

           Returns:
               bool: True if line is a child line, False otherwise

           """
        if self.indent > 0:
            return True
        else:
            return False

    @property
    def is_interface(self):
        return bool(re.match(self._interface_regex, self.text))

    def __str__(self):
        return "[BaseConfigLine #{} ({}): '{}']".format(self.number, self.type, self.text)

    def __repr__(self):
        return self.__str__()


