import pathlib
import json
import re
from jinja2 import FileSystemLoader, Environment, select_autoescape

class CCTemplater:
    def __init__(self, template_folder=None):
        self.template_folder = template_folder if template_folder else pathlib.Path("ccutils/templates")
        self.env = Environment(
            loader=FileSystemLoader(searchpath=str(self.template_folder)),
            autoescape=select_autoescape(["jinja2"]),
            lstrip_blocks=True,
            trim_blocks=True
        )
        
    def render(self, template_name, context):
        template = self.env.get_template(template_name)
        return template.render(context=context)

if __name__ == "__main__":
    context = None
    with open(r"C:\Users\mhudec\Develop\cctemplater\cctemplater\context_skeleton.json") as f:
        context = json.load(fp=f)
    ct = CCTemplater()
    print(ct.render(template_name="base_config.jinja2", context=context))