import unittest
import pathlib
import json
from ccutils.utils import JsonValidator

DEBUG = True
VERBOSITY = 5 if DEBUG else 3


class TestJsonSchemaValidity(unittest.TestCase):
    validator = None

    def test_instantiate_validator(self):
        result = None
        try:
            self.validator = JsonValidator(verbosity=VERBOSITY)
            self.validator.test_schema_store()
            result = True
        except Exception as e:
            self.fail("Exception: {}".format(repr(e)))
            result = False
        self.assertTrue(result)

    def test_validate_interface(self):
        self.test_instantiate_validator()
        tests = {
            "flags_l2": {"result": True, "schema": "ios_interface", "data": {"flags": ["l3"]}},
            "flags_l3": {"result": True, "schema": "ios_interface", "data": {"flags": ["l3"]}},
            "flags_l2_l3": {"result": False, "schema": "ios_interface", "data": {"flags": ["l2", "l3"]}},
            "flags_l2_l3Present": {"result": False, "schema": "ios_interface", "data": {"flags": ["l2"], "l3": {}}}
        }
        for test in tests.keys():
            with self.subTest(msg=test):
                result = self.validator.validate(data=tests[test]["data"], schema_id=tests[test]["schema"])
                self.assertTrue(result is tests[test]["result"])




if __name__ == '__main__':
    unittest.main()