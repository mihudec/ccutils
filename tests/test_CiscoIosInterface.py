import unittest
import pathlib
import json
from ccutils.ccparser import ConfigParser
from ccutils.utils.common_utils import jprint

DEBUG = False
VERBOSITY = 5 if DEBUG else 3


class TestL3Interface(unittest.TestCase):
    test_file_base = "cisco_ios_interface_l3_tests"
    test_file_path = pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format(test_file_base))
    result_file_path = pathlib.Path(__file__).parent.joinpath("results/{}.json".format(test_file_base))
    config = ConfigParser(config=test_file_path, device_type="ios")
    config.minimal_results = True
    results = json.loads(result_file_path.read_text())

    def test_ipv4_addresses(self):
        tested_interfaces = ["Vlan100", "Vlan101", "Vlan102"]

        for interface in tested_interfaces:
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                want = self.results["interfaces"][interface]["ipv4"]["addresses"]
                have = interface_line.ipv4_addresses
                self.assertEqual(want, have)

    def test_isis(self):
        tested_interfaces = ["TenGigabitEthernet0/0/8"]

        for interface in tested_interfaces:
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                want = self.results["interfaces"][interface]["isis"]
                have = interface_line.isis
                self.assertEqual(want, have)

    def test_bdf(self):
        tested_interfaces = ["TenGigabitEthernet0/0/8"]

        for interface in tested_interfaces:
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                want = self.results["interfaces"][interface]["bfd"]
                have = interface_line.bfd
                self.assertEqual(want, have)

    def test_standby(self):
        tested_interfaces = ["Vlan100", "Vlan101", "Vlan102"]

        for interface in tested_interfaces:
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                want = self.results["interfaces"][interface]["standby"]
                have = interface_line.standby
                self.assertEqual(want, have)


class TestL2Interface(unittest.TestCase):
    test_file_base = "cisco_ios_interface_l2_tests"
    test_file_path = pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format(test_file_base))
    result_file_path = pathlib.Path(__file__).parent.joinpath("results/{}.json".format(test_file_base))
    config = ConfigParser(config=test_file_path, device_type="ios", verbosity=3)
    config.minimal_results = True
    results = json.loads(result_file_path.read_text())

    def test_dhcp_snooping(self):
        tested_interfaces = ["TenGigabitEthernet1/0/1"]
        for interface in tested_interfaces:
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                want = self.results["interfaces"][interface]["dhcp_snooping"]
                have = interface_line.dhcp_snooping
                self.assertEqual(want, have)

