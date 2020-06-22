from ccutils.ccparser import BaseConfigParser
from ccutils.ccparser import CiscoIosInterfaceLine
from ccutils.utils import CiscoRange
from ccutils.utils.common_utils import remove_empty_values, value_to_bool
import functools
import re


class CiscoIosParser(BaseConfigParser):

    INTERFACE_LINE_CLASS = CiscoIosInterfaceLine


    # Regexes
    _interface_pattern = r"[A-z]{2,}(?:[A-z\-])?\d+(?:\/\d+)?(?:\:\d+)?(?:\.\d+)?"
    _ip_address_pattern = r"(?:\d{1,3}\.){3}\d{1,3}"
    _host_pattern = r"[A-z0-9\-\_\.]+"
    _acl_name = r"[A-z0-9\_\-\.]+"

    _vlan_configuration_regex = re.compile(pattern=r"^vlan configuration (?P<vlan_range>[\d\-,]+)", flags=re.MULTILINE)
    _device_tracking_attach_policy_regex = re.compile(pattern=r"^ device-tracking attach-policy (?P<policy>\S+)")

    _source_interface_regex = re.compile(pattern=r"source (?P<source_interface>{0})".format(_interface_pattern))
    _source_vrf_regex = re.compile(pattern=r"vrf (?P<vrf>\S+)")

    _name_server_base_regex = re.compile(pattern=r"^ip name.server (?P<name_servers>(?:\d{1,3}\.){3}\d{1,3}(?: (?:\d{1,3}\.){3}\d{1,3})*)", flags=re.MULTILINE)

    _ntp_server_base_regex = re.compile(pattern=r"^ntp server(?: vrf \S+)? (?P<server>{0}|{1})".format(_ip_address_pattern, _host_pattern))
    _ntp_peer_base_regex = re.compile(pattern=r"^ntp peer(?: vrf \S+)? (?P<server>{0}|{1})".format(_ip_address_pattern, _host_pattern))
    _ntp_access_group_regex = re.compile(pattern=r"^ntp access-group (?P<access_type>peer|serve|serve-only|query-only) (?P<acl>{0})".format(_acl_name))
    _ntp_authentication_keys_regex = re.compile(pattern=r"^ntp authentication-key (?P<key>\d+) (?P<hash_algorithm>\S+) (?P<hash>\S+)(?: (?P<encryption_type>\d+))?".format(_acl_name))
    _ntp_trusted_key_regex = re.compile(pattern=r"ntp trusted-key (?P<key>\d+)")
    _ntp_source_regex = re.compile(pattern="^ntp source (?P<source>{0})".format(_interface_pattern))


    _logging_server_base_regex = re.compile(pattern=r"^logging host (?P<server>{0}|{1})".format(_ip_address_pattern, _host_pattern))
    _logging_transport_regex = re.compile(pattern=r"transport (?P<protocol>udp|tcp) port (?P<port>\d+)")

    _tacacs_server_regex = re.compile(pattern=r"^tacacs server (?P<name>\S+)")
    _radius_server_regex = re.compile(pattern=r"^radius server (?P<name>\S+)")

    _radius_auth_port_regex = re.compile(pattern=r"auth-port (?P<auth_port>\d+)")
    _radius_acct_port_regex = re.compile(pattern=r"acct-port (?P<acct_port>\d+)")

    _aaa_radius_group_regex = re.compile(pattern=r"^aaa group server radius (?P<name>\S+)")
    _aaa_tacacs_group_regex = re.compile(pattern=r"^aaa group server tacacs\+ (?P<name>\S+)")

    _aaa_group_server_name_regex = re.compile(pattern=r"^ server name (?P<name>\S+)")
    _aaa_group_vrf_regex = re.compile(pattern=r"^ ip vrf forwarding (?P<vrf>\S+)")
    _aaa_group_source_interface_regex = re.compile(pattern=r"^ ip (?:tacacs|radius) source-interface (?P<source_interface>{0})".format(_interface_pattern))

    _aaa_server_address_regex = re.compile(pattern=r"^ address (?P<address_version>ipv4|ipv6) (?P<server>\S+)")
    _aaa_server_key_regex = re.compile(pattern=r"^ key(?: (?P<encryption_type>\d+))? (?P<hash>\S+)")
    _aaa_server_timeout_regex = re.compile(pattern=r"^ timeout (?P<timeout>\d+)")
    _aaa_server_retransmit_regex = re.compile(pattern=r"^ retransmit (?P<retransmit>\d+)")
    _aaa_server_single_connection = re.compile(pattern=r"^ (?P<single_connection>single-connection)")

    _aaa_method_group_regex = re.compile(pattern=r"(?:group \S+)|local|radius|tacacs\+")
    _aaa_authentication_base_regex = re.compile(pattern=r"^aaa authentication login (?P<name>)")

    def __init__(self, config=None, verbosity=4, **kwargs):
        super(CiscoIosParser, self).__init__(config=config, verbosity=verbosity, **kwargs)

    @property
    @functools.lru_cache()
    def hostname(self):
        hostname = None
        regex = r"^hostname\s(\S+)"
        candidates = self.find_objects(regex=regex)
        if len(candidates):
            hostname = candidates[0].re_search(regex=regex, group=1)
        return hostname

    @property
    @functools.lru_cache()
    def cdp(self):
        if len(self.find_objects(regex="^no cdp run")):
            return False
        else:
            return True

    @property
    def domain_name(self):
        domain_name = None
        domain_name_regex = re.compile(pattern=r"^ip domain.name (?P<domain_name>\S+)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=domain_name_regex)
        if len(candidates):
            domain_name = candidates[0].re_search(regex=domain_name_regex, group="domain_name")
        return domain_name

    @property
    @functools.lru_cache()
    def name_servers(self):
        name_servers = None
        candidates = self.find_objects(regex=self._name_server_base_regex)
        if len(candidates):
            name_servers = []
        else:
            return name_servers
        for candidate in candidates:
            name_servers.extend(re.findall(pattern=r"(?:\d{1,3}\.){3}\d{1,3}", string=candidate.text))
        return name_servers

    @property
    @functools.lru_cache()
    def ntp_servers(self):
        """
        Property containing DNS servers related data

        Returns:
            list: List of name server IP addresses

            Example::

                [
                    "10.0.0.1",
                    "10.0.0.2"
                ]

            Returns ``None`` if absent


        """
        candidate_pattern = self._ntp_server_base_regex
        patterns = [
            self._ntp_server_base_regex,
            self._source_interface_regex,
            self._source_vrf_regex,
            re.compile("key (?P<key>\d+)"),
            re.compile("(?P<prefer>prefer)")
        ]
        ntp_servers = self.property_autoparse(candidate_pattern=candidate_pattern, patterns=patterns)
        if ntp_servers is not None:
            for server in ntp_servers:
                server = value_to_bool(entry=server, keys=["prefer"])
        return ntp_servers

    @property
    @functools.lru_cache()
    def ntp_peers(self):
        candidate_pattern = self._ntp_peer_base_regex
        patterns = [
            self._ntp_peer_base_regex,
            self._source_interface_regex,
            self._source_vrf_regex,
            re.compile("key (?P<key>\d+)")
        ]
        ntp_peers = self.property_autoparse(candidate_pattern=candidate_pattern, patterns=patterns)
        return ntp_peers

    @property
    @functools.lru_cache()
    def ntp_access_groups(self):
        ntp_access_groups = None
        candidate_pattern = self._ntp_access_group_regex
        candidates = self.find_objects(regex=candidate_pattern)
        if len(candidates):
            ntp_access_groups = {"peer": None, "serve": None, "serve-only": None, "query-only": None}
        else:
            return ntp_access_groups
        for candidate in candidates:
            match_result = candidate.re_search(regex=candidate_pattern, group="ALL")
            if match_result is not None:
                ntp_access_groups.update({match_result["access_type"]: match_result["acl"]})
        return ntp_access_groups

    @property
    @functools.lru_cache()
    def ntp_authentication_keys(self):
        candidate_pattern = self._ntp_authentication_keys_regex
        patterns = [
            self._ntp_authentication_keys_regex
        ]
        ntp_authentication_keys = self.property_autoparse(candidate_pattern=candidate_pattern, patterns=patterns)
        return ntp_authentication_keys

    @property
    @functools.lru_cache()
    def ntp_trusted_keys(self):
        candidate_pattern = self._ntp_trusted_key_regex
        patterns = [
            self._ntp_trusted_key_regex
        ]
        ntp_trusted_keys = self.property_autoparse(candidate_pattern=candidate_pattern, patterns=patterns)
        return ntp_trusted_keys

    @property
    @functools.lru_cache()
    def ntp_global_params(self):
        ntp_global_params = {
            "source": None,
            "authenticate": None
        }
        source_candidates = self.find_objects(regex=self._ntp_source_regex)
        if len(source_candidates) == 1:
            ntp_global_params["source"] = source_candidates[0].re_search(regex=self._ntp_source_regex, group="source")

        authenticate_candidates = self.find_objects(regex=r"^ntp authenticate$")
        if len(authenticate_candidates):
            ntp_global_params["authenticate"] = True
        return ntp_global_params

    @property
    @functools.lru_cache()
    def ntp(self):
        ntp = {}
        ntp.update(self.ntp_global_params)
        ntp["servers"] = self.ntp_servers
        ntp["peers"] = self.ntp_peers
        ntp["access_groups"] = self.ntp_access_groups
        ntp["authentication_keys"] = self.ntp_authentication_keys
        ntp["trusted_keys"] = self.ntp_trusted_keys
        is_empty = True
        for value in ntp.values():
            if value is not None:
                is_empty = False
        if is_empty:
            ntp = None
        return ntp

    @property
    @functools.lru_cache()
    def logging_servers(self):
        candidate_pattern = self._logging_server_base_regex
        patterns = [
            self._logging_server_base_regex,
            self._source_interface_regex,
            self._source_vrf_regex,
            self._logging_transport_regex
        ]
        logging_servers = self.property_autoparse(candidate_pattern=candidate_pattern, patterns=patterns)
        return logging_servers

    @property
    @functools.lru_cache()
    def tacacs_servers(self):
        """

        Returns:
            list: List of TACACS Servers

            Example::

                [
                    {
                      "name": "ISE-1",
                      "address_version": "ipv4",
                      "server": "10.0.0.1",
                      "encryption_type": "7",
                      "hash": "36A03A8A4C00E81F03D62D8B04BBBF4D",
                      "timeout": "10",
                      "single_connection": true
                    },
                    {
                      "name": "ISE-2",
                      "address_version": "ipv4",
                      "server": "10.0.1.1",
                      "encryption_type": "7",
                      "hash": "36A03A8A4C00E81F03D62D8B04BBBF4D",
                      "timeout": "10",
                      "single_connection": true
                    }
                ]

            Returns ``None`` if absent


        """
        patterns = [
            self._aaa_server_address_regex,
            self._aaa_server_key_regex,
            self._aaa_server_timeout_regex,
            self._aaa_server_retransmit_regex,
            self._aaa_server_single_connection
        ]
        tacacs_servers = self.section_property_autoparse(candidate_pattern=self._tacacs_server_regex, patterns=patterns)
        if tacacs_servers is not None:
            for entry in tacacs_servers:
                entry = value_to_bool(entry=entry, keys=["single_connection"])
        return tacacs_servers

    @property
    @functools.lru_cache()
    def radius_servers(self):
        """

        Returns:
            list: List of RADIUS Servers

            Example::

                [
                    {
                      "name": "RADIUS-Primary",
                      "address_version": "ipv4",
                      "server": "10.0.0.1",
                      "encryption_type": null,
                      "hash": "Test123",
                      "timeout": "2",
                      "retransmit": "1",
                      "auth_port": "1812",
                      "acct_port": "1813"
                    },
                    {
                      "name": "RADIUS-Secondary",
                      "address_version": "ipv4",
                      "server": "10.0.1.1",
                      "encryption_type": null,
                      "hash": "Test123",
                      "timeout": "2",
                      "retransmit": "1",
                      "auth_port": "1812",
                      "acct_port": "1813"
                    }
                ]

            Returns ``None`` if absent

        """
        patterns = [
            self._aaa_server_address_regex,
            self._aaa_server_key_regex,
            self._aaa_server_timeout_regex,
            self._aaa_server_retransmit_regex,
            self._aaa_server_single_connection,
            self._radius_auth_port_regex,
            self._radius_acct_port_regex
        ]
        radius_servers = self.section_property_autoparse(candidate_pattern=self._radius_server_regex, patterns=patterns)
        if radius_servers is not None:
            for entry in radius_servers:
                entry = value_to_bool(entry=entry, keys=["single_connection"])
        return radius_servers

    @property
    @functools.lru_cache()
    def tacacs_groups(self):
        """

        Returns:
            list: List of TACACS Server entries

            Example::

                [
                    {
                        "name": "ISE-TACACS",
                        "source_interface": "Loopback0",
                        "servers": [
                            {
                                "name": "ISE-1"
                            },
                            {
                                "name": "ISE-2"
                            }
                        ]
                    }
                ]

            Returns ``None`` if absent

        """
        patterns = [
            self._aaa_group_vrf_regex,
            self._aaa_group_source_interface_regex,
        ]
        tacacs_groups = self.section_property_autoparse(candidate_pattern=self._aaa_tacacs_group_regex, patterns=patterns)
        if tacacs_groups is not None:
            candidates = self.find_objects(regex=self._aaa_tacacs_group_regex)
            for candidate in candidates:
                name = candidate.re_search(regex=self._aaa_tacacs_group_regex, group="name")
                servers = candidate.re_search_children(regex=self._aaa_group_server_name_regex, group="ALL")
                for tacacs_group in tacacs_groups:
                    if tacacs_group["name"] == name:
                        tacacs_group["servers"] = servers
        return tacacs_groups

    @property
    @functools.lru_cache()
    def radius_groups(self):
        """

        Returns:
            list: List of RADIUS Server Groups Entries

            Example::

                [
                    {
                        "name": "RADIUS-GROUP",
                        "source_interface": "Vlan100",
                        "servers": [
                            {
                                "name": "RADIUS-Primary"
                            }
                        ]
                    }
                ]

            Returns ``None`` if absent

        """
        patterns = [
            self._aaa_group_vrf_regex,
            self._aaa_group_source_interface_regex
        ]
        radius_groups = self.section_property_autoparse(candidate_pattern=self._aaa_radius_group_regex, patterns=patterns)
        if radius_groups is not None:
            candidates = self.find_objects(regex=self._aaa_radius_group_regex)
            for candidate in candidates:
                name = candidate.re_search(regex=self._aaa_radius_group_regex, group="name")
                servers = candidate.re_search_children(regex=self._aaa_group_server_name_regex, group="ALL")
                for radius_group in radius_groups:
                    if radius_group["name"] == name:
                        radius_group["servers"] = servers
        return radius_groups

    @property
    def vlans(self):
        vlans = {}
        # Basic VLAN Definition
        vlan_id_regex = re.compile(pattern=r"^vlan (?P<vlan_id>\d+)", flags=re.MULTILINE)
        vlan_name_regex = re.compile(pattern=r"^ name (?P<vlan_name>\S+)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=vlan_id_regex)
        for candidate in candidates:
            vlan_id = candidate.re_search(regex=vlan_id_regex, group="vlan_id")
            vlan_name = None
            vlan_name_candidate = candidate.re_search_children(regex=vlan_name_regex, group="vlan_name")
            if len(vlan_name_candidate):
                vlan_name = vlan_name_candidate[0]
            vlans[vlan_id] = {"name": vlan_name}
        # VLAN Configuration
        candidates = self.find_objects(regex=self._vlan_configuration_regex)
        for candidate in candidates:
            vlan_range = CiscoRange(candidate.re_search(regex=self._vlan_configuration_regex, group="vlan_range"))
            policy = candidate.re_search_children(regex=self._device_tracking_attach_policy_regex, group="policy")
            if len(policy):
                for vlan_id in vlan_range:
                    vlans[vlan_id]["device_tracking_policy"] = policy[0]
        return vlans

    @property
    def vlan_groups(self):
        vlan_group_regex = re.compile(pattern=r"^vlan group (?P<group>\S+) vlan-list (?P<vlan_id>\d+)",
                                      flags=re.MULTILINE)
        candidates = self.find_objects(regex=vlan_group_regex)
        return [x.re_search(regex=vlan_group_regex, group="ALL") for x in candidates]

    @property
    def vrfs(self):
        vrfs = None
        vrf_name_regex = re.compile(pattern=r"^(?:ip )?vrf(?: definition)? (?P<vrf_name>\S+)", flags=re.MULTILINE)
        rd_regex = re.compile(pattern=r"^ rd (?P<rd>\S+)", flags=re.MULTILINE)
        description_regex = re.compile(pattern=r"^ description (?P<description>.*)", flags=re.MULTILINE)
        candidates = self.find_objects(regex=vrf_name_regex)
        if len(candidates):
            vrfs = {}
        for candidate in candidates:
            vrf_name = candidate.re_search(regex=vrf_name_regex, group="vrf_name")
            if vrf_name:
                vrfs[vrf_name] = {}
            else:
                continue
            rd_candidates = candidate.re_search_children(regex=rd_regex, group="rd")
            if len(rd_candidates):
                vrfs[vrf_name]["rd"] = rd_candidates[0]
            else:
                vrfs[vrf_name]["rd"] = None
            description_candidates = candidate.re_search_children(regex=description_regex, group="description")
            if len(description_candidates):
                vrfs[vrf_name]["description"] = description_candidates[0]
            else:
                vrfs[vrf_name]["description"] = None
        return vrfs



