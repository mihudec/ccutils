import unittest
import pathlib
import json
from ccutils.ccparser import BaseConfigParser


class TestL2Interface(unittest.TestCase):
    test_file_path = pathlib.Path(__file__).joinpath("../resources/interface_l2_test.txt")
    config = BaseConfigParser(config=test_file_path)

    def test_switchport_mode(self):
        wanted_results = {
            "Ethernet0/0": "trunk",
            "Ethernet0/1": "access"
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.switchport_mode
                self.assertEqual(wanted_results[interface], result)

    def test_switchport_access_vlan(self):
        wanted_results = {
            "Ethernet0/1": 10
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.access_vlan
                self.assertEqual(wanted_results[interface], result)

    def test_switchport_vioce_vlan(self):
        wanted_results = {
            "Ethernet0/1": 20
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.voice_vlan
                self.assertEqual(wanted_results[interface], result)

    def test_switchport_trunk_encapsulation(self):
        wanted_results = {
            "Ethernet0/0": "dot1q"
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.trunk_encapsulation
                self.assertEqual(wanted_results[interface], result)

    def test_switchport_native_vlan(self):
        wanted_results = {
            "Ethernet0/0": 10
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.native_vlan
                self.assertEqual(wanted_results[interface], result)

    def test_storm_control(self):
        wanted_results = json.loads(pathlib.Path(__file__).joinpath("../results/test_storm_control.json").read_text())
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.storm_control
                self.assertEqual(wanted_results[interface], result)


class TestL3Interface(unittest.TestCase):
    test_file_path = pathlib.Path(__file__).joinpath("../resources/interface_l3_test.txt")
    config = BaseConfigParser(config=test_file_path)

    def test_encapsulation(self):
        wanted_results = {
            "Port-channel1.2500": {
                "type": "dot1q",
                "tag": 2500,
                "native": False
            },
            "GigabitEthernet1/0/1.99": {
                "type": "dot1q",
                "tag": 99,
                "native": True
            },
            "Loopback0": None
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.encapsulation
                self.assertEqual(wanted_results[interface], result)

    def test_ospf(self):
        wanted_results = {
            "Port-channel1.2500": {
                "process_id": None,
                "area": None,
                "network_type": "point-to-point",
                "priority": 200
            },
            "GigabitEthernet1/0/1.99": {
                "process_id": 1,
                "area": 0,
                "network_type": None,
                "priority": None
            },
            "Loopback0": None
        }
        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.ospf
                self.assertEqual(wanted_results[interface], result)

class TestTunnelInterface(unittest.TestCase):
    test_file_path = pathlib.Path(__file__).joinpath("../resources/interface_tunnel_test.txt")
    config = BaseConfigParser(config=test_file_path)

    def test_interface_tunnel_properties_1(self):
        wanted_results = {
            "Tunnel0": {
                "source": "Loopback0",
                "destination": "1.2.3.4",
                "vrf": "PROVIDER",
                "mode": "ipsec ipv4",
                "ipsec_profile": "IPSEC-PROFILE"
            },
            "Tunnel1": {
                "source": None,
                "destination": None,
                "vrf": None,
                "mode": None,
                "ipsec_profile": None
            }
        }

        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.tunnel_properties
                self.assertEqual(wanted_results[interface], result)

    def test_tcp_mss(self):
        wanted_results = {
            "Tunnel0": 1360,
            "Tunnel1": None
        }

        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.tcp_mss
                self.assertEqual(wanted_results[interface], result)

    def test_ip_mtu(self):
        wanted_results = {
            "Tunnel0": 1400,
            "Tunnel1": None
        }

        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.ip_mtu
                self.assertEqual(wanted_results[interface], result)

    def test_keepalive(self):
        wanted_results = {
            "Tunnel0": {
                "period": 1,
                "retries": 3
            },
            "Tunnel1": None
        }

        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.keepalive
                self.assertEqual(wanted_results[interface], result)


class TestServiceInstances(unittest.TestCase):
    test_file_path = pathlib.Path(__file__).joinpath("../resources/interface_service_instances_test.txt")
    config = BaseConfigParser(config=test_file_path)

    def test_interface_service_instances_1(self):
        wanted_results = {
            "GigabitEthernet0/0": {
                101: {
                    "type": "ethernet",
                    "description": "SI 101 TestDescription",
                    "encapsulation": {
                        "type": "dot1q",
                        "tag": 101
                    },
                    "service_policy": {
                        "input": "SomeInputPolicy",
                        "output": None
                    }
                }
            },
            "GigabitEthernet0/1": {
                10: {
                    "type": "ethernet",
                    "description": "SI 10 TestDescription",
                    "encapsulation": "untagged",
                    "bridge_domain": 10
                }
            }
        }

        for interface in wanted_results.keys():
            with self.subTest(msg=interface):
                interface_line = [x for x in self.config.interface_lines if x.name == interface][0]
                result = interface_line.service_instances
                self.assertEqual(wanted_results[interface], result)

if __name__ == '__main__':
    unittest.main()