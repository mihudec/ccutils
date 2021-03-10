import unittest
import pathlib
import json
from ccutils.ccparser import ConfigParser
from ccutils.utils.common_utils import jprint

DEBUG = False
VERBOSITY = 5 if DEBUG else 3


class TestCiscoIosParser(unittest.TestCase):

    @staticmethod
    def get_config(test_file_name):
        test_file_path = pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format(test_file_name))
        return ConfigParser(config=test_file_path, device_type="ios", verbosity=VERBOSITY)

    @staticmethod
    def get_results(results_file_name):
        result_file_path = pathlib.Path(__file__).parent.joinpath("results/{}.json".format(results_file_name))
        return json.loads(result_file_path.read_text())

    def test_vrfs(self):
        test_file_base = "cisco_ios_vrf_definition"
        with self.subTest(msg=test_file_base):
            config = self.get_config(test_file_name=test_file_base)
            want = self.get_results(results_file_name=test_file_base)
            have = config.vrfs
            jprint(have)

            self.assertEqual(want, have)

    def test_all_ipv4_physical_addresses(self):
        test_file_base = "cisco_ios_L3_interfaces_address_test"
        with self.subTest(msg=test_file_base):
            config = self.get_config(test_file_name=test_file_base)
            want = self.get_results(results_file_name=test_file_base)["all_ipv4_physical_addresses"]
            have = config.all_ipv4_physical_addresses
            jprint(have)

            self.assertEqual(want, have)

    def test_vrf_ipv4_physical_addresses(self):
        test_file_base = "cisco_ios_L3_interfaces_address_test"
        with self.subTest(msg=test_file_base):
            config = self.get_config(test_file_name=test_file_base)
            want = self.get_results(results_file_name=test_file_base)["vrf_ipv4_physical_addresses"]
            have = config.vrf_ipv4_physical_addresses(vrf="TEST")
            jprint(have)

            self.assertEqual(want, have)

    def test_all_ipv4_standby_addresses(self):
        test_file_base = "cisco_ios_L3_interfaces_address_test"
        with self.subTest(msg=test_file_base):
            config = self.get_config(test_file_name=test_file_base)
            want = self.get_results(results_file_name=test_file_base)["all_ipv4_standby_addresses"]
            have = config.all_ipv4_standby_addresses
            jprint(have)

            self.assertEqual(want, have)

    def test_vrf_ipv4_standby_addresses(self):
        test_file_base = "cisco_ios_L3_interfaces_address_test"
        with self.subTest(msg=test_file_base):
            config = self.get_config(test_file_name=test_file_base)
            want = self.get_results(results_file_name=test_file_base)["vrf_ipv4_standby_addresses"]
            have = config.vrf_ipv4_standby_addresses(vrf="TEST")
            jprint(have)

            self.assertEqual(want, have)

    def test_vlan_groups(self):
        test_file_base = "cisco_ios_vlan_groups_tests"
        with self.subTest(msg=test_file_base):
            config = self.get_config(test_file_name=test_file_base)
            want = self.get_results(results_file_name=test_file_base)["vlan_groups"]
            have = config.vlan_groups
            jprint(have)

            self.assertEqual(want, have)


