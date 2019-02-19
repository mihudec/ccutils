from ccutils.ccparser import BaseConfigParser, BaseConfigLine
from ccutils.utils.common_utils import get_logger
import re
import json
import pathlib

class ConfigToJson:
    def __init__(self, config, verbosity=1):
        self.config = config
        self.logger = get_logger(name="CTJ", verbosity=verbosity)
        self.data = {
            "interfaces": {}
        }

    def parse_interfaces(self):
        interface_lines = list(filter(lambda x: "interface" in x.type, self.config.config_lines_obj))
        self.logger.debug(msg="Loaded {} interface lines.".format(len(interface_lines)))
        for interface in interface_lines:
            interface_name = interface.interface_name
            port_mode = interface.port_mode

            self.data["interfaces"][interface_name] = {"flags": [port_mode], "description": interface.interface_description, "unprocessed_lines": interface.get_unprocessed(return_type="text")}
            # Get Shutdown State
            self.data["interfaces"][interface_name]["shutdown"] = interface.shutdown
            # Get CDP
            self.data["interfaces"][interface_name]["cdp"] = interface.cdp
            # Get Logging events
            self.data["interfaces"][interface_name]["logging_events"] = interface.logging_events

            

            if port_mode == "l3":
                # Get IP addresses
                self.data["interfaces"][interface_name]["l3"] = {}
                ip_addresses = interface.ip_addresses
                if len(ip_addresses):
                    self.data["interfaces"][interface_name]["l3"]["ip_addresses"] = ip_addresses
                else:
                    self.data["interfaces"][interface_name]["l3"]["ip_addresses"] = []
                # Get VRF
                self.data["interfaces"][interface_name]["l3"]["vrf"] = interface.vrf
                # Get OSPF Priority
                self.data["interfaces"][interface_name]["l3"]["ospf_priority"] = interface.ospf_priority
                # Get standby
                self.data["interfaces"][interface_name]["l3"]["standby"] = interface.standby
                # Get Helper Address
                self.data["interfaces"][interface_name]["l3"]["helper_addresses"] = interface.helper_address
            elif port_mode == "l2":
                self.data["interfaces"][interface_name]["l2"] = {}
                # Get Native VLAN
                self.data["interfaces"][interface_name]["l2"]["native_vlan"] = interface.native_vlan
                # Get Trunk Encapsulation
                self.data["interfaces"][interface_name]["l2"]["trunk_encapsulation"] = interface.trunk_encapsulation
                # Get Switchport Mode
                self.data["interfaces"][interface_name]["l2"]["mode"] = interface.switchport_mode
                # Get Trunk Allowed VLANs
                self.data["interfaces"][interface_name]["l2"]["allowed_vlans"] = interface.trunk_allowed_vlans
                # Get Access VLAN
                self.data["interfaces"][interface_name]["l2"]["access_vlan"] = interface.access_vlan
                # Get Voice VLAN
                self.data["interfaces"][interface_name]["l2"]["voice_vlan"] = interface.voice_vlan

    def parse_common(self):
        # Get Domain name
        self.data["domain_name"] = self.config.domain_name
        # Get Name-Servers
        self.data["name_servers"] = self.config.name_servers
        self.data["cdp"] = self.config.cdp
        self.data["vlans"] = self.config.vlans

                
            

    @staticmethod
    def jprint(data):
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    config = BaseConfigParser(filepath=pathlib.Path(r"C:\Users\mhudec\CloudStation\Work\ALEF\MHMP\scripts\data\CFG\MHMP\cat01Ask.txt"), verbosity=1)
    
    ctj = ConfigToJson(config=config, verbosity=2)
    ctj.parse_interfaces()
    ctj.parse_common()
    #ctj.jprint(ctj.data)


    with open(r"C:\Users\mhudec\Develop\ccutils\MHMP\new_configs\cat01Ask.json", mode="w") as f:
        json.dump(obj=ctj.data, fp=f, indent=2)
    
