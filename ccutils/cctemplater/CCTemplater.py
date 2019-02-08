import pathlib
import json
import re
from jinja2 import FileSystemLoader, Environment, select_autoescape

class CCTemplater:
    def __init__(self, context, template_folder=None):
        self.context = context
        self.template_folder = template_folder if template_folder else pathlib.Path("ccutils/templates")
        print(self.template_folder)
        self.env = Environment(
            loader=FileSystemLoader(searchpath=str(self.template_folder)),
            autoescape=select_autoescape(["jinja2"]),
            lstrip_blocks=True,
            trim_blocks=True
        )
        
    def render(self, template_name, context):
        template = self.env.get_template(template_name)
        return template.render(context=context)

