# Version 0.3.0 Breaking changes
Starting from v0.2.9 there are new objects, namely `CiscoIosParser` and `CiscoIosInterfaceLine` from `ccutils.ccparser`.
 These classes have all the functionality of former `BaseConfigParser` and `BaseInterfaceLine` which were *Cisco Only* up to this point.
 This means that all of the *Base** classes have been put to background and will serve only as parent objects for new 
 *\<Vendor>\<OS>Parser* and *\<Vendor>\<OS>InterfaceLine* which will come in the future releases.
 
 **From now on use the following approach for instantiating your config objects:**
 ```python
from ccutils.ccparser import ConfigParser

parser = ConfigParser(config="/path/to/file/or/string", device_type="ios")
```
Where **device-type="ios"** is the important part. `ConfigParser` is just a function returning proper class based on *device-type* parameter.
So far, the only supported device type is "ios".

Alternatively, if you are working just with IOS configs, you can use:
```python
from ccutils.ccparser import CiscoIosParser

parser = CiscoIosParser(config="/path/to/file/or/string")
```

**Starting from 0.3.0, all the functions and properties of `BaseConfigParser` and `BaseInterfaceLine` which contained 
any Cisco-related regexes/stuff will be removed.**

# Cisco Config Utils

This package provides a library to handle Cisco configuration files in a better programmatic way.

## Contained Packages
* **Cisco Config Parser**
* **Cisco Config Templater**

As the names suggest, *Cisco Config Parser* can be used to search, audit and parse existing configuration files, whereas *Cisco Config Templater* can be used to generate these configs.


# QuickStart
## Instalation 
Step 1:

``pip3 install ccutils``

Step 2: 

Check out the docs at https://ccutils.readthedocs.org


