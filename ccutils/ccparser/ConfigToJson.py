from ccutils.ccparser import BaseConfigParser, BaseConfigLine
from ccutils.utils.common_utils import get_logger
import re
import json
import pathlib


class ConfigToJson:
    """

    """
    def __init__(self, config, verbosity=1):
        """

        :param config: Reference to the parent BaseConfigParser object
        :param int verbosity: Logging output level
        """
        self.config = config
        self.logger = get_logger(name="CTJ", verbosity=verbosity)
        self.data = {
            "interfaces": {}
        }
        self.parse_interfaces()
        self.parse_common()

    def parse_interfaces(self):
        """

        :return:
        """
        interface_lines = list(filter(lambda x: "interface" in x.type, self.config.config_lines_obj))
        self.logger.debug(msg="Loaded {} interface lines.".format(len(interface_lines)))
        for interface in interface_lines:
            interface_name = interface.interface_name
            port_mode = interface.port_mode

            self.data["interfaces"][interface_name] = {"flags": [port_mode], "description": interface.interface_description, "unprocessed_lines": interface.get_unprocessed(return_type="text")}
            if "Vlan" in interface_name:
                self.data["interfaces"][interface_name]["flags"].append("svi")
            elif "Ethernet" in interface_name:
                self.data["interfaces"][interface_name]["flags"].append("physical")
            elif "Port-channel" in interface_name:
                self.data["interfaces"][interface_name]["flags"].append("port-channel")

            # Get Shutdown State
            self.data["interfaces"][interface_name]["shutdown"] = interface.shutdown
            # Get CDP
            self.data["interfaces"][interface_name]["cdp"] = interface.cdp
            # Get Logging events
            self.data["interfaces"][interface_name]["logging_events"] = interface.logging_events
            # Get channel group
            self.data["interfaces"][interface_name]["channel_group"] = interface.channel_group
            if self.data["interfaces"][interface_name]["channel_group"]:
                self.data["interfaces"][interface_name]["flags"].append("pc-member")
            
            # Get speed and duplex
            self.data["interfaces"][interface_name]["speed"] = interface.speed
            self.data["interfaces"][interface_name]["duplex"] = interface.duplex


            

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
                if self.data["interfaces"][interface_name]["l3"]["standby"]:
                    self.data["interfaces"][interface_name]["flags"].append("standby")
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
        # Get Hostname
        self.data["hostname"] = self.config.hostname
        # Get Domain name
        self.data["domain_name"] = self.config.domain_name
        # Get Name-Servers
        self.data["name_servers"] = self.config.name_servers
        self.data["cdp"] = self.config.cdp
        self.data["vlans"] = self.config.vlans
        self.data["vrfs"] = self.config.vrfs

    def get_interface_list(self, flags_filter=None):
        interfaces = []
        if not flags_filter:
            interfaces = list(self.data["interfaces"].keys())
        else:
            if isinstance(flags_filter, list):
                for interface, params in self.data["interfaces"].items():
                    for flag in flags_filter:
                        if flag in params["flags"]:
                            interfaces.append(interface)
        return interfaces

    @staticmethod
    def jprint(data):
        print(json.dumps(data, indent=2))

    
