============
ConfigParser
============
.. _config-parser:

-----------
Quick Start
-----------

..  code-block:: python

    from ccutils.ccparser import ConfigParser
    import pathlib

    # Optinal - Create pathlib object pointing to your config file
    path_to_file = pathlib.Path("/path/to/config_file.txt")

    config = ConfigParser(config=path_to_file, device_type="ios")

    # Print number of config lines
    print(len(config.lines))

