import unittest
import pathlib
import json
from ccutils.ccparser import BaseConfigParser, ConfigToJson


class TestBaseConfigParser(unittest.TestCase):

    def test_Vlans(self):
        wanted_results = {
            "vlans_test": None
        }
        for test in wanted_results.keys():
            with self.subTest(msg=test):
                config = BaseConfigParser(config=pathlib.Path(__file__).joinpath("../resources/{}.txt".format(test)))
                print(config.lines)
                result = json.loads(pathlib.Path(__file__).joinpath("../results/{}.json".format(test)).read_text())
                print(config.vlans)
                print(result)
                self.assertDictEqual(config.vlans, result)

if __name__ == '__main__':
    unittest.main()