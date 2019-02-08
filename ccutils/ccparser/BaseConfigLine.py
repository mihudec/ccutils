import pathlib
import re
import json
import timeit
from ccutils.utils.common_utils import get_logger

class BaseConfigLine(object):
    parent_indent_regex = re.compile(pattern=r"[^! ]", flags=re.MULTILINE)
    child_indent_regex = re.compile(pattern=r"^ \S", flags=re.MULTILINE)
    grandchild_indent_regex = re.compile(pattern=r"^  \S", flags=re.MULTILINE)
    comment_regex = re.compile(pattern=r"^(\s+)?!", flags=re.MULTILINE)
    interface_regex = re.compile(pattern=r"^interface\s(\S+)", flags=re.MULTILINE)

    def __init__(self, number, text, config, verbosity):
        self.logger = get_logger(name="BaseConfigLine #{}".format(number), verbosity=verbosity)
        #print(self.logger.handlers)
        self.config_lines_obj = config
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
        children = []
        line_num = int(self.number) + 1
        while line_num < len(self.config_lines_obj) - 1:
            if self.config_lines_obj[line_num].indent <= self.indent:
                break
            else:
                children.append(self.config_lines_obj[line_num])
                line_num += 1
        return children

    def re_search_children(self, regex, group=None):
        pattern = None
        if not isinstance(regex, re._pattern_type):
            pattern = self._compile_regex(regex=regex)
        else:
            pattern = regex
        if not pattern:
            return []
        children = self.get_children()
        result = list(filter(lambda x: bool(re.search(pattern=pattern, string=x.text)), children))
        if group:
            result = list(map(lambda x: x.re_search(regex=regex, group=group), result))
        return result


    def re_search(self, regex, group=None):
        pattern = None
        if not isinstance(regex, re._pattern_type):
            pattern = self._compile_regex(regex=regex)
        else: 
            pattern = regex

        if pattern is None:
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
                else:
                    self.logger.error(msg="Given regex '{}' does not contain required group '{}'".format(regex, group))
                    return None
        else:
            self.logger.info(msg="Given regex '{}' did not match.".format(regex))
            return None

    def re_match(self, regex, group=None):
        pattern = None
        if not isinstance(regex, re._pattern_type):
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
        if self.number < len(self.config_lines_obj)-1:
            if self.config_lines_obj[self.number+1].indent > self.indent:
                return True
            else:
                return False
        else:
            return False

    @property
    def is_child(self):
        if self.indent > 0:
            return True
        else:
            return False

    @property
    def is_interface(self):
        return bool(re.match(self.interface_regex, self.text))

    @property
    def interface_name(self):
        if not self.is_interface:
            return None
        else:
            return self.re_match(self.interface_regex, group=1)

    @property
    def interface_description(self):
        if not self.is_interface:
            return None
        else:
            regex = r"description\s(.*)"
            candidates = self.re_search_children(regex=regex)
            if len(candidates) == 1:
                return candidates[0].re_search(regex=regex, group=1)
            else:
                return None

    def __str__(self):
        return "[BaseConfigLine #{} ({}): '{}']".format(self.number, self.type, self.text)

    def __repr__(self):
        return self.__str__()