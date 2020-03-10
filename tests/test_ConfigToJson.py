import unittest
import pathlib
import json
from ccutils.ccparser import BaseConfigParser, ConfigToJson


class TestConfigToJson(unittest.TestCase):
    test_file_path = pathlib.Path("./resources/interface_l2_test.txt")
    config = BaseConfigParser(config=test_file_path, verbosity=1)

    def test_config_to_json(self):
        wanted_results = {
            "interface_l2_test": {"omit_empty": True}
        }
        for hostname in wanted_results.keys():
            with self.subTest(msg=hostname):
                config = BaseConfigParser(config=pathlib.Path("./resources/{}.txt".format(hostname)))
                ctj = ConfigToJson(config=config, omit_empty=wanted_results[hostname]["omit_empty"], verbosity=3)
                ctj.jprint(ctj.data)
                result = json.loads(pathlib.Path("./results/{}.json".format(hostname)).read_text())
                self.assertEqual(ctj.data, result)

if __name__ == '__main__':
    unittest.main()