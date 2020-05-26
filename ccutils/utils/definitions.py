import pathlib

INSTALL_DIR = pathlib.Path(__file__).parent.parent
SCHEMA_DIR = INSTALL_DIR.joinpath("schemas")
SCHEMA_BASE_URI = "https://github.com/mihudec/ccutils/schemas"
