import pathlib
from ccutils.utils.common_utils import get_logger, load_excel_sheet, jprint, split_interface_name
from ccutils.ccparser import BaseConfigParser, ConfigToJson
import json


class ConfigMigration:
    def __init__(self, hostname, excel_path, excel_sheet, old_config_folder, verbosity=1):
        self.hostname = hostname
        self.logger = get_logger(name="ConfigMigration - {}".format(self.hostname), verbosity=verbosity)
        self.old_config_folder = old_config_folder if isinstance(old_config_folder, pathlib.Path) else pathlib.Path(old_config_folder)
        self.excel_data = load_excel_sheet(file=excel_path, sheet_name=excel_sheet)
        if not self.excel_data:
            self.logger.error(msg="Could not load Excel Data")
        self.old_hostnames = self.get_old_hostnames()
        self.old_configs = None
        self.old_ctj = None
        self.interface_map = self.get_interface_mapping()

        self.get_old_configs()
        self.get_old_ctj()


    def get_old_hostnames(self, column="Old Host"):
        old_hosts = set()
        if self.excel_data:
            try:
                for old_host in filter(lambda x: bool(x), self.excel_data[column]):
                    old_hosts.add(old_host)
            except Exception as e:
                self.logger.error(msg="Could not retrieve Old Hostnames from Excel Table. Reason: Unkown. Exception: {}".format(repr(e)))
        else:
            self.logger.error(msg="Could not retrieve Old Hostnames from Excel Table. Reason: File not loaded.")
        return list(old_hosts)
    
    def get_interface_mapping(self):
        interface_map = {}
        for new_interface in filter(lambda x: bool(x), self.excel_data["New Interface"]):
            i = self.excel_data["New Interface"].index(new_interface)
            if self.excel_data["Old Interface"][i] and self.excel_data["Old Host"][i]:
                #print("{} maps to {} on {}".format(new_interface, self.excel_data["Old Interface"][i], self.excel_data["Old Host"][i]))
                interface_map[new_interface] = [self.excel_data["Old Host"][i], self.excel_data["Old Interface"][i]]
            else:
                interface_map[new_interface] = None
        return interface_map


    def get_old_configs(self):
        old_configs = {}
        for old_hostname in self.old_hostnames:
            file_candidates = list(filter(lambda x: old_hostname in x.stem, self.old_config_folder.iterdir()))
            if len(file_candidates) == 1:
                self.logger.info(msg="Found config file for hostname: {}".format(old_hostname))
                old_configs[old_hostname] = BaseConfigParser(filepath=file_candidates[0])
            elif len(file_candidates) == 0:
                self.logger.error(msg="Could not find config file for hostname: {}".format(old_hostname))
            else:
                self.logger.error(msg="Found multiple configs for hostname: {}".format(old_hostname))
        self.old_configs = old_configs

    def get_old_ctj(self):
        old_ctj = {}
        for old_hostname, config in self.old_configs.items():
            old_ctj[old_hostname] = ConfigToJson(config=config)
        self.old_ctj = old_ctj


    def get_new_interface(self, old_host, old_interface):
        new_interface = None
        if old_interface in self.old_ctj[old_host].data["interfaces"].keys():
            self.logger.debug(msg="Requested interface {} exists in config of host {}".format(old_interface, old_host))
        candidates = [x for x in self.interface_map.keys() if (self.interface_map[x] and (self.interface_map[x][0] == old_host and self.interface_map[x][1] == old_interface))]
        if len(candidates) == 1:
            new_interface = candidates[0]
            self.logger.debug(msg="New interface for {} / {} is {}".format(old_host, old_interface, new_interface))
        else:
            self.logger.error(msg="No mapping for interface found. ({} / {})".format(old_host, old_interface))
        return new_interface


    def get_context_for_new_interface(self, new_interface):
        old_interface = None
        old_host = None
        new_interface_context = None
        if new_interface not in self.interface_map.keys():
            self.logger.error(msg="No such New Interface Exists: {}".format(new_interface))
            
        elif not self.interface_map[new_interface]:
            self.logger.warning(msg="No Old Interface exists for New Interface: {}".format(new_interface))
            
        else:
            old_host = self.interface_map[new_interface][0]
            old_interface = self.interface_map[new_interface][1]
            old_interface_context = self.old_ctj[old_host].data["interfaces"][old_interface]
            # Replace Etherchannel group Number
            if old_interface_context["channel_group"]:
                old_channel_group_number = old_interface_context["channel_group"]["channel_group_number"]
                old_portchannel = "Port-channel{}".format(old_channel_group_number)
                new_portchannel = self.get_new_interface(old_host=old_host, old_interface=old_portchannel)
                if new_portchannel:
                    new_channel_group_number = split_interface_name(new_portchannel)[1]
                    new_interface_context = old_interface_context
                    new_interface_context["channel_group"]["channel_group_number"] = new_channel_group_number
                else:
                    self.logger.error(msg="Could not determine new Port-channel number. No replacement for interface {} / {} exists.".format(old_host, old_portchannel))
                    
            else:
                new_interface_context = old_interface_context
        return new_interface_context


    def check_standby(self):
        groups = {}
        for old_hostname, old_ctj in self.old_ctj.items():
            for interface, params in old_ctj.data["interfaces"].items():
                if "standby" in params["flags"]:
                    for group in params["l3"]["standby"]["groups"].keys():
                        if group not in groups.keys():
                            groups[group] = []
                        groups[group] += old_hostname, interface, params["l3"]["standby"]["groups"][group]["priority"]
        
        for group, value in groups.items():
            line = [group]
            for hostname in self.old_hostnames:
                if hostname in value:
                    line += value[value.index(hostname)], value[value.index(hostname)+1]
                else:
                    line += "", ""

            print(";".join(line))
    
    def user_selection(self, prompt, options):
        result = int(input(prompt))
        return options[result]

    def merge_vlans(self):
        vlans = {}
        for hostname, old_ctj in self.old_ctj.items():
            for vlan, params in old_ctj.data["vlans"].items():
                if vlan not in vlans.keys():
                    vlans[vlan] = params
                    self.logger.debug(msg="Added new VLAN: {} '{}'".format(vlan, params["name"]))
                else:
                    if vlans[vlan]["name"] == params["name"]:
                        pass
                    elif vlans[vlan]["name"] != params["name"]:
                        if not vlans[vlan]["name"]:
                            vlans[vlan]["name"] = params["name"]
                            self.logger.debug(msg="Renamed VLAN {} to '{}'".format(vlan, params["name"]))
                        elif not params["name"]:
                            pass
                        else: 
                            options = {1: vlans[vlan]["name"], 2: params["name"]}
                            result = self.user_selection(prompt="Found two diffenet names for same VLAN {}: {}:\n".format(vlan, options), options=options)
                            vlans[vlan]["name"] = result
        
        return vlans
    
    def merge_vrfs(self):
        vrfs = {}
        for hostname, old_ctj in self.old_ctj.items():
            self.logger.info(msg="Proccessing VRFs on {}".format(hostname))
            for vrf, params in old_ctj.data["vrfs"].items():
                if vrf not in vrfs.keys():
                    vrfs[vrf] = params
                    self.logger.debug(msg="Added new VRF: {}".format(vrf))
                else:
                    self.logger.info(msg="VRF {} exists.".format(vrf))
                    if vrfs[vrf]["rd"] == params["rd"]:
                        self.logger.info(msg="VRF has same RD.")
                        pass
                    elif vrfs[vrf]["rd"] != params["rd"]:
                        self.logger.info(msg="VRF does NOT have same RD.")
                        if not vrfs[vrf]["rd"]:
                            vrfs[vrf]["rd"] = params["rd"]
                        elif not params["rd"]:
                            pass
                        else:
                            options = {1: vrfs[vrf]["rd"], 2: params["rd"]}
                            result = self.user_selection(prompt="Found two diffenet RDs for same VRF {}: {}:\n".format(vrf, options), options=options)
                            vrfs[vrf]["rd"] = result
                    
                    if vrfs[vrf]["description"] == params["description"]:
                        pass
                    elif vrfs[vrf]["description"] != params["description"]:
                        if not vrfs[vrf]["description"]:
                            vrfs[vrf]["description"] = params["description"]
                        elif not params["description"]:
                            pass
                        else:
                            options = {1: vrfs[vrf]["description"], 2: params["description"]}
                            result = self.user_selection(prompt="Found two diffenet descriptions for same VRF {}: {}:\n".format(vrf, options), options=options)
                            vrfs[vrf]["description"] = result

        with pathlib.Path(r"C:\Users\mhudec\CloudStation\Work\ALEF\MHMP\MHMP_Migrations\CONFIG\NEW\6500\vrfs.json").open(mode="w") as f:
            json.dump(obj=vrfs, fp=f, indent=2)
        return vrfs




if __name__ == "__main__":
    cm = ConfigMigration(
        hostname="NUB-SW-COR-001", 
        excel_path=r"C:\Users\mhudec\CloudStation\Work\ALEF\MHMP\MHMP_Migrations\EXCEL\NUB_6500_Ports.xlsx", 
        excel_sheet="Port Mappings",
        old_config_folder=r"C:\Users\mhudec\CloudStation\Work\ALEF\MHMP\MHMP_Migrations\CONFIG\OLD\NUB",
        verbosity=2
    )
    #cm.check_standby()
    #cm.merge_vrfs()
    #cm.get_interface_mapping()
    for interface in filter(lambda x: bool(cm.old_ctj["gw1-serv"].data["interfaces"][x]["channel_group"]), cm.old_ctj["gw1-serv"].data["interfaces"].keys()):
        new_interface = cm.get_new_interface(old_host="gw1-serv", old_interface=interface)
        if new_interface:
            print(interface, cm.old_ctj["gw1-serv"].data["interfaces"][interface]["channel_group"]["channel_group_number"])
            print(cm.get_context_for_new_interface(cm.get_new_interface(old_host="gw1-serv", old_interface=interface))["channel_group"]["channel_group_number"])

   
    
            
    