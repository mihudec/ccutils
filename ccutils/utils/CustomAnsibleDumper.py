import yaml
from yaml.representer import Representer
from yaml.dumper import Dumper
from yaml.emitter import Emitter
from yaml.serializer import Serializer
from yaml.resolver import Resolver
from collections import OrderedDict


def represent_ordereddict(dumper, data):
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

class CustomAnsibleRepresenter(Representer):

    def represent_none(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:null', u'')


class CustomAnsibleDumper(Emitter, Serializer, CustomAnsibleRepresenter, Resolver):
    def __init__(self, stream,
                 default_style=None, default_flow_style=None,
                 canonical=None, indent=None, width=None,
                 allow_unicode=None, line_break=None,
                 encoding=None, explicit_start=None, explicit_end=None, sort_keys=False,
                 version=None, tags=None):
        Emitter.__init__(self, stream, canonical=canonical,
                         indent=indent, width=width,
                         allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                            explicit_start=explicit_start, explicit_end=explicit_end,
                            version=version, tags=tags)
        CustomAnsibleRepresenter.__init__(self, default_style=default_style,
                                          default_flow_style=default_flow_style)
        Resolver.__init__(self)

        CustomAnsibleRepresenter.add_representer(type(None), CustomAnsibleRepresenter.represent_none)
        CustomAnsibleRepresenter.add_representer(OrderedDict, represent_ordereddict)


    def increase_indent(self, flow=False, indentless=False):
        return super(CustomAnsibleDumper, self).increase_indent(flow=flow, indentless=False)