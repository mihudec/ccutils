## Version 0.2.18
**Release Date:** 10-03-2021

### Minor Changes
Changed structure of `CiscoIosInterface.standby`, along with some new keys

### Deprecation Warnings
`CiscoIosInterface.ip_addresses` deprecated by `CiscoIosInterface.ipv4_addresses`

`CiscoIosInterface.ip_unnumbered` deprecated by `CiscoIosInterface.ipv4_unnumbered`

## Version 0.2.16
**Release Date:** 02-12-2020

### BugFixes

 - Some configuration lines were missing from `CiscoIosInterface.get_unprocessed()`
 - `utils.common_utils.get_logger` used Formatter which did not show logger name

### New Functions

#### CiscoIosParser.vlan_groups
Returns list of VLAN groups, such as 
```python
[
  {
    "group": "GROUP01", 
    "vlan_id": "1"
  },
  {
    "group": "GROUP02",
    "vlan_id": "2"
  }
]
```
#### CiscoIosInterface.dhcp_snooping
*Note: This is just a quick one for specific use case. Currently only checks if interface is trusted (containing `ip dhcp snooping trust` child)*

In the future will return all info regarding DHCP Snooping on interface level. Currently only returns dict
```python
{
  "trust": True
}
```
or `None`
