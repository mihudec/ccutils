from collections import MutableSequence
import re
import sys
from ccutils.utils.common_utils import get_logger
import json

class CiscoRange(MutableSequence):

    # TODO: Remove
    #PREFIX_REGEX = re.compile(pattern=r"^[A-z]{2,}")
    PREFIX_REGEX = re.compile(pattern=r"^[A-z\-]+(?=\d)", flags=re.MULTILINE)
    SUFFIX_REGEX = re.compile(pattern=r"\d+(?:\/\d+)*(?:\s*-\s*\d+)*")
    RANGE_REGEX = re.compile(pattern=r"\d+\s*-\s*\d+")
    # TODO: Remove
    #PREFIX_SLOT_REGEX = re.compile(pattern=r"(?P<prefix_slot>[A-z]{2,}(?:\d+/)*)(?P<number>\d+)")
    PREFIX_SLOT_REGEX = re.compile(pattern=r"(?P<prefix_slot>^[A-z\-]+(?=\d)(?:\d+/)*)(?P<number>\d+)", flags=re.MULTILINE)

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
            self.logger.error(msg="Not all items contain prefixes." )
            return False

    def split_to_list(self, data):
        _list = []
        raw_list = self.split_text(text=data)
        if self.has_prefix(data=raw_list) and not self.check_prefix(data=data):
            self.logger.error(msg="Found prefix inconsistency in given data.")
            return _list
        for item in raw_list:
            results = self.split_item(item)
            for res in results:
                if res not in _list:
                    _list.append(res)
        return _list


    def split_text(self, text):
        result = []
        if isinstance(text, list):
            return [x.strip() for x in text if isinstance(x, str) and x != ""]
        elif isinstance(text, str):
            try:
                result = [x.strip() for x in text.strip(",").split(",")]
            except Exception as e:
                self.logger.error(msg="{}".format(repr(e)))
            finally:
                return result
        else:
            self.logger.error(msg="Unexpected data type given: {}".format(type(text)))

    def split_item(self, item):
        match = re.match(pattern=self.PREFIX_REGEX, string=item)
        prefix = match.group(0) if match else ""
        self.logger.debug(msg="Prefix: '{}'".format(prefix))
        try:
            suffix = re.search(pattern=self.SUFFIX_REGEX, string=item).group(0)
        except AttributeError:
            self.logger.error("Suffix regex did not match on item: {}".format(item))
            suffix = ""
        self.logger.debug(msg="Suffix: '{}'".format(suffix))
        match = re.search(pattern=self.RANGE_REGEX, string=suffix)
        if match:
            base_suffix = suffix[:len(suffix) - len(match.group(0))]
            self.logger.debug(msg="Base Suffix: '{}'".format(base_suffix))
            start = int(match.group(0).split("-")[0].strip())
            stop = int(match.group(0).split("-")[1].strip())
            ERROR = "Given invalid range: '{}'. Start is bigger than stop!".format(item)
            assert stop >= start, ERROR
            number_range = range(start, stop+1)
            return ["{}{}{}".format(prefix, base_suffix, x) for x in number_range]
        else:
            return ["{}{}".format(prefix, suffix)]


    def sort_list(self, data):
        if self.has_prefix(data=data):
            results = []
            temp_list = []
            # Split item to list of prefixes and suffixes
            for item in data:
                temp_list.append([
                    re.search(pattern=self.PREFIX_REGEX, string=item).group(0),
                    re.search(pattern=self.SUFFIX_REGEX, string=item).group(0).split("/")
                ])
            self.logger.debug(msg="TempList: {}".format(temp_list))
            suffix_lengths = []
            for item in temp_list:
                if len(item[1]) not in suffix_lengths:
                    suffix_lengths.append(len(item[1]))
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
                        number += int(value) * 100**index
                    item.append(number)
                sorted_items = list(items)
                sorted_items.sort(key=lambda x: x[2])
                # Remove numeric value
                for item in sorted_items:
                    del item[2]
                    results.append("{}{}".format(item[0], "/".join(item[1])))
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