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
                config = BaseConfigParser(config=pathlib.Path(__file__).parent.joinpath("resources/{}.txt".format(test)))
                # print(config.lines)
                result = json.loads(pathlib.Path(__file__).parent.joinpath("results/{}.json".format(test)).read_text())
                # print(config.vlans)
                # print(result)
                self.assertDictEqual(config.vlans, result)


    def test_section_by_parents(self):

        text1 = """
interface GigabitEthernet1/0/1
 switchport mode trunk
!
interface GigabitEthernet1/0/2
 switchport mode access
 switchport access vlan 10
!
"""
        text2 = """
interface GigabitEthernet1/0/1
 switchport mode trunk
!
interface GigabitEthernet1/0/2
 switchport mode access
 switchport access vlan 10
!
interface GigabitEthernet1/0/3
!
"""
        config1 = BaseConfigParser(config=text1, verbosity=5)
        result = config1.get_section_by_parents(["interface GigabitEthernet1/0/2"])
        print(result)





if __name__ == '__main__':
    unittest.main()