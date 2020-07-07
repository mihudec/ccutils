import unittest
import pathlib
from ccutils.ccparser import ConfigParser, CiscoIosParser
from ccutils.utils.common_utils import jprint
import json


class TestConfigParser01(unittest.TestCase):

    config_path = pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format("global_config_01"))
    results_path = pathlib.Path(__file__).parent.joinpath("results/{}.json".format("global_config_01"))
    results = json.loads(results_path.read_text())

    def test_instance(self):
        tests = {
            "ios": CiscoIosParser
        }
        for test, instance in tests.items():
            with self.subTest(msg=test):
                parser = ConfigParser(config=self.config_path, device_type=test)
                self.assertIsInstance(parser, instance)

    def test_name_servers(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["name_servers"]
        have = parser.name_servers
        self.assertEqual(want, have)

    def test_ntp_servers(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["ntp_servers"]
        have = parser.ntp_servers
        self.assertEqual(want, have)

    def test_ntp_peers(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["ntp_peers"]
        have = parser.ntp_peers
        self.assertEqual(want, have)

    def test_ntp_access_groups(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["ntp_access_groups"]
        have = parser.ntp_access_groups
        self.assertEqual(want, have)

    def test_ntp_authentication_keys(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["ntp_authentication_keys"]
        have = parser.ntp_authentication_keys
        self.assertEqual(want, have)

    def test_ntp_trusted_keys(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["ntp_trusted_keys"]
        have = parser.ntp_trusted_keys
        self.assertEqual(want, have)

    def test_ntp_global_params(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["ntp_global"]
        have = parser.ntp_global_params
        self.assertEqual(want, have)

    def test_ntp(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = {
            "source": "Loopback1000",
            "authenticate": True,
            "servers": self.results["ntp_servers"],
            "peers": self.results["ntp_peers"],
            "access_groups": self.results["ntp_access_groups"],
            "authentication_keys": self.results["ntp_authentication_keys"],
            "trusted_keys": self.results["ntp_trusted_keys"]
        }
        have = parser.ntp
        self.assertEqual(want, have)

    def test_logging_servers(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["logging_servers"]
        have = parser.logging_servers
        self.assertEqual(want, have)


    def test_logging_global_params(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["logging_global"]
        have = parser.logging_global_params
        self.assertEqual(want, have)

    def test_logging(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = {
            "source": "Loopback0",
            "servers": self.results["logging_servers"],
        }
        have = parser.logging
        self.assertEqual(want, have)

    def test_tacacs_servers(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["tacacs_servers"]
        have = parser.tacacs_servers
        jprint(have)
        self.assertEqual(want, have)

    def test_radius_servers(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["radius_servers"]
        have = parser.radius_servers
        jprint(have)
        self.assertEqual(want, have)

    def test_tacacs_groups(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["tacacs_groups"]
        have = parser.tacacs_groups
        jprint(have)
        self.assertEqual(want, have)

    def test_radius_groups(self):
        parser = ConfigParser(config=self.config_path, device_type="ios")
        parser.minimal_results = True
        want = self.results["radius_groups"]
        have = parser.radius_groups
        jprint(have)
        self.assertEqual(want, have)

if __name__ == '__main__':
    unittest.main()