import unittest
import pathlib
import json
from ccutils.ccparser import BaseConfigParser

DEBUG = False
VERBOSITY = 5 if DEBUG else 3


class TestBaseConfigParser(unittest.TestCase):
    test_file_path = pathlib.Path(__file__).parent.joinpath("resources/interface_service_instances_test.txt")
    config = BaseConfigParser(config=test_file_path, verbosity=VERBOSITY)

    def test_interface_parent(self):
        wanted_results = {
            0: None,
            1: 0,
            2: 0,
            3: 1,
            8: None,
            13: 9
        }
        for test in wanted_results.keys():
            with self.subTest(msg=test):
                config_line = [x for x in self.config.lines if x.number == test][0]
                parent = config_line
                self.assertEqual(parent.number, test)


if __name__ == '__main__':
    unittest.main()