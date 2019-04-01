
from ccutils.ccparser import BaseConfigLine
from ccutils.utils import CiscoRange
from ccutils.utils.common_utils import get_logger
import re


class BaseInterfaceLine(BaseConfigLine):
    ip_addr_regex = re.compile(pattern=r"^\sip\saddress\s(?P<ip_address>(?:\d{1,3}\.){3}\d{1,3})\s(?P<mask>(?:\d{1,3}\.){3}\d{1,3})(?:\s(?P<secondary>secondary))?", flags=re.MULTILINE)
    description_regex = re.compile(pattern=r"^\sdescription\s(?P<description>.*)")
    vrf_regex = re.compile(pattern=r"^(?:\sip)?\svrf\sforwarding\s(?P<vrf>\S+)", flags=re.MULTILINE)
    shutdown_regex = re.compile(pattern=r"^\sshutdown", flags=re.MULTILINE)
    ospf_priority_regex = re.compile(pattern=r"^\sip\sospf\spriority\s(?P<ospf_priority>\d+)", flags=re.MULTILINE)
    cdp_regex = re.compile(pattern=r"cdp enable")
    logging_event_regex = re.compile(pattern=r"^\slogging\sevent\s(?P<logging_event>\S+)", flags=re.MULTILINE)

    standby_ip_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\sip\s(?P<ip_address>(?:\d{1,3}\.){3}\d{1,3})(?:\s(?P<secondary>secondary))?", flags=re.MULTILINE)
    standby_timers_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\stimers\s(?P<hello>\d+)\s(?P<hold>\d+)", flags=re.MULTILINE)
    standby_priority_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\spriority\s(?P<priority>\d+)", flags=re.MULTILINE)
    standby_preempt_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\s(?P<preempt>preempt)", flags=re.MULTILINE)
    standby_authentication_regex = re.compile(pattern=r"^\sstandby\s(?P<standby_group>\d+)\sauthentication\s(?P<authentication_type>md5)\skey-string\s(?P<key_type>0|7)\s(?P<key_string>\S+)", flags=re.MULTILINE)
    standby_version_regex = re.compile(pattern=r"^\sstandby\sversion\s(?P<version>2)")
    
    helper_address_regex = re.compile(pattern=r"^\sip\shelper-address\s(?P<helper_address>(?:\d{1,3}\.){3}\d{1,3})", flags=re.MULTILINE)


    native_vlan_regex = re.compile(pattern=r"^ switchport trunk native vlan (?P<native_vlan>\d+)", flags=re.MULTILINE)
    trunk_encapsulation_regex = re.compile(pattern=r"^ switchport trunk encapsulation (?P<encapsulation>dot1q|isl|negotiate)", flags=re.MULTILINE)
    switchport_mode_regex = re.compile(pattern=r"^ switchport mode (?P<switchport_mode>access|trunk|dot1q-tunnel|private-vlan)")
    trunk_allowed_vlans_regex = re.compile(pattern=r"^ switchport trunk allowed vlan(?: add)? (?P<allowed_vlans>\S+)", flags=re.MULTILINE)
    access_vlan_regex = re.compile(pattern=r"^ switchport access vlan (?P<access_vlan>\d+)", flags=re.MULTILINE)
    voice_vlan_regex = re.compile(pattern=r"^ switchport voice vlan (?P<voice_vlan>\d+)")

    channel_group_regex = re.compile(pattern=r"^ channel-group (?P<channel_group_number>\d+) mode (?P<channel_group_mode>\S+)")
    speed_regex = re.compile(pattern=r"^ speed (?P<speed>\d+)", flags=re.MULTILINE)
    duplex_regex = re.compile(pattern=r"^ duplex (?P<duplex>full|half)", flags=re.MULTILINE)

    def __init__(self, number, text, config, verbosity):
        super(BaseInterfaceLine, self).__init__(number=number, text=text, config=config, verbosity=verbosity)
        self.logger = get_logger(name="BaseInterfaceLine", verbosity=verbosity)
        

    def get_unprocessed(self, return_type=None):
        unprocessed_children = self.get_children()
        regexes = [
            self.description_regex, 
            self.ip_addr_regex, 
            self.vrf_regex, 
            self.shutdown_regex, 
            self.ospf_priority_regex,
            self.cdp_regex,
            self.logging_event_regex,
            self.standby_ip_regex,
            self.standby_timers_regex,
            self.standby_priority_regex,
            self.standby_preempt_regex,
            self.standby_authentication_regex,
            self.standby_version_regex,
            self.helper_address_regex,
            self.native_vlan_regex,
            self.trunk_encapsulation_regex,
            self.switchport_mode_regex,
            self.trunk_allowed_vlans_regex,
            self.access_vlan_regex,
            self.voice_vlan_regex,
            self.channel_group_regex,
            self.speed_regex,
            self.duplex_regex,
            re.compile(pattern=r"^\sno\sip\saddress", flags=re.MULTILINE),
            re.compile(pattern=r"^ (no )?switchport$", flags=re.MULTILINE),
            re.compile(pattern=r"^ spanning-tree portfast")
        ]
        for regex in regexes:
            for child in self.re_search_children(regex=regex):
                unprocessed_children.remove(child)
        if return_type == "text":
            return [x.text for x in unprocessed_children]

    def _val_to_bool(self, entry, key):
        if entry[key]:
            entry[key] = True
        else:
            entry[key] = False
        return entry

    @property
    def interface_name(self):
        if not self.is_interface:
            return None
        else:
            return self.re_match(self.interface_regex, group=1)

    @property
    def interface_description(self):
        if not self.is_interface:
            return None
        else:
            regex = r"description\s(.*)"
            candidates = self.re_search_children(regex=self.description_regex, group="description")
            if len(candidates) == 1:
                return candidates[0]
            else:
                return None
    
    @property
    def port_mode(self):
        if len(self.re_search_children(regex="ip address")):
            return "l3"
        else:
            return "l2"
    
    @property 
    def ip_addresses(self):
        ip_addresses = []
        candidates = self.re_search_children(regex=self.ip_addr_regex)
        for candidate in candidates:
            ip_addresses.append(self._val_to_bool(entry=candidate.re_search(regex=self.ip_addr_regex, group="ALL"), key="secondary"))
        return ip_addresses
        
    @property
    def vrf(self):
        vrf = None
        candidates = self.re_search_children(regex=self.vrf_regex, group="vrf")
        if len(candidates):
            vrf = candidates[0]
        return vrf

    @property
    def shutdown(self):
        if len(self.re_search_children(regex=self.shutdown_regex)):
            return True
        else:
            return False

    @property
    def ospf_priority(self):
        ospf_priority = None
        candidates = self.re_search_children(regex=self.ospf_priority_regex, group="ospf_priority")
        if len(candidates):
            ospf_priority = int(candidates[0])
        return ospf_priority
    
    @property
    def cdp(self):
        global_cdp = self.config.cdp
        candidates = self.re_search_children(regex=self.cdp_regex)
        if len(candidates):
            if "no" in candidates[0].text:
                return False
            else:
                return True
        else:
            return global_cdp

    @property
    def logging_events(self):
        return self.re_search_children(regex=self.logging_event_regex, group="logging_event")

    @property
    def standby(self):
        
        data = {"version": 1}
        if self.re_search_children(regex=self.standby_version_regex, group="version"):
            data["version"] = 2
        standby_ips = [self._val_to_bool(entry=x, key="secondary") for x in self.re_search_children(regex=self.standby_ip_regex, group="ALL")]
        #print(standby_ips)
        standby_timers = self.re_search_children(regex=self.standby_timers_regex, group="ALL")
        #print(standby_timers)
        standby_priority = self.re_search_children(regex=self.standby_priority_regex, group="ALL")
        #print(standby_priority)
        standby_preempt = [self._val_to_bool(entry=x, key="preempt") for x in self.re_search_children(regex=self.standby_preempt_regex, group="ALL")]
        #print(standby_preempt)
        standby_authentication = self.re_search_children(regex=self.standby_authentication_regex, group="ALL")
        #print(standby_authentication)
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
    def helper_address(self):
        helper_address = None
        candidates = self.re_search_children(regex=self.helper_address_regex, group="helper_address")
        if len(candidates):
            helper_address = candidates
        return helper_address

    @property
    def native_vlan(self):
        native_vlan = None
        candidates = self.re_search_children(regex=self.native_vlan_regex, group="native_vlan")
        if len(candidates):
            native_vlan = int(candidates[0])
        return native_vlan

    @property
    def trunk_encapsulation(self):
        trunk_encapsulation = None
        candidates = self.re_search_children(regex=self.trunk_encapsulation_regex, group="encapsulation")
        if len(candidates):
            trunk_encapsulation = candidates[0]
        return trunk_encapsulation
    
    @property
    def switchport_mode(self):
        switchport_mode = None
        candidates = self.re_search_children(regex=self.switchport_mode_regex, group="switchport_mode")
        if len(candidates):
            switchport_mode = candidates[0]
        return switchport_mode

    @property
    def trunk_allowed_vlans(self):
        
        candidates = self.re_search_children(regex=self.trunk_allowed_vlans_regex, group="allowed_vlans")
        if len(candidates):
            candidates = ",".join(candidates)
            crange = CiscoRange(text=candidates)
            return crange.compressed_list
        else:
            return None
        
    @property
    def access_vlan(self):
        access_vlan = None
        candidates = self.re_search_children(regex=self.access_vlan_regex, group="access_vlan")
        if len(candidates):
            access_vlan = int(candidates[0])
        return access_vlan

    @property
    def voice_vlan(self):
        voice_vlan = None
        candidates = self.re_search_children(regex=self.voice_vlan_regex, group="voice_vlan")
        if len(candidates):
            voice_vlan = int(candidates[0])
        return voice_vlan

    @property
    def channel_group(self):
        channel_group = None
        candidates = self.re_search_children(regex=self.channel_group_regex, group="ALL")
        if len(candidates):
            channel_group = candidates[0]
        return channel_group

    @property
    def speed(self):
        speed = None
        candidates = self.re_search_children(regex=self.speed_regex, group="speed")
        if len(candidates):
            speed = int(candidates[0])
        return speed

    @property
    def duplex(self):
        duplex = None
        candidates = self.re_search_children(regex=self.duplex_regex, group="duplex")
        if len(candidates):
            duplex = candidates[0]
        return duplex

    def __str__(self):
        return "[BaseInterfaceLine #{} ({}): '{}']".format(self.number, self.type, self.text)

    def __repr__(self):
        return self.__str__()
