import unittest
import pathlib
import json
from ccutils.ccparser import BaseConfigParser, ConfigToJson


class TestBaseConfigParser(unittest.TestCase):

    def test_performance(self):
        test_path = pathlib.Path(r"/path/to/test_configs")
        config_files = [x for x in test_path.glob("**/*.conf")]
        for config_file in config_files:

            with self.subTest(msg=config_file.stem):
                config = BaseConfigParser(config=config_file, verbosity=4)
                ctj = ConfigToJson(config=config, omit_empty=True, verbosity=3)
                #ctj.jprint(ctj.data)
                self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()