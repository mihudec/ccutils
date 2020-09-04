import unittest
import pathlib
import json
from ccutils.ccparser import ConfigParser
from ccutils.utils.common_utils import jprint


class TestCiscoIosParser(unittest.TestCase):

    @staticmethod
    def get_config(test_file_name):
        test_file_path = pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format(test_file_name))
        return ConfigParser(config=test_file_path, device_type="ios")

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

