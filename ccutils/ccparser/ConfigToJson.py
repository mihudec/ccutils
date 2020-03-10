from ccutils.ccparser import BaseConfigParser, BaseConfigLine
from ccutils.utils.common_utils import get_logger
import re
import json
import pathlib


class ConfigToJson:
    """

    """
    def __init__(self, config, omit_empty=False, verbosity=3):
        """

        :param config: Reference to the parent BaseConfigParser object
        :param int verbosity: Logging output level
        """
        self.config = config
        self.omit_empty = omit_empty
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
            flags = interface.flags
            self.data["interfaces"][interface_name] = {"flags": flags, "description": interface.interface_description, "unprocessed_lines": interface.get_unprocessed(return_type="text")}

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
                ip_mtu = interface.ip_mtu
                tcp_mss = interface.tcp_mss
                if ip_mtu:
                    self.data["interfaces"][interface_name]["l3"]["ip_mtu"] = ip_mtu
                if tcp_mss:
                    self.data["interfaces"][interface_name]["l3"]["tcp_mss"] = tcp_mss
            elif port_mode == "l2":
                self.data["interfaces"][interface_name]["l2"] = {}
                # Get Native VLAN
                self.data["interfaces"][interface_name]["l2"]["native_vlan"] = interface.native_vlan
                # Get Trunk Encapsulation
                self.data["interfaces"][interface_name]["l2"]["trunk_encapsulation"] = interface.trunk_encapsulation
                # Get Switchport Mode
                self.data["interfaces"][interface_name]["l2"]["mode"] = interface.switchport_mode

                # Get Trunk Allowed VLANs
                trunk_allowed_vlans = interface.access_vlan
                if trunk_allowed_vlans:
                    self.data["interfaces"][interface_name]["l2"]["allowed_vlans"] = trunk_allowed_vlans
                elif not trunk_allowed_vlans and not self.omit_empty:
                    self.data["interfaces"][interface]["l2"]["allowed_vlans"] = None
                elif not trunk_allowed_vlans and self.omit_empty:
                    pass

                # Get Access VLAN
                access_vlan = interface.access_vlan
                if access_vlan:
                    self.data["interfaces"][interface_name]["l2"]["access_vlan"] = access_vlan
                elif not access_vlan and not self.omit_empty:
                    self.data["interfaces"][interface]["l2"]["access_vlan"] = None
                elif not access_vlan and self.omit_empty:
                    pass
                
                # Get Voice VLAN
                voice_vlan = interface.voice_vlan
                if voice_vlan:
                    self.data["interfaces"][interface_name]["l2"]["voice_vlan"] = voice_vlan
                elif not voice_vlan and not self.omit_empty:
                    self.data["interfaces"][interface_name]["l2"]["voice_vlan"] = None
                elif not voice_vlan and self.omit_empty:
                    pass

                # Get Storm Control
                storm_control = interface.storm_control
                if storm_control:
                    self.logger.debug("Interface {}:\tStorm-Control: Present".format(interface_name))
                    self.data["interfaces"][interface_name]["l2"]["storm_control"] = storm_control
                elif not storm_control and not self.omit_empty:
                    self.logger.debug("Interface {}:\tStorm-Control: Absent\t Omit: {}".format(interface_name, self.omit_empty))
                    self.data["interfaces"][interface_name]["l2"]["storm_control"] = None
                elif not storm_control and self.omit_empty:
                    self.logger.debug("Interface {}:\tStorm-Control: Absent\t Omit: {}".format(interface_name, self.omit_empty))
                    pass


            if "tunnel" in flags:
                self.data["interfaces"][interface_name]["tunnel"] = interface.tunnel_properties

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
                            if interface not in interfaces:
                                interfaces.append(interface)
        return interfaces

    @staticmethod
    def jprint(data):
        print(json.dumps(data, indent=2))

    
