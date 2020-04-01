import unittest
import pathlib
import json
from ccutils.utils import CiscoRange


class TestCiscoRange(unittest.TestCase):

    def test_uncompressed(self):
        tests = {
            "Test1": {
                "source": "1,3,4-6,8,11 - 20, 9",
                "result": ["1", "3", "4", "5", "6", "8", "9", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]
            },
            "Test2": {
                "source": "Fa0, Fa0/3-6, Fa0/1-2, Fa2/1-2 Fa2/0/10-11, Fa1/0/3-4",
                "result": ["Fa0", "Fa0/1", "Fa0/2", "Fa0/3", "Fa0/4", "Fa0/5", "Fa0/6", "Fa2/1", "Fa2/2", "Fa1/0/3", "Fa1/0/4"]
            },
            "Test3": {
                "source": "1,2,10,15,19,21,22,24,27,30,31,55,58,66,100-102,",
                "result": ["1", "2", "10", "15", "19", "21", "22", "24", "27", "30", "31", "55", "58", "66", "100", "101", "102"]
            },
            "Test4": {
                "source": "Port-channel1-2",
                "result": ["Port-channel1", "Port-channel2"]
            }
        }

        for test in tests.keys():
            with self.subTest(msg=test):
                cr = CiscoRange(tests[test]["source"])
                print(list(cr))
                self.assertSequenceEqual(list(cr), tests[test]["result"])

    def test_compressed(self):
        tests = {
            "Test1": {
                "source": "1,3,4-6,8,11 - 20, 9",
                "result": ["1", "3-6", "8", "9", "11-20"]
            },
            "Test2": {
                "source": "Fa0, Fa0/3-6, Fa0/1-2, Fa2/1-2 Fa2/0/10-11, Fa1/0/3-4",
                "result": ["Fa0", "Fa0/1-6", "Fa2/1-2", "Fa1/0/3-4"]
            },
        }

        for test in tests.keys():
            with self.subTest(msg=test):
                cr = CiscoRange(tests[test]["source"])
                print(cr.compressed_list)
                self.assertEqual(cr.compressed_list, tests[test]["result"])

if __name__ == '__main__':
    unittest.main()