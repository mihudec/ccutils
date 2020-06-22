from ccutils.ccparser.BaseConfigLine import BaseConfigLine
from ccutils.ccparser.BaseInterfaceLine import BaseInterfaceLine
from ccutils.ccparser.BaseConfigParser import BaseConfigParser
from ccutils.ccparser.ConfigToJson import ConfigToJson
from ccutils.ccparser.ConfigMigration import ConfigMigration
from ccutils.ccparser.CiscoIosInterfaceLine import CiscoIosInterfaceLine
from ccutils.ccparser.CiscoIosParser import CiscoIosParser


def ConfigParser(config, device_type, verbosity=4):
    """
    Factory function for getting Parser object
    Args:
        config:
        device_type:
        verbosity:

    Returns:
        obj: Instance of proper Parsing class based on device_type

    """
    parser_class = BaseConfigParser
    if device_type == "ios":
        parser_class = CiscoIosParser

    return parser_class(config=config, verbosity=verbosity)