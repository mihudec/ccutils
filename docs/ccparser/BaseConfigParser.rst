================
BaseConfigParser
================
.. _base-config-parser:

-----------
Quick Start
-----------

..  code-block:: python

    from ccutils.ccparser import BaseConfigParser
    import pathlib

    # Optinal - Create pathlib object pointing to your config file
    path_to_file = pathlib.Path("/path/to/config_file.txt")

    config = BaseConfigParser(config=path_to_file)

    # Print number of config lines
    print(len(config.config_lines_obj))



..  autoclass:: ccutils.ccparser.BaseConfigParser
    :members:
    :private-members:
    :undoc-members:
    :show-inheritance:
