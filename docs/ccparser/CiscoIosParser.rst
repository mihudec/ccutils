==============
CiscoIosParser
==============
.. _cisco-ios-parser:

-----------
Quick Start
-----------

..  code-block:: python

    from ccutils.ccparser import CiscoIosParser
    import pathlib

    # Optinal - Create pathlib object pointing to your config file
    path_to_file = pathlib.Path("/path/to/config_file.txt")

    config = CiscoIosParser(config=path_to_file)

    # Print number of config lines
    print(len(config.lines))



..  autoclass:: ccutils.ccparser.CiscoIosParser
    :members:
    :undoc-members:
    :show-inheritance:
