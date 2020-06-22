import unittest
import pathlib
import json
from ccutils.ccparser import ConfigParser, ConfigToJson


class TestConfigToJson(unittest.TestCase):

    def test_config_to_json(self):
        self.maxDiff = 5000
        wanted_results = {
            "interface_l2_test": {"omit_empty": True}
        }
        for hostname in wanted_results.keys():
            with self.subTest(msg=hostname):
                config = ConfigParser(config=pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format(hostname)), device_type="ios")
                ctj = ConfigToJson(config=config, omit_empty=wanted_results[hostname]["omit_empty"], verbosity=5)
                # print(ctj.to_json())
                # print(ctj.to_yaml())
                result = json.loads(pathlib.Path(__file__).parent.joinpath("results/{}.json".format(hostname)).read_text())
                self.assertDictEqual(ctj.data, result)

if __name__ == '__main__':
    unittest.main()