from ccutils.ccparser import BaseConfigParser
from ccutils.ccparser import CiscoIosInterfaceLine
from ccutils.utils import CiscoRange
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

    _ntp_server_base_regex = re.compile(pattern=r"^ntp server (?P<server>{0}|{1})".format(_ip_address_pattern, _host_pattern))
    _ntp_peer_base_regex = re.compile(pattern=r"^ntp peer (?P<server>{0}|{1})".format(_ip_address_pattern, _host_pattern))
    _ntp_access_group_regex = re.compile(pattern=r"^ntp access-group (?P<access_type>peer|serve|serve-only|query-only) (?P<acl>{0})".format(_acl_name))
    _ntp_authentication_keys_regex = re.compile(pattern=r"^ntp authentication-key (?P<key>\d+) (?P<hash_algorithm>\S+) (?P<hash>\S+) (?P<number>\d+)".format(_acl_name))
    _ntp_trusted_key_regex = re.compile(pattern=r"ntp trusted-key (?P<key>\d+)")
    _ntp_source_regex = re.compile(pattern="^ntp source (?P<source>{0})".format(_interface_pattern))


    _logging_server_base_regex = re.compile(pattern=r"^logging(?: host)? (?P<server>{0}|{1})".format(_ip_address_pattern, _host_pattern))
    _logging_transport_regex = re.compile(pattern=r"transport (?P<protocol>udp|tcp) port (?P<port>\d+)")

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
            re.compile("key (?P<key>\d+)")
        ]
        ntp_servers = self.property_autoparse(candidate_pattern=candidate_pattern, patterns=patterns)
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
            "authenticate": False
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



