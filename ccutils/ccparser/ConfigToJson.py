from ccutils.ccparser import BaseConfigParser, BaseConfigLine
from ccutils.utils.common_utils import get_logger, interface_sort, UnsortableOrderedDict, has_old_pyyaml
from ccutils.utils import CiscoRange
import re
import json
import pathlib
from collections import OrderedDict


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
            port_mode = interface.port_mode
            flags = interface.flags
            self.data["interfaces"][interface.name] = {"flags": flags, "unprocessed_lines": interface.get_unprocessed(return_type="text")}

            # Get Shutdown State
            self.data["interfaces"][interface.name]["shutdown"] = interface.shutdown

            # Get Description
            if interface.description or not self.omit_empty:
                self.data["interfaces"][interface.name]["description"] = interface.description

            # Get CDP
            self.data["interfaces"][interface.name]["cdp"] = interface.cdp

            # Get Logging events
            if interface.logging_events or not self.omit_empty:
                self.data["interfaces"][interface.name]["logging_events"] = interface.logging_events

            # Get channel group
            if interface.channel_group or not self.omit_empty:
                self.data["interfaces"][interface.name]["channel_group"] = interface.channel_group
            
            # Get speed and duplex
            if interface.speed or not self.omit_empty:
                self.data["interfaces"][interface.name]["speed"] = interface.speed
            if interface.duplex or not self.omit_empty:
                self.data["interfaces"][interface.name]["duplex"] = interface.duplex

            if port_mode == "l3":
                # Get IP addresses
                self.data["interfaces"][interface.name]["l3"] = {}
                ip_addresses = interface.ip_addresses
                if len(ip_addresses):
                    self.data["interfaces"][interface.name]["l3"]["ip_addresses"] = ip_addresses
                else:
                    self.data["interfaces"][interface.name]["l3"]["ip_addresses"] = []
                # Get VRF
                self.data["interfaces"][interface.name]["l3"]["vrf"] = interface.vrf
                # Get OSPF Priority
                self.data["interfaces"][interface.name]["l3"]["ospf_priority"] = interface.ospf_priority
                # Get standby
                self.data["interfaces"][interface.name]["l3"]["standby"] = interface.standby
                if self.data["interfaces"][interface.name]["l3"]["standby"]:
                    self.data["interfaces"][interface.name]["flags"].append("standby")
                # Get Helper Address
                self.data["interfaces"][interface.name]["l3"]["helper_addresses"] = interface.helper_address
                ip_mtu = interface.ip_mtu
                tcp_mss = interface.tcp_mss
                if ip_mtu:
                    self.data["interfaces"][interface.name]["l3"]["ip_mtu"] = ip_mtu
                if tcp_mss:
                    self.data["interfaces"][interface.name]["l3"]["tcp_mss"] = tcp_mss

            elif port_mode == "l2":

                self.data["interfaces"][interface.name]["l2"] = {}

                # Get Native VLAN
                if interface.native_vlan or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["native_vlan"] = interface.native_vlan

                # Get Trunk Encapsulation
                if interface.trunk_encapsulation or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["trunk_encapsulation"] = interface.trunk_encapsulation

                # Get Switchport Mode
                if interface.switchport_mode or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["mode"] = interface.switchport_mode

                # Get Trunk Allowed VLANs
                if interface.trunk_allowed_vlans or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["allowed_vlans"] = interface.trunk_allowed_vlans

                # Get Access VLAN
                if interface.access_vlan or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["access_vlan"] = interface.access_vlan
                
                # Get Voice VLAN
                if interface.voice_vlan or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["voice_vlan"] = interface.voice_vlan

                # Get Storm Control
                if interface.storm_control or not self.omit_empty:
                    self.data["interfaces"][interface.name]["l2"]["storm_control"] = interface.storm_control

            if "tunnel" in flags:
                self.data["interfaces"][interface.name]["tunnel"] = interface.tunnel_properties

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

    def get_ordered_interfaces(self):
        """
        Return interfaces as OrderedDict

        Returns:
            (:obj:`OrderedDict`): Interface section as OrderedDict

        """
        interfaces_crange = CiscoRange(list(self.data["interfaces"].keys()))
        ordered_interfaces = OrderedDict(sorted(self.data["interfaces"].items(), key=lambda x: interface_sort(crange=interfaces_crange, name=x[0])))

        return ordered_interfaces

    def to_json(self, indent=2):
        """
        Return JSON formatted structure describing configuration

        Args:
            indent (int): Set JSON indent, defaults to 2

        Returns:
            str: JSON string

        """
        # Convert Interfaces to OrderedDict
        data = dict(self.data)
        data["interfaces"] = self.get_ordered_interfaces()
        return json.dumps(obj=data, indent=indent)

    def to_yaml(self):
        """
        Return YAML formatted structure describing configuration

        Returns:
            str: YAML string
        """
        try:
            import yaml

            class CustomDumper(yaml.Dumper):
                pass

        except ImportError:
            self.logger.error("Missing Package PyYAML. Please install it by running 'pip3 install pyyaml'")
            return ""

        # Convert Interfaces to OrderedDict
        data = dict(self.data)
        data["interfaces"] = self.get_ordered_interfaces()
        if has_old_pyyaml():
            data["interfaces"] = UnsortableOrderedDict(data["interfaces"])
            CustomDumper.add_representer(UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict)
            return yaml.dump(data=data, sort_keys=False, Dumper=CustomDumper)
        else:
            CustomDumper.add_representer(OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
            return yaml.dump(data=data, sort_keys=False, Dumper=CustomDumper)

    @staticmethod
    def jprint(data):
        print(json.dumps(data, indent=2))

    
