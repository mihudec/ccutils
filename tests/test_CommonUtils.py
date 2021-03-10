import unittest
from ccutils.utils.common_utils import split_interface_name, convert_interface_name
import json

DEBUG = False
VERBOSITY = 5 if DEBUG else 3


class TestCommonUtils(unittest.TestCase):

    def test_split_interface_name(self):
        testmap = {
            "FastEthernet0/20": ["FastEthernet", "0/20"],
            "Vlan1": ["Vlan", "1"],
            "Port-channel1": ["Port-channel", "1"],
            "GigabitEthernet1/0/1.20": ["GigabitEthernet", "1/0/1.20"],
        }
        for interface, parts in testmap.items():
            with self.subTest(msg="{}".format(interface)):
                want = parts
                have = split_interface_name(interface=interface)
                self.assertEqual(want, have)

    def test_convert_interface_name(self):
        testmap = {
            "FastEthernet0/20": "Fa0/20",
            "Vlan1": "Vl1",
            "Port-channel1": "Po1",
            "GigabitEthernet1/0/1.20": "Gi1/0/1.20",
            "Port-channel10.20": "Po10.20",
        }
        for interface, parts in testmap.items():
            with self.subTest(msg="{}".format(interface)):
                want = parts
                have = convert_interface_name(interface=interface, out="short")
                self.assertEqual(want, have)

if __name__ == '__main__':
    unittest.main()