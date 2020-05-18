from collections import MutableSequence
import re
import sys
from ccutils.utils.common_utils import get_logger
import json

class CiscoRange(MutableSequence):

    # TODO: Remove
    #PREFIX_REGEX = re.compile(pattern=r"^[A-z]{2,}")
    PREFIX_REGEX = re.compile(pattern=r"^[A-z\-]+(?=\d)", flags=re.MULTILINE)
    # SUFFIX_REGEX = re.compile(pattern=r"\d+(?:\/\d+)*(?:\s*-\s*\d+)*")
    SUFFIX_REGEX = re.compile(pattern=r"\d.*?$")
    RANGE_REGEX = re.compile(pattern=r"\d+\s*-\s*\d+")
    SUBINT_REGEX = re.compile(pattern=r"\.(?P<number>\d+)$")
    # SUFFIX_REGEX = re.compile(pattern=r"\d+(?:(?:-\d+)|(?:\/\d+)+(?:(?:\s*-\s*\d+)|(?:\.\d+(?:\s*-\s*\d+)))|(?:\.\d+))?$")
    # SUFFIX_REGEX = re.compile(pattern=r"(?P<prefix_slot>(?:\d+\/)*)(?:(?:\d+)|(?P<range>\d+\s*-\s*\d+)|(?:\d+\.(?P<subint>\d+)))$")

    # TODO: Remove
    #PREFIX_SLOT_REGEX = re.compile(pattern=r"(?P<prefix_slot>[A-z]{2,}(?:\d+/)*)(?P<number>\d+)")
    PREFIX_SLOT_REGEX = re.compile(pattern=r"(?P<prefix_slot>^[A-z\-]+(?=\d)(?:\d+/)*)(?P<number>\d+)", flags=re.MULTILINE)
    # PREFIX_SLOT_REGEX = re.compile(pattern=r"(?P<prefix_slot>^[A-z\-]+(?=\d)(?:\d+\/)*(?:\d+\.)?)(?P<number>\d+)", flags=re.MULTILINE)


    def __init__(self, text, verbosity=3):
        super(CiscoRange, self).__init__()
        self.logger = get_logger(name="CiscoRange", verbosity=verbosity)
        self.text = text
        self._list = self.sort_list(data=self.split_to_list(data=self.text))
        self.compressed_list = self.compress_list(data=self._list)

    def __delitem__(self, index):
        del self._list[index]
    
    def __getitem__(self, index):
        return self._list[index]
    
    def __len__(self):
        return len(self._list)
    
    def __setitem__(self, index, value):
        self._list[index] = value

    def __eq__(self, other):
        return self._list == other._list

    def __sub__(self, other):
        return self.sort_list(list(set(self._list) - set(other._list)))

    def __or__(self, other):
        return self.sort_list(list(set(self._list) | set(other._list)))

    def __xor__(self, other):
        return self.sort_list(list(set(self._list) ^ set(other._list)))

    def insert(self, index, value):
        self._list.insert(index, value)

    def __repr__(self):
        return "<CiscoRange: {}>".format(self.compressed_list)

    def add(self, data):
        data = self.split_to_list(data=data)
        if self.has_prefix(data=self._list):
            if not self.has_prefix(data=data):
                raise ValueError("Cannot merge prefixed and un-prefixed values!")
        else:
            if self.has_prefix(data=data):
                raise ValueError("Cannot merge prefixed and un-prefixed values!")
        _set = set(self._list)
        _set.add(tuple(data))
        self._list = self.sort_list(list(_set))
        self.compressed_list = self.compress_list(data=self._list)
    
    def remove(self, data):
        data = self.split_to_list(data=data)
        if self.has_prefix(data=self._list):
            if not self.has_prefix(data=data):
                raise ValueError("Cannot merge prefixed and un-prefixed values!")
        else:
            if self.has_prefix(data=data):
                raise ValueError("Cannot merge prefixed and un-prefixed values!")
        for element in data:
            try:
                self._list.remove(element)
            except Exception as e:
                pass
        self._list = self.sort_list(self._list)
        self.compressed_list = self.compress_list(data=self._list)


    def has_prefix(self, data):
        if isinstance(data, str):
            data = self.split_text(text=data)
        elif isinstance(data, list):
            pass
        else:
            self.logger.error(msg="Unexpected data type given: {}".format(type(data)))
            data = []
        # Check if at least one item contains prefix
        return bool(len(list(filter(lambda x: re.match(pattern=self.PREFIX_REGEX, string=x), data))))

    def check_prefix(self, data):
        if isinstance(data, str):
            data = self.split_text(text=data)
        elif isinstance(data, list):
            pass
        else:
            self.logger.error(msg="Unexpected data type given: {}".format(type(data)))
            data = []
        # Check if all items have prefix
        if len(data) == len(list(filter(lambda x: re.match(pattern=self.PREFIX_REGEX, string=x), data))):
            return True
        else:
            self.logger.error(msg="Not all items contain prefixes.")
            return False

    def split_to_list(self, data):
        _list = []
        raw_list = self.split_text(text=data)
        self.logger.debug("Raw List: {}".format(raw_list))
        if self.has_prefix(data=raw_list) and not self.check_prefix(data=data):
            self.logger.error(msg="Found prefix inconsistency in given data.")
            self.logger.debug("Returning '{}' for data: '{}'".format(_list, data))
            return _list
        for item in raw_list:
            results = self.split_item(item)
            for res in results:
                if res not in _list:
                    _list.append(res)
        self.logger.debug("Returning '{}' for data: '{}'".format(_list, data))
        return _list


    def split_text(self, text):
        result = []
        if isinstance(text, list):
            for item in text:
                if isinstance(item, int):
                    # TODO: Fix this ugliness
                    result.append(str(item))
                elif isinstance(item, str):
                    if item == "":
                        continue
                    else:
                        for subitem in [x.strip() for x in item.strip(",").split(",")]:
                            result.append(subitem)
            self.logger.debug("Text Instance: List - Returning {} for text: '{}'".format(result, text))
            return result
        elif isinstance(text, str):
            try:
                result = [x.strip() for x in text.strip(",").split(",")]
            except Exception as e:
                self.logger.error(msg="{}".format(repr(e)))
            finally:
                self.logger.debug("Text Instance: String - Returning {} for text: '{}'".format(result, text))
                return result
        else:
            self.logger.error(msg="Unexpected data type given: {}".format(type(text)))

    def split_item(self, item):
        self.logger.debug("Working on Item: {}".format(item))
        prefix_search = re.match(pattern=self.PREFIX_REGEX, string=item)
        prefix = prefix_search.group(0) if prefix_search else ""
        self.logger.debug(msg="Prefix: '{}'".format(prefix))
        suffix_search = self.SUFFIX_REGEX.search(string=item)
        if suffix_search:
            suffix = suffix_search.group(0)
            subint = self.SUBINT_REGEX.search(string=suffix).group("number") if self.SUBINT_REGEX.search(string=suffix) else None
            int_range = self.RANGE_REGEX.search(string=suffix).group(0) if self.RANGE_REGEX.search(string=suffix) else None
            if subint:
                # Cut off subinterface from suffix, +1 for dot
                suffix = suffix[:-(len(subint)+1)]
            self.logger.debug("Prefix: {} Suffix: {} IntRange: {} SubInt: {}".format(prefix, suffix, int_range, subint))

        else:
            self.logger.error("Suffix regex did not match on item: {}".format(item))
            suffix = ""
        self.logger.debug(msg="Suffix: '{}'".format(suffix))
        # Range and subinterface is not supported
        if int_range and subint:
            self.logger.error("Subinterfaces cannot be combined with ranges. Item: {}".format(item))
            raise NotImplementedError("Subinterfaces cannot be combined with ranges. Item: {}".format(item))
        elif int_range:
            # Range, no Subinterface
            base_suffix = suffix[:len(suffix) - len(int_range)]
            self.logger.debug(msg="Base Suffix: '{}'".format(base_suffix))
            start = int(int_range.split("-")[0].strip())
            stop = int(int_range.split("-")[1].strip())
            ERROR = "Given invalid range: '{}'. Start is bigger than stop!".format(item)
            assert stop >= start, ERROR
            number_range = range(start, stop+1)
            result = ["{}{}{}".format(prefix, base_suffix, x) for x in number_range]
            self.logger.debug("Result: {}".format(result))
            return result
        else:
            # Subinterface, no Range
            if subint:
                result = ["{}{}.{}".format(prefix, suffix, subint)]
                self.logger.debug("Result: {}".format(result))
                return result
            # No Subinterface, no Range
            else:
                result = ["{}{}".format(prefix, suffix)]
                self.logger.debug("Result: {}".format(result))
                return result

    def sort_list(self, data):
        if self.has_prefix(data=data):
            results = []
            temp_list = []
            # Split item to list of prefixes and suffixes
            for item in data:
                prefix = self.PREFIX_REGEX.search(string=item).group(0)
                subint_search = self.SUBINT_REGEX.search(string=item)
                subint = subint_search.group("number") if subint_search else None
                suffix_list = []
                if subint:
                    suffix_list = [int(x) for x in self.SUFFIX_REGEX.search(string=item).group(0)[:-(len(subint)+1)].split("/")]
                else:
                    suffix_list = [int(x) for x in self.SUFFIX_REGEX.search(string=item).group(0).split("/")]
                temp_list.append([
                    prefix,
                    suffix_list,
                    int(subint) if subint is not None else None
                ])
            self.logger.debug(msg="TempList: {}".format(temp_list))
            suffix_lengths = list(set([len(x[1]) for x in temp_list]))
            suffix_lengths.sort()
            # Get items with same suffix length
            for suffix_length in suffix_lengths:
                items = list(filter(lambda x: len(x[1]) == suffix_length, temp_list))
                self.logger.debug(msg="SuffixLength: {}: {}".format(suffix_length, items))
                # Assign numeric values to items based on suffixes
                for item in items:
                    number = 0
                    reverse_suffix = list(item[1])
                    reverse_suffix.reverse()
                    for index, value in enumerate(reverse_suffix):
                        number += int(100*value) * 100**(index+1)
                    if item[2] is not None:
                        number += item[2]
                    item.append(number)
                    self.logger.debug("Prefix: {} SuffixList: {}, SubInt: {}, Value: {} ".format(*item))
                sorted_items = list(items)
                sorted_items.sort(key=lambda x: x[3])
                # Remove numeric value
                for item in sorted_items:
                    del item[3]
                    if item[2] is None:
                        results.append("{}{}".format(item[0], "/".join([str(x) for x in item[1]])))
                    else:
                        results.append("{}{}.{}".format(item[0], "/".join([str(x) for x in item[1]]), str(item[2])))
                self.logger.debug(msg="SortedItems: {}".format(sorted_items))

            self.logger.debug(msg="Results: {}".format(results))
            return results        
        else:
            temp_list = [int(x) for x in data]
            temp_list.sort()
            
            return ["{}".format(x) for x in temp_list]

    def compress_list(self, data):
        results = []
        prefix = ""
        entry = []
        for index, item in enumerate(data):
            current_prefix = ""
            match = re.match(pattern=self.PREFIX_SLOT_REGEX, string=item)
            if match:
                current_prefix = match.group("prefix_slot")
                subint_search = self.SUBINT_REGEX.search(string=item)
                subint = subint_search.group("number") if subint_search else None
                if subint is not None:
                    results.append(item)
                    continue
                item = int(match.group("number"))
            else:
                item = int(item)
            if not len(entry):
                self.logger.debug(msg="BEFORE: CurrentPrefix: '{}'; CurrentItem: '{}'; CurrentEntry: '{}'; Prefix: '{}'".format(current_prefix, item, entry, prefix))
                entry.append(item)
                prefix = current_prefix
            elif len(entry) == 1:
                self.logger.debug(msg="BEFORE: CurrentPrefix: '{}'; CurrentItem: '{}'; CurrentEntry: '{}'; Prefix: '{}'".format(current_prefix, item, entry, prefix))
                if current_prefix == prefix:
                    if entry[0] == item-1:
                        entry.append(item)
                    else:
                        results.append("{}{}".format(prefix, *entry))
                        entry = [item]
                else:
                    results.append("{}{}".format(prefix, *entry))
                    entry = [item]
                    prefix = current_prefix
            elif len(entry) == 2:
                self.logger.debug(msg="BEFORE: CurrentPrefix: '{}'; CurrentItem: '{}'; CurrentEntry: '{}'; Prefix: '{}'".format(current_prefix, item, entry, prefix))
                if current_prefix == prefix:
                    if entry[1] == item-1:
                        # Increase entry[1]
                        entry[1] += 1
                    else:
                        # Cisco VLAN range uses compression (eg. "1-3") only when the difference between start and stop is HIGHER than 1
                        # If difference is EQUAL to 1, each number is separate (eg. "1,2")
                        #Do this only for entries without prefix
                        if (entry[1] == entry[0] + 1) and prefix == "":
                            results.append("{}".format(entry[0]))
                            results.append("{}".format(entry[1]))
                        else:
                            results.append("{}{}-{}".format(prefix, *entry))
                        entry = [item]
                else:
                    results.append("{}{}-{}".format(prefix, *entry))
                    entry = [item]
                    prefix = current_prefix
        
        if len(entry) == 1:
            results.append("{}{}".format(prefix, *entry))
        elif len(entry) == 2:
            if (entry[1] == entry[0] + 1) and prefix == "":
                results.append("{}".format(entry[0]))
                results.append("{}".format(entry[1]))
            else:
                results.append("{}{}-{}".format(prefix, *entry))
        
        return results

    def to_string(self):
        return ",".join(self.compressed_list)



def main():
    text = "1,3,4-6,8,11-20, 9"
    text2 = "Fa0, Fa0/3-6, Fa0/1-2, Fa2/1-2 Fa2/0/10-11, Fa1/0/3-4"
    text4 = "Fa0, Fa0/3-6, Fa0/1-2, Fa2/3-4 Fa2/0/10-11, Fa1/0/3-4"
    text3 = "1,2,10,15,19,21,22,24,27,30,31,55,58,66,100-102,"
    crange = CiscoRange(text=text)
    
    crange.add("22-24")
    print(crange)


if __name__ == "__main__":
     main()