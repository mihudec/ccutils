from ccutils.ccparser import BaseInterfaceLine
from ccutils.utils.common_utils import get_logger, split_interface_name, value_to_bool, value_to_int, remove_empty_values, strip_none, strip_false
from ccutils.utils import CiscoRange
import re
import functools

class CiscoIosInterfaceLine(BaseInterfaceLine):


    # Regexes
    _ip_addr_regex = re.compile(pattern=r"^\sip\saddress\s(?P<ip_address>(?:\d{1,3}\.){3}\d{1,3})\s(?P<mask>(?:\d{1,3}\.){3}\d{1,3})(?:\s(?P<secondary>secondary))?", flags=re.MULTILINE)
    _ipv4_addr_regex = re.compile(pattern=r"^ ip address (?P<address>(?:\d{1,3}\.){3}\d{1,3}) (?P<mask>(?:\d{1,3}\.){3}\d{1,3})(?: (?P<secondary>secondary))?", flags=re.MULTILINE)
    _ipv4_unnumbered_interface_regex = re.compile(pattern=r"^ ip unnumbered (?P<unnumbered>\S+)", flags=re.MULTILINE)
    _description_regex = re.compile(pattern=r"^\sdescription\s(?P<description>.*)")
    _vrf_regex = re.compile(pattern=r"^(?:\sip)?\svrf\sforwarding\s(?P<vrf>\S+)", flags=re.MULTILINE)
    _shutdown_regex = re.compile(pattern=r"^\sshutdown", flags=re.MULTILINE)
    _cdp_regex = re.compile(pattern=r"cdp enable")
    _logging_event_regex = re.compile(pattern=r"^\slogging\sevent\s(?P<logging_event>\S+)", flags=re.MULTILINE)

    _standby_ip_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\sip\s(?P<ip_address>(?:\d{1,3}\.){3}\d{1,3})(?:\s(?P<secondary>secondary))?", flags=re.MULTILINE)
    _standby_ipv4_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\sip\s(?P<address>(?:\d{1,3}\.){3}\d{1,3})(?:\s(?P<secondary>secondary))?", flags=re.MULTILINE)
    _standby_timers_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\stimers(?:\s(?P<timers_msec>msec))?\s(?P<hello>\d+)\s(?P<hold>\d+)", flags=re.MULTILINE)
    _standby_priority_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\spriority\s(?P<priority>\d+)", flags=re.MULTILINE)
    _standby_preempt_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\s(?P<preempt>preempt)", flags=re.MULTILINE)
    _standby_authentication_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\sauthentication\s(?P<authentication_type>md5)\skey-string\s(?:(?P<key_type>0|7)\s)?(?P<key_string>\S+)", flags=re.MULTILINE)
    _standby_version_regex = re.compile(pattern=r"^\sstandby\sversion\s(?P<version>2)")
    _standby_group_regex = re.compile(pattern=r"^ standby (?P<standby_group>\d+)")
    _standby_name_regex = re.compile(pattern=r"^ standby (?P<standby_group>\d+) name (?P<name>\S+)", flags=re.MULTILINE)
    _standby_follow_regex = re.compile(pattern=r"^ standby (?P<standby_group>\d+) follow (?P<follow>\S+)", flags=re.MULTILINE)
    _standby_track_regex = re.compile(pattern=r"^ standby (?P<standby_group>\d+) track (?P<id>\d+) (?P<action>shutdown|decrement)(?: (?P<decrement>\d+))?$", flags=re.MULTILINE)
    _standby_auth_regexes = [
        re.compile(pattern="^ standby (?P<standby_group>\d+) authentication (?P<auth_method>md5) key-chain (?P<keychain>\S+)$", flags=re.MULTILINE),
        re.compile(pattern="^ standby (?P<standby_group>\d+) authentication (?P<auth_method>md5|text) (?:key-string )?(?:(?P<encryption_type>\d+) )?(?P<key_string>\S+)$", flags=re.MULTILINE)

    ]

    _helper_address_regex = re.compile(pattern=r"^\sip\shelper-address\s(?P<helper_address>(?:\d{1,3}\.){3}\d{1,3})", flags=re.MULTILINE)

    _ip_dhcp_snooping_trust_regex = re.compile(r"^\sip dhcp snooping trust$", flags=re.MULTILINE)

    _native_vlan_regex = re.compile(pattern=r"^ switchport trunk native vlan (?P<native_vlan>\d+)", flags=re.MULTILINE)
    _trunk_encapsulation_regex = re.compile(pattern=r"^ switchport trunk encapsulation (?P<encapsulation>dot1q|isl|negotiate)", flags=re.MULTILINE)
    _switchport_mode_regex = re.compile(pattern=r"^ switchport mode (?P<switchport_mode>access|trunk|dot1q-tunnel|private-vlan|dynamic)")
    _switchport_nonegotiate_regex = re.compile(pattern=r"^ switchport nonegotiate")
    _trunk_allowed_vlans_regex = re.compile(pattern=r"^ switchport trunk allowed vlan(?: add)? (?P<allowed_vlans>\S+)", flags=re.MULTILINE)
    _access_vlan_regex = re.compile(pattern=r"^ switchport access vlan (?P<access_vlan>\d+)", flags=re.MULTILINE)
    _voice_vlan_regex = re.compile(pattern=r"^ switchport voice vlan (?P<voice_vlan>\d+)")

    _channel_group_regex = re.compile(pattern=r"^ channel-group (?P<channel_group_number>\d+) mode (?P<channel_group_mode>\S+)")
    _speed_regex = re.compile(pattern=r"^ speed (?P<speed>\d+)", flags=re.MULTILINE)
    _duplex_regex = re.compile(pattern=r"^ duplex (?P<duplex>full|half)", flags=re.MULTILINE)
    _load_interval_regex = re.compile(pattern=r"^ load-interval (?P<load_interval>\d+)")

    _bandwidth_regex = re.compile(pattern=r"^ bandwidth (?P<bandwidth>\d+)", flags=re.MULTILINE)
    _delay_regex = re.compile(pattern=r"^ delay (?P<delay>\d+)", flags=re.MULTILINE)
    _mtu_regex = re.compile(pattern=r"^ mtu (?P<mtu>\d+)", flags=re.MULTILINE)
    _ip_mtu_regex = re.compile(pattern=r"^ ip mtu (?P<ip_mtu>\d+)", flags=re.MULTILINE)
    _ip_tcp_mss_regex = re.compile(pattern=r"^ ip tcp adjust-mss (?P<tcp_mss>\d+)", flags=re.MULTILINE)
    _keepalive_regex = re.compile(pattern=r"^ keepalive (?P<period>\d+) (?P<retries>\d+)")
    _negotiation_regex = re.compile(pattern=r"^ negotiation (?P<negotiation>\S+)")


    _service_policy_regex = re.compile(pattern=r"^ service-policy (?P<direction>input|output) (?P<policy_map>\S+)", flags=re.MULTILINE)
    _tunnel_src_regex = re.compile(pattern=r"^ tunnel source (?P<source>\S+)", flags=re.MULTILINE)
    _tunnel_dest_regex = re.compile(pattern=r"^ tunnel destination (?P<destination>\S+)", flags=re.MULTILINE)
    _tunnel_vrf_regex = re.compile(pattern=r"^ tunnel vrf (?P<vrf>\S+)", flags=re.MULTILINE)
    _tunnel_mode_regex = re.compile(pattern=r"^ tunnel mode (?P<mode>.*?)$", flags=re.MULTILINE)
    _tunnel_ipsec_profile_regex = re.compile(pattern=r"^ tunnel protection ipsec profile (?P<ipsec_profile>\S+)", flags=re.MULTILINE)

    _storm_control_threshold_regex = re.compile(pattern=r"^ storm-control (?P<traffic>broadcast|multicast) level (?:(?P<type>bps|pps) )?(?P<raising>\d{1,3}(?:\.\d{1,2})?(?:k|m|g)?)(?: (?P<falling>\d{1,3}(?:\.\d{1,2})?(?:k|m|g)?))?", flags=re.MULTILINE)
    _storm_control_action_regex = re.compile(pattern=r"^ storm-control action (?P<action>trap|shutdown)")
    _device_tracking_attach_policy_regex = re.compile(pattern=r"^ device-tracking attach-policy (?P<policy>\S+)")
    _encapsulation_regex = re.compile(pattern=r"^ encapsulation (?P<type>\S+) (?P<tag>\d+)(?: (?P<native>native))?")

    _service_instance_regex = re.compile(pattern=r"^ service instance (?P<number>\d+) (?P<type>\S+)")
    _service_instance_description_regex = re.compile(pattern=r"^  description (?P<description>.*)")
    _service_instance_encapsulation_mapping_regex = re.compile(pattern=r"^  encapsulation (?P<type>\S+) (?P<tag>\d+)$", flags=re.MULTILINE)
    _service_instance_encapsulation_string_regex = re.compile(pattern=r"^  encapsulation (?P<encapsulation>\S+)$", flags=re.MULTILINE)
    _service_instance_bridge_domain_regex = re.compile(pattern=r"^  bridge-domain (?P<number>\d+)$", flags=re.MULTILINE)
    _service_instance_service_policy_regex = re.compile(pattern=r"^  service-policy (?P<direction>input|output) (?P<policy_map>\S+)$", flags=re.MULTILINE)
    _service_instance_shutdown_regex = re.compile(pattern=r"^  shutdown$", flags=re.MULTILINE)
    _service_instance_snmp_trap_regex = re.compile(pattern=r"^  snmp trap (?P<trap>\S+)")

    _ospf_process_regex = re.compile(pattern=r"^ ip ospf (?P<process_id>\d+) area (?P<area>\d+)$", flags=re.MULTILINE)
    _ospf_network_type_regex = re.compile(pattern=r"^ ip ospf network (?P<network_type>\S+)", flags=re.MULTILINE)
    _ospf_priority_regex = re.compile(pattern=r"^ ip ospf priority (?P<priority>\d+)", flags=re.MULTILINE)
    _ospf_cost_regex = re.compile(pattern=r"^ ip ospf cost (?P<cost>\d+)", flags=re.MULTILINE)

    _isis_process_regex = re.compile(pattern=r"^ ip router isis (?P<process_id>\S+)$", flags=re.MULTILINE)
    _isis_network_type_regex = re.compile(pattern=r"^ isis network (?P<network_type>\S+)", flags=re.MULTILINE)
    _isis_circuit_type_regex = re.compile(pattern=r"^ isis circuit-type (?P<circuit_type>\S+)", flags=re.MULTILINE)
    _isis_metric_regex = re.compile(pattern=r"^ isis metric (?P<metric>\d+) (?P<level>level-[1-2])", flags=re.MULTILINE)
    _isis_authentication_mode_regex = re.compile(pattern=r"^ isis authentication mode (?P<mode>\S+)", flags=re.MULTILINE)
    _isis_authentication_keychain_regex = re.compile(pattern=r"^ isis authentication key-chain (?P<keychain>\S+)", flags=re.MULTILINE)

    _bfd_template_regex = re.compile(pattern=r"^ bfd template (?P<template>\S+)", flags=re.MULTILINE)








    def __init__(self, number, text, config, verbosity=3):
        super(CiscoIosInterfaceLine, self).__init__(number=number, text=text, config=config, verbosity=verbosity, name="CiscoIosInterfaceLine")

    @functools.lru_cache()
    def get_unprocessed(self, return_type=None):
        """
        Return a list of config lines under the interface, which did not match any of the existing regex patterns.
        Mostly for development/testing purposes.

        By default returns list of objects.

        Args:
            return_type (str): Set this to `"text"` to receive list of strings

        Returns:
            list: List of unprocessed config lines

        """
        unprocessed_children = self.get_children()

        regexes = [
            self._description_regex,
            self._ip_addr_regex,
            self._ipv4_addr_regex,
            self._vrf_regex,
            self._shutdown_regex,
            self._ospf_priority_regex,
            self._ospf_process_regex,
            self._ospf_network_type_regex,
            self._ospf_cost_regex,
            self._isis_process_regex,
            self._isis_metric_regex,
            self._isis_network_type_regex,
            self._isis_circuit_type_regex,
            self._isis_authentication_mode_regex,
            self._isis_authentication_keychain_regex,
            self._bfd_template_regex,
            self._cdp_regex,
            self._logging_event_regex,
            self._standby_ip_regex,
            self._standby_timers_regex,
            self._standby_priority_regex,
            self._standby_preempt_regex,
            self._standby_authentication_regex,
            self._standby_version_regex,
            self._standby_name_regex,
            self._standby_ipv4_regex,
            self._standby_auth_regexes,
            self._standby_group_regex,
            self._standby_follow_regex,
            self._standby_track_regex,
            self._standby_auth_regexes[0],
            self._standby_auth_regexes[1],
            self._helper_address_regex,
            self._native_vlan_regex,
            self._trunk_encapsulation_regex,
            self._switchport_mode_regex,
            self._switchport_nonegotiate_regex,
            self._trunk_allowed_vlans_regex,
            self._access_vlan_regex,
            self._voice_vlan_regex,
            self._channel_group_regex,
            self._speed_regex,
            self._duplex_regex,
            self._load_interval_regex,
            self._bandwidth_regex,
            self._delay_regex,
            self._mtu_regex,
            self._ip_mtu_regex,
            self._ip_tcp_mss_regex,
            self._keepalive_regex,
            self._service_policy_regex,
            self._tunnel_src_regex,
            self._tunnel_dest_regex,
            self._tunnel_vrf_regex,
            self._tunnel_mode_regex,
            self._tunnel_ipsec_profile_regex,
            self._storm_control_threshold_regex,
            self._storm_control_action_regex,
            self._encapsulation_regex,
            self._service_instance_regex,
            self._service_instance_description_regex,
            self._service_instance_encapsulation_mapping_regex,
            self._service_instance_encapsulation_string_regex,
            self._service_instance_bridge_domain_regex,
            self._service_instance_service_policy_regex,
            self._ipv4_unnumbered_interface_regex,
            self._negotiation_regex,
            self._ip_dhcp_snooping_trust_regex,
            re.compile(pattern=r"^\s*!.*", flags=re.MULTILINE),
            re.compile(pattern=r"^\sno\sip\saddress", flags=re.MULTILINE),
            re.compile(pattern=r"^ (no )?switchport$", flags=re.MULTILINE),
            re.compile(pattern=r"^ spanning-tree portfast")
        ]
        for regex in regexes:
            for child in self.re_search_children(regex=regex):
                unprocessed_children.remove(child)
        if return_type == "text":
            return [x.text for x in unprocessed_children]
        elif return_type == "obj":
            return unprocessed_children
        else:
            return [x.text for x in unprocessed_children]

    @property
    @functools.lru_cache()
    def flags(self):
        """
        List of flags/tags describing basic properties of the interface. Used for filtering purposes.
        Currently supported flags are:

        ``l2`` - Interface is switched port

        ``l3`` - Interface is routed port

        ``physical`` - Interface is a physical interface (Only \*Ethernet interfaces)

        ``svi`` - Interface is SVI (VLAN Interface)

        ``port-channel`` - Interface is port-channel

        ``pc-member`` - Interface is a member of Port-channel

        ``tunnel`` - Interface is a Tunnel

        Returns:
             list: List of flags

        """
        flags = []
        flags.append(self.port_mode)
        interface = split_interface_name(self.name)
        if "Vlan" in interface[0]:
            flags.append("svi")
        elif "Ethernet" in interface[0]:
            flags.append("physical")
            if self.channel_group is not None:
                flags.append("pc-member")
        elif "Port-channel" in interface[0]:
            flags.append("port-channel")
        elif "Tunnel" in interface[0]:
            flags.append("tunnel")
        elif "Loopback" in interface[0]:
            flags.append("virtual")
        elif "BDI" in interface[0]:
            flags.append("virtual")
        return flags

    @property
    @functools.lru_cache()
    def interface_name(self):
        self.logger.warning("DEPRECATED: You are using deprecated property .interface_name, use .name instead.")
        return self.name

    @property
    @functools.lru_cache()
    def name(self):
        """
        Return name of the interface, such as `GigabitEthernet0/1`.

        Returns:
            str: Name of the interface

        """
        if not self.is_interface:
            return None
        else:
            return self.re_match(self._interface_regex, group=1)

    @property
    @functools.lru_cache()
    def interface_description(self):
        self.logger.warning("DEPRECATED: You are using deprecated property .interface_description, use .description instead.")
        return self.description

    @property
    @functools.lru_cache()
    def description(self):
        """
        Returns description of the interface.

        Returns:
            str: Interface description

            Returns ``None`` if absent

        """
        if not self.is_interface:
            return None
        else:
            regex = r"description\s(.*)"
            candidates = self.re_search_children(regex=self._description_regex, group="description")
            if len(candidates) == 1:
                return candidates[0]
            else:
                return None

    @property
    @functools.lru_cache()
    def port_mode(self):
        """
        Checks whether the interface is running in switched (**l2**) or routed (**l3**) mode.

        Returns:
            str: `l2` or `l3`

        """
        if len(self.re_search_children(regex="ip address")):
            return "l3"
        elif len(self.re_search_children(regex=r"ip unnumbered")):
            return "l3"
        else:
            return "l2"

    @property
    @functools.lru_cache()
    def ip_addresses(self):
        """
        Return list of IP addresses present on the interface

        Returns:
            list: List of dictionaries representing individual IP addresses

            Example::

                [
                    {
                        "ip_address": "10.0.0.1",
                        "mask": "255.255.255.0",
                        "secondary": False
                    },
                    {
                        "ip_address": "10.0.1.1",
                        "mask": "255.255.255.0",
                        "secondary": True
                    }
                ]

            If there is no IP address present on the interface, an empty list is returned.

        """
        self.logger.warning("DEPRECATION WARNING: You are using deprecated property 'ip_addresses'. Please switch to using 'ipv4_addresses'. The 'ip_addresses' property will be removed in Version 0.3.0.")

        # print("DEPRECATION WARNING: You are using deprecated property 'ip_addresses'. Please switch to using 'ipv4_addresses'. The 'ip_addresses' property will be removed in Version 0.3.0.")
        ip_addresses = []
        candidates = self.re_search_children(regex=self._ip_addr_regex)
        for candidate in candidates:
            ip_addresses.append(self._val_to_bool(entry=candidate.re_search(regex=self._ip_addr_regex, group="ALL"), key="secondary"))
        return ip_addresses

    @property
    @functools.lru_cache()
    def ipv4_addresses(self) -> list:
        """
        Return list of IPv4 addresses present on the interface

        Returns:
            list: List of dictionaries representing individual IPv4 addresses

            Example::

                [
                    {
                        "address": "10.0.0.1",
                        "mask": "255.255.255.0",
                        "secondary": False
                    },
                    {
                        "address": "10.0.1.1",
                        "mask": "255.255.255.0",
                        "secondary": True
                    }
                ]

            If there is no IP address present on the interface, an empty list is returned.

        """
        ipv4_addresses = []
        candidates = self.re_search_children(regex=self._ipv4_addr_regex)
        for candidate in candidates:
            ipv4_addresses.append(
                value_to_bool(entry=candidate.re_search(regex=self._ipv4_addr_regex, group="ALL"), keys=["secondary"])
            )
        if self.config.minimal_results:
            ipv4_addresses = strip_false(ipv4_addresses)
        return ipv4_addresses

    @property
    @functools.lru_cache()
    def ipv6_addresses(self) -> list:
        """
        Return list of IPv6 addresses present on the interface

        Returns:
            list: List of dictionaries representing individual IPv6 addresses

            If there is no IP address present on the interface, an empty list is returned.

        """
        raise NotImplementedError("Sorry, this property is waiting to be implemented")

    @property
    @functools.lru_cache()
    def ip_unnumbered_interface(self):
        return self.ipv4_unnumbered_interface()

    @property
    @functools.lru_cache()
    def ipv4_unnumbered_interface(self):
        ipv4_unnumbered_interface = None
        candidates = self.re_search_children(regex=self._ipv4_unnumbered_interface_regex, group="unnumbered")
        if len(candidates):
            ipv4_unnumbered_interface = candidates[0]
        return ipv4_unnumbered_interface



    @property
    @functools.lru_cache()
    def vrf(self):
        """
        Return VRF of the interface

        Returns:
            str: Name of the VRF

            Returns ``None`` if absent

        """
        vrf = None
        candidates = self.re_search_children(regex=self._vrf_regex, group="vrf")
        if len(candidates):
            vrf = candidates[0]
        return vrf

    @property
    @functools.lru_cache()
    def shutdown(self):
        if len(self.re_search_children(regex=self._shutdown_regex)):
            return True
        else:
            return False

    @property
    @functools.lru_cache()
    def ospf_priority(self):
        """
        Returns OSPF priority of the interface.

        Returns:
            int: OSPF Priority or None

        """
        self.logger.warning("DEPRECATED: You are using deprecated property .ospf_priority, use .ospf['priority'] instead.")
        ospf_priority = None
        candidates = self.re_search_children(regex=self._ospf_priority_regex, group="priority")
        if len(candidates):
            ospf_priority = int(candidates[0])
        return ospf_priority

    @property
    @functools.lru_cache()
    def ospf(self):
        """
        Return OSPF interface parameters

        Returns:
            dict: OSPF parameters

            Example::

                {"process_id": 1, "area": 0, "network_type": "point-to-point", "priority": 200}

            Returns ``None`` if absent

        """
        ospf = None
        # OSPF Process Section
        candidates = self.re_search_children(regex=self._ospf_process_regex, group="ALL")
        if len(candidates):
            ospf = candidates[0]
            ospf["process_id"] = int(ospf["process_id"])
            ospf["area"] = int(ospf["area"])
        # OSPF Network Type Section
        candidates = self.re_search_children(regex=self._ospf_network_type_regex, group="ALL")
        if len(candidates):
            if ospf is None:
                ospf = {k: None for k in self._ospf_process_regex.groupindex.keys() if isinstance(k, str)}
            ospf.update(candidates[0])
        else:
            if ospf is not None:
                ospf.update({k: None for k in self._ospf_network_type_regex.groupindex.keys()})
        # OSPF Priority Section
        candidates = self.re_search_children(regex=self._ospf_priority_regex, group="ALL")
        if len(candidates):
            if ospf is None:
                ospf = {k: None for k in self._ospf_process_regex.groupindex.keys() if isinstance(k, str)}
                ospf.update({k: None for k in self._ospf_network_type_regex.groupindex.keys()})
            ospf.update(candidates[0])
            # Convert priority to int
            ospf["priority"] = int(ospf["priority"])
        else:
            if ospf is not None:
                ospf.update({k: None for k in self._ospf_priority_regex.groupindex.keys()})
        # OSPF Cost Section
        candidates = self.re_search_children(regex=self._ospf_cost_regex, group="ALL")
        if len(candidates):
            if ospf is None:
                ospf = {k: None for k in self._ospf_process_regex.groupindex.keys() if isinstance(k, str)}
                ospf.update({k: None for k in self._ospf_network_type_regex.groupindex.keys()})
                ospf.update({k: None for k in self._ospf_priority_regex.groupindex.keys()})
            ospf.update(candidates[0])
            # Convert cost to int
            ospf["cost"] = int(ospf["cost"])
        else:
            if ospf is not None:
                ospf.update({k: None for k in self._ospf_cost_regex.groupindex.keys()})

        return ospf

    @property
    @functools.lru_cache()
    def isis(self):
        """

        Return IS-IS interface parameters

        Returns:
            dict: IS-IS parameters

            Example::

                {}

            Returns ``None`` if absent

        """
        isis = {}
        # ISIS Process ID Section
        patterns = [
            self._isis_process_regex,
            self._isis_network_type_regex,
            self._isis_circuit_type_regex
        ]
        for regex in patterns:
            candidates = self.re_search_children(regex=regex, group="ALL")
            if len(candidates):
                isis.update(candidates[0])

        # Metrics
        isis["metric"] = []
        candidates = self.re_search_children(regex=self._isis_metric_regex, group="ALL")
        if len(candidates):
            for candidate in candidates:
                isis["metric"].append(candidate)

        # Authentication mode
        isis["authentication"] = {}
        candidates = self.re_search_children(regex=self._isis_authentication_mode_regex, group="ALL")
        if len(candidates):
            if isis is None:
                isis = {"authentication": {}}
        if len(candidates) == 1:
            isis["authentication"].update(candidates[0])
        elif len(candidates) == 0:
            isis["authentication"].update({k: None for k in self._isis_authentication_mode_regex.groupindex.keys()})

        # Authentication keychain
        candidates = self.re_search_children(regex=self._isis_authentication_keychain_regex, group="ALL")
        if len(candidates):
            if isis is None:
                isis = {"authentication": {}}
        if len(candidates) == 1:
            isis["authentication"].update(candidates[0])
        elif len(candidates) == 0:
            isis["authentication"].update({k: None for k in self._isis_authentication_keychain_regex.groupindex.keys()})

        if self.config.minimal_results:
            isis = strip_none(isis)
            if not any(isis["metric"]):
                del isis["metric"]
            if not any(isis["authentication"].values()):
                del isis["authentication"]

        if not any(isis.values()):
            isis = None

        return isis

    @property
    @functools.lru_cache()
    def standby(self):
        standby = {}
        # Get only list of all standby groups
        standby_group_candidates = [x for x in set(
            self.re_search_children(regex=self._standby_group_regex, group="standby_group"))]
        standby_global_candidates = self.re_search_children(regex=r"standby [^\d].*")
        if len(standby_group_candidates) or len(standby_global_candidates):
            standby = {"groups": {}}
        else:
            return None


        for group_id in standby_group_candidates:
            standby["groups"][group_id] = {"group": int(group_id)}

        # Standby IPv4
        standby_ipv4_candidates = [value_to_bool(entry=x, keys=["secondary"], keep_none=False) for x in
                                   self.re_search_children(regex=self._standby_ipv4_regex, group="ALL")]
        self.logger.debug(msg=f"Interface {self.name}:\tIPv4 Candidates: {standby_ipv4_candidates}")

        standby_preempt_candidates = [value_to_bool(entry=x, keys=["preempt"], keep_none=False) for x in
                                      self.re_search_children(regex=self._standby_preempt_regex, group="ALL")]
        self.logger.debug(msg=f"Interface {self.name}:\tPreempt Candidates: {standby_preempt_candidates}")

        standby_timers_candidates = [value_to_bool(entry=x, keys=["timers_msec"], keep_none=False) for x in
                                     self.re_search_children(regex=self._standby_timers_regex, group="ALL")]
        self.logger.debug(msg=f"Interface {self.name}:\tTimers Candidates: {standby_timers_candidates}")

        standby_priority_candidates = self.re_search_children(regex=self._standby_priority_regex, group="ALL")
        self.logger.debug(msg=f"Interface {self.name}:\tPriority Candidates: {standby_priority_candidates}")

        standby_name_candidates = self.re_search_children(regex=self._standby_name_regex, group="ALL")
        self.logger.debug(msg=f"Interface {self.name}:\tName Candidates: {standby_name_candidates}")

        standby_follow_candidates = self.re_search_children(regex=self._standby_follow_regex, group="ALL")
        self.logger.debug(msg=f"Interface {self.name}:\tFollow Candidates: {standby_follow_candidates}")

        standby_auth_candidates = self.re_search_children_multipattern(regexes=self._standby_auth_regexes, group="ALL")
        self.logger.debug(msg=f"Interface {self.name}:\tAuth Candidates: {standby_auth_candidates}")

        standby_track_candidates = self.re_search_children(regex=self._standby_track_regex, group="ALL")
        self.logger.debug(msg=f"Interface {self.name}:\tTrack Candidates: {standby_track_candidates}")

        standby_version_candidates = self.re_search_children(regex=self._standby_version_regex, group="ALL")
        self.logger.debug(msg=f"Interface {self.name}:\tVersion Candidates: {standby_version_candidates}")

        # Standby Version
        if len(standby_version_candidates):
            standby["version"] = int(standby_version_candidates[0]["version"])
        else:
            standby["version"] = None

        if "groups" in standby.keys():
            for group_id in standby["groups"].keys():
                ipv4s = [x for x in standby_ipv4_candidates if x["standby_group"] == group_id]
                for x in ipv4s:
                    del x["standby_group"]
                standby["groups"][group_id]["ipv4"] = ipv4s

                preempt = [x for x in standby_preempt_candidates if x["standby_group"] == group_id]
                if len(preempt):
                    preempt = preempt[0]["preempt"]
                    standby["groups"][group_id]["preempt"] = preempt
                else:
                    standby["groups"][group_id]["preempt"] = None


                timers = [x for x in standby_timers_candidates if x["standby_group"] == group_id]
                if len(timers):
                    timers = timers[0]
                    del timers["standby_group"]
                    standby["groups"][group_id].update(value_to_int(entry=timers, keys=["hello", "hold"]))
                else:
                    standby["groups"][group_id].update({k: None for k in ["hello", "hold", "timers_msec"]})

                priority = [x for x in standby_priority_candidates if x["standby_group"] == group_id]
                if len(priority):
                    priority = priority[0]["priority"]
                    standby["groups"][group_id]["priority"] = int(priority)
                else:
                    standby["groups"][group_id]["priority"] = None

                name = [x for x in standby_name_candidates if x["standby_group"] == group_id]
                if len(name):
                    name = name[0]["name"]
                    standby["groups"][group_id]["name"] = name
                else:
                    standby["groups"][group_id]["name"] = None

                follow = [x for x in standby_follow_candidates if x["standby_group"] == group_id]
                if len(follow):
                    follow = follow[0]["follow"]
                    standby["groups"][group_id]["follow"] = follow
                else:
                    standby["groups"][group_id]["follow"] = None

                auth = [x for x in standby_auth_candidates if x["standby_group"] == group_id]
                if len(auth):
                    auth = auth[0]
                    if auth["auth_method"] == "text":
                        standby["groups"][group_id]["authentication"] = {
                            "method": "text",
                            "key": {
                                "string": auth["key_string"]
                            }
                        }
                    elif auth["auth_method"] == "md5":
                        standby["groups"][group_id]["authentication"] = {
                            "method": "md5"
                        }
                        if "keychain" in auth.keys():
                            standby["groups"][group_id]["authentication"]["keychain"] = auth["keychain"]
                        else:
                            standby["groups"][group_id]["authentication"]["key"] = {
                                "string": auth["key_string"],
                                "encryption_type": int(auth["encryption_type"]) if auth["encryption_type"] is not None else None
                            }
                else:
                    standby["groups"][group_id]["authentication"] = None

                track = [x for x in standby_track_candidates if x["standby_group"] == group_id]
                if len(track):
                    standby["groups"][group_id]["track"] = []
                    for t in track:
                        del t["standby_group"]
                        t = value_to_int(entry=t, keys=["decrement"])
                        standby["groups"][group_id]["track"].append(t)
                else:
                    standby["groups"][group_id]["track"] = None



        if self.config.minimal_results:
            standby = strip_none(standby)
            standby = strip_false(standby)
        if not any(standby.values()):
            standby = None

        return standby

    @property
    @functools.lru_cache()
    def bfd(self):
        bfd = {}
        candidates = self.re_search_children(regex=self._bfd_template_regex, group="ALL")
        if len(candidates) == 1:
            bfd.update(candidates[0])
        if not any(bfd.values()):
            bfd = None

        return bfd

    @property
    @functools.lru_cache()
    def cdp(self):
        """
        Checks whether CDP is enabled on the interface. This property takes global CDP configuration into account,
        meaning if there is no specific configuration on the interface level, it will return state based on the entire
        config (eg. `no cdp run` in the global config will make this property be `False`)

        Returns:
            bool: ``True`` if CDP is enabled, ``False`` otherwise

        """
        global_cdp = self.config.cdp
        candidates = self.re_search_children(regex=self._cdp_regex)
        if len(candidates):
            if "no" in candidates[0].text:
                return False
            else:
                return True
        else:
            return global_cdp

    @property
    @functools.lru_cache()
    def logging_events(self):
        return self.re_search_children(regex=self._logging_event_regex, group="logging_event")

    @property
    @functools.lru_cache()
    def standby_v1(self):
        """
        DEPRECATED: Use ``self.hsrp`` or ``self.standby`` instead
        HSRP related configuration. Groups, IP addresses, hello/hold timers, priority and authentication.


        :return: Dictionary with top level keys being HSRP groups.
        """

        data = {"version": 1}
        if self.re_search_children(regex=self._standby_version_regex, group="version"):
            data["version"] = 2
        standby_ips = [self._val_to_bool(entry=x, key="secondary") for x in self.re_search_children(regex=self._standby_ip_regex, group="ALL")]
        standby_timers = self.re_search_children(regex=self._standby_timers_regex, group="ALL")
        standby_priority = self.re_search_children(regex=self._standby_priority_regex, group="ALL")
        standby_preempt = [self._val_to_bool(entry=x, key="preempt") for x in self.re_search_children(regex=self._standby_preempt_regex, group="ALL")]
        standby_authentication = self.re_search_children(regex=self._standby_authentication_regex, group="ALL")
        if not len(standby_ips):
            return None
        data["groups"] = {}
        for entry in standby_ips:
            if entry["standby_group"] not in data["groups"].keys():
                data["groups"][entry["standby_group"]] = {"ip_addresses": []}
            data["groups"][entry["standby_group"]]["ip_addresses"].append(entry)
        for entry in standby_timers:
            data["groups"][entry["standby_group"]]["hello"] = entry["hello"]
            data["groups"][entry["standby_group"]]["hold"] = entry["hold"]
        for entry in standby_priority:
            data["groups"][entry["standby_group"]]["priority"] = entry["priority"]
        for entry in standby_preempt:
            data["groups"][entry["standby_group"]]["preempt"] = entry["preempt"]
        for entry in standby_authentication:
            data["groups"][entry["standby_group"]]["authentication_type"] = entry["authentication_type"]
            data["groups"][entry["standby_group"]]["key_type"] = entry["key_type"]
            data["groups"][entry["standby_group"]]["key_string"] = entry["key_string"]
        return data

    @property
    @functools.lru_cache()
    def helper_address(self):
        """
        Return a list of IP addresses specified with **ip helper-address** command (DHCP relay).

        Returns:
            list: List of helper addresses

            Returns ``None`` if absent

        """
        helper_address = None
        candidates = self.re_search_children(regex=self._helper_address_regex, group="helper_address")
        if len(candidates):
            helper_address = candidates
        return helper_address

    @property
    @functools.lru_cache()
    def native_vlan(self):
        """
        Return Native VLAN of L2 Interface

        Returns:
            int: Native VLAN Number (`None` if absent)

            Returns ``None`` if absent

        """
        native_vlan = None
        candidates = self.re_search_children(regex=self._native_vlan_regex, group="native_vlan")
        if len(candidates):
            native_vlan = int(candidates[0])
        return native_vlan

    @property
    @functools.lru_cache()
    def trunk_encapsulation(self):
        """
        Return encapsulation on trunk interfaces

        Returns:
            str: "dot1q" or "isl"

            Returns ``None`` if absent

        """
        trunk_encapsulation = None
        candidates = self.re_search_children(regex=self._trunk_encapsulation_regex, group="encapsulation")
        if len(candidates):
            trunk_encapsulation = candidates[0]
        return trunk_encapsulation

    @property
    @functools.lru_cache()
    def encapsulation(self):
        """
        Return encapsulation type and tag for subinterfaces

        Returns:
            dict: Encapsualtion parameters

            Example::

                {"type": "dot1q", "tag": 10, "native": False}

            Returns ``None`` if absent

        """
        encapsulation = None
        candidates = self.re_search_children(regex=self._encapsulation_regex, group="ALL")
        if len(candidates):
            encapsulation = candidates[0]
            encapsulation["tag"] = int(encapsulation["tag"])
            encapsulation = value_to_bool(encapsulation, keys=["native"])
        return encapsulation

    @property
    @functools.lru_cache()
    def switchport_mode(self):
        """
        Return L2 Mode of interface, either access or trunk

        Returns:
            str: "access" or "trunk"

            Returns ``None`` if absent

        """
        switchport_mode = None
        candidates = self.re_search_children(regex=self._switchport_mode_regex, group="switchport_mode")
        if len(candidates):
            switchport_mode = candidates[0]
        return switchport_mode

    @property
    @functools.lru_cache()
    def switchport_nonegotiate(self):
        """
        Check whether the port is running DTP or not. Checks for presence of ``switchport nonegotiate`` command

        Returns:
            bool: ``True`` if command is present, ``False`` otherwise

        """
        candidates = self.re_search_children(regex=self._switchport_nonegotiate_regex)
        if len(candidates):
            return True
        else:
            return False

    @property
    @functools.lru_cache()
    def trunk_allowed_vlans(self):
        """
        Return a expanded list of VLANs allowed with ``switchport trunk allowed vlan x,y,z``.

        **Caution:** This does not mean the interface is necessarily a trunk port.

        Returns:
            list: Expanded list of allowed VLANs

            Returns ``None`` if absent

            Returns "none" if ``switchport trunk allowed vlan none``

        """
        candidates = self.re_search_children(regex=self._trunk_allowed_vlans_regex, group="allowed_vlans")
        if len(candidates):
            if len(candidates) == 1:
                # In case all VLANs are disabled - "switchport trunk allowed vlan none"
                if candidates[0] == "none":
                    return "none"

            self.logger.debug("Interface [{}]".format(self.name))
            candidates = ",".join(candidates)
            crange = CiscoRange(text=candidates)
            return crange._list
        else:
            return None

    @property
    @functools.lru_cache()
    def access_vlan(self):
        """
        Return a number of access VLAN or `None` if the command ``switchport access vlan x`` is not present.

        **Caution:** This does not mean the interface is necessarily an access port.

        Returns:
            int: Number of access VLAN or None

            Returns ``None`` if absent

        """
        access_vlan = None
        candidates = self.re_search_children(regex=self._access_vlan_regex, group="access_vlan")
        if len(candidates):
            access_vlan = int(candidates[0])
        return access_vlan

    @property
    @functools.lru_cache()
    def voice_vlan(self):
        """
        Return a number of voice VLAN

        Returns:
            int: Number of voice VLAN or None

            Returns ``None`` if absent

        """
        voice_vlan = None
        candidates = self.re_search_children(regex=self._voice_vlan_regex, group="voice_vlan")
        if len(candidates):
            voice_vlan = int(candidates[0])
        return voice_vlan

    @property
    @functools.lru_cache()
    def channel_group(self):
        """
        Return a dictionary describing Port-channel/Etherchannel related configuration

        Returns:
            dict: Channel-group parameters

            Example::

                {"channel_group_number": "1", "channel_group_mode": "active"}

            Otherwise returns ``None``

        """
        channel_group = None
        candidates = self.re_search_children(regex=self._channel_group_regex, group="ALL")
        if len(candidates):
            channel_group = candidates[0]
        return channel_group

    @property
    @functools.lru_cache()
    def speed(self):
        """
        Return speed of the interface set by command **speed X**

        Returns:
            int: Speed

            Returns ``None`` if absent

        """
        speed = None
        candidates = self.re_search_children(regex=self._speed_regex, group="speed")
        if len(candidates):
            speed = int(candidates[0])
        return speed

    @property
    @functools.lru_cache()
    def duplex(self):
        """
        Return duplex of the interface set by command **duplex X**.

        Returns:
            str: Duplex

            Returns ``None`` if absent

        """
        duplex = None
        candidates = self.re_search_children(regex=self._duplex_regex, group="duplex")
        if len(candidates):
            duplex = candidates[0]
        return duplex

    @property
    @functools.lru_cache()
    def bandwidth(self):
        """
        Return bandwidth of the interface set by command **bandwidth X**.

        Returns:
            int: Bandwidth

            Returns ``None`` if absent

        """
        bandwith = None
        candidates = self.re_search_children(regex=self._bandwidth_regex, group="bandwidth")
        if len(candidates):
            bandwith = candidates[0]
        return bandwith

    @property
    @functools.lru_cache()
    def delay(self):
        """
        Return delay of the interface set by command **delay X**.

        Returns:
            int: Delay

            Returns ``None`` if absent

        """
        delay = None
        candidates = self.re_search_children(regex=self._delay_regex, group="delay")
        if len(candidates):
            delay = candidates[0]
        return delay

    @property
    @functools.lru_cache()
    def mtu(self):
        """
        Return MTU of the interface set by command **mtu X**.

        Returns:
            int: MTU

            Returns ``None`` if absent

        """
        mtu = None
        candidates = self.re_search_children(regex=self._mtu_regex, group="mtu")
        if len(candidates):
            mtu = int(candidates[0])
        return mtu

    @property
    @functools.lru_cache()
    def ip_mtu(self):
        """
        Return IP MTU of the interface set by command **ip mtu X**.

        Returns:
            int: IP MTU

            Returns ``None`` if absent

        """
        ip_mtu = None
        candidates = self.re_search_children(regex=self._ip_mtu_regex, group="ip_mtu")
        if len(candidates):
            ip_mtu = int(candidates[0])
        return ip_mtu

    @property
    @functools.lru_cache()
    def tcp_mss(self):
        """
        Return TCP Max Segment Size of the interface set by command **ip tcp adjust-mss X**.

        Returns:
            int: TCP MSS

            Returns ``None`` if absent

        """
        tcp_mss = None
        candidates = self.re_search_children(regex=self._ip_tcp_mss_regex, group="tcp_mss")
        if len(candidates):
            tcp_mss = int(candidates[0])
        return tcp_mss

    @property
    @functools.lru_cache()
    def load_interval(self):
        """
        Return Load Interval of the interface set by command **load-interval X**.

        Returns:
            int: Load Interval

            Returns ``None`` if absent

        """
        load_interval = None
        candidates = self.re_search_children(regex=self._load_interval_regex, group="load_interval")
        if len(candidates):
            load_interval = int(candidates[0])
        return load_interval

    @property
    @functools.lru_cache()
    def keepalive(self):
        keepalive = None
        candidates = self.re_search_children(regex=self._keepalive_regex, group="ALL")
        if len(candidates):
            keepalive = {k: int(v) for k, v in candidates[0].items()}
        return keepalive

    @property
    @functools.lru_cache()
    def negotiation(self):
        negotiation = None
        candidates = self.re_search_children(regex=self._negotiation_regex, group="negotiation")
        if len(candidates):
            negotiation = candidates[0]
        return negotiation

    @property
    @functools.lru_cache()
    def service_policy(self):
        """
        Return names of applied service policies

        Returns:
            dict: Dictionary containing names of both input and output policies.

            Example::

                {"input": "TEST_INPUT_POLICY", "output": "TEST_OUTPUT_POLICY"}

            If there are no policies specified, returns::

                {"input": None, "output": None}


        """
        service_policy = {"input": None, "output": None}
        candidates = self.re_search_children(regex=self._service_policy_regex, group="ALL")
        for candidate in candidates:
            if candidate["direction"] == "input":
                service_policy["input"] = candidate["policy_map"]
            elif candidate["direction"] == "output":
                service_policy["output"] = candidate["policy_map"]
        # print(candidates)
        return service_policy

    @property
    @functools.lru_cache()
    def service_instances(self):
        service_instances = None
        service_instance_candidates = self.re_search_children(regex=self._service_instance_regex)
        self.logger.debug("Interface {}: Service Instances Lines: {}".format(self.name, service_instance_candidates))
        if len(service_instance_candidates):
            service_instances = {}
        for service_instance_line in service_instance_candidates:
            match_dict = service_instance_line.re_search(regex=self._service_instance_regex, group="ALL")
            instance_number = int(match_dict["number"])
            service_instances[instance_number] = {"type": match_dict["type"]}

            # Description
            description_candidates = service_instance_line.re_search_children(regex=self._service_instance_description_regex, group="description")
            if len(description_candidates):
                service_instances[instance_number]["description"] = description_candidates[0]

            # Encapsulation
            # Try the mapping variant first
            encapsulation_candidates = service_instance_line.re_search_children(regex=self._service_instance_encapsulation_mapping_regex, group="ALL")
            if len(encapsulation_candidates):
                service_instances[instance_number]["encapsulation"] = {"type": encapsulation_candidates[0]["type"], "tag": int(encapsulation_candidates[0]["tag"])}
            else:
                # Fallback to string variant
                encapsulation_candidates = service_instance_line.re_search_children(regex=self._service_instance_encapsulation_string_regex, group="ALL")
                if len(encapsulation_candidates):
                    service_instances[instance_number]["encapsulation"] = encapsulation_candidates[0]["encapsulation"]

            # Bridge Domain
            bd_candidates = service_instance_line.re_search_children(regex=self._service_instance_bridge_domain_regex, group="number")
            if len(bd_candidates):
                service_instances[instance_number]["bridge_domain"] = int(bd_candidates[0])

            # Service Policy
            service_policy_candidates = service_instance_line.re_search_children(regex=self._service_instance_service_policy_regex, group="ALL")
            if len(service_policy_candidates):
                service_instances[instance_number]["service_policy"] = {"input": None, "output": None}
                for candidate in service_policy_candidates:
                    if candidate["direction"] == "input":
                        service_instances[instance_number]["service_policy"]["input"] = candidate["policy_map"]
                    elif candidate["direction"] == "output":
                        service_instances[instance_number]["service_policy"]["output"] = candidate["policy_map"]

            # Service Instance Shutdown
            shutdown_candidates = service_instance_line.re_search_children(regex=self._service_instance_shutdown_regex)
            if len(shutdown_candidates) == 1:
                service_instances[instance_number]["shutdown"] = True
            elif len(shutdown_candidates) == 0:
                service_instances[instance_number]["shutdown"] = False

            # SNMP Traps
            snmp_trap_candidates = service_instance_line.re_search_children(regex=self._service_instance_snmp_trap_regex, group="trap")
            if len(snmp_trap_candidates):
                service_instances[instance_number]["snmp_traps"] = snmp_trap_candidates

            check_patterns = [
                self._service_instance_description_regex,
                self._service_instance_encapsulation_mapping_regex,
                self._service_instance_encapsulation_string_regex,
                self._service_instance_bridge_domain_regex,
                self._service_instance_service_policy_regex,
                re.compile(pattern="^  (?:no )?shutdown"),
                self._service_instance_snmp_trap_regex
            ]
            unprocessed_lines = [x.text for x in self.config.section_unprocessed_lines(parent=service_instance_line, check_patterns=check_patterns)]
            if len(unprocessed_lines):
                service_instances[instance_number]["unprocessed_lines"] = unprocessed_lines




        # print(service_instances)
        return service_instances

    @property
    @functools.lru_cache()
    def tunnel_properties(self):
        """
        Return properties related to Tunnel interfaces

        Returns:
            dict: Dictionary with tunnel properties.

            Example::

                {
                    "source": "Loopback0",
                    "destination": "10.0.0.1",
                    "vrf": None,
                    "mode": "ipsec ipv4",
                    "ipsec_profile": "TEST_IPSEC_PROFILE"
                }

            Returns ``None`` if absent

        """
        # Check if interface is a Tunnel
        if not re.match(pattern=r"^Tu", string=self.name):
            return None
        else:
            tunnel_properties = {}
            tunnel_src_candidates = self.re_search_children(regex=self._tunnel_src_regex, group="source")
            tunnel_dest_candidates = self.re_search_children(regex=self._tunnel_dest_regex, group="destination")
            tunnel_vrf_candidates = self.re_search_children(regex=self._tunnel_vrf_regex, group="vrf")
            tunnel_mode_candidates = self.re_search_children(regex=self._tunnel_mode_regex, group="mode")
            tunnel_ipsec_profile_candidates = self.re_search_children(regex=self._tunnel_ipsec_profile_regex, group="ipsec_profile")
            tunnel_properties["source"] = tunnel_src_candidates[0] if tunnel_src_candidates else None
            tunnel_properties["destination"] = tunnel_dest_candidates[0] if tunnel_dest_candidates else None
            tunnel_properties["vrf"] = tunnel_vrf_candidates[0] if tunnel_vrf_candidates else None
            tunnel_properties["mode"] = tunnel_mode_candidates[0] if tunnel_mode_candidates else None
            tunnel_properties["ipsec_profile"] = tunnel_ipsec_profile_candidates[0] if tunnel_ipsec_profile_candidates else None
            return tunnel_properties

    @property
    @functools.lru_cache()
    def storm_control(self):
        threshold_candidates = self.re_search_children(regex=self._storm_control_threshold_regex, group="ALL")
        action_candidates = self.re_search_children(regex=self._storm_control_action_regex, group="action")
        if len(threshold_candidates) == 0 and len(action_candidates) == 0:
            return None
        storm_control = {"thresholds": None, "action": None}
        if len(threshold_candidates):
            storm_control["thresholds"] = threshold_candidates
        if len(action_candidates):
            storm_control["action"] = action_candidates[0]
        return storm_control

    @property
    @functools.lru_cache()
    def device_tracking_policy(self):
        device_tracking_policy = None
        candidates = self.re_search_children(regex=self._device_tracking_attach_policy_regex, group="policy")
        if len(candidates):
            device_tracking_policy = candidates[0]
        return device_tracking_policy
    @property
    @functools.lru_cache()
    def dhcp_snooping(self):
        dhcp_snooping = {"trust": None}
        trust_candidates = self.re_search_children(regex=self._ip_dhcp_snooping_trust_regex)
        if len(trust_candidates):
            dhcp_snooping["trust"] = True

        if self.config.minimal_results:
            if not any(dhcp_snooping.values()):
                dhcp_snooping = None

        return dhcp_snooping



