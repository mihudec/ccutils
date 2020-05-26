from ccutils.utils.common_utils import get_logger
from ccutils.utils.definitions import SCHEMA_DIR, SCHEMA_BASE_URI
import pathlib
import json
import jsonschema
import functools


class JsonValidator(object):

    def __init__(self, schema_dir=None, base_uri=None, verbosity=3):
        self.logger = get_logger(name="JsonValidator", verbosity=verbosity)
        self.schema_dir = pathlib.Path(schema_dir) if schema_dir is not None else SCHEMA_DIR
        self.logger.debug("Loading schemas from: {}".format(self.schema_dir))
        self.base_uri = base_uri if base_uri is not None else SCHEMA_BASE_URI
        self.logger.debug("Schema Base URI: {}".format(self.base_uri))
        self.schema_store = self.load_schema_store()
        self.logger.debug("Schema Store: {}".format(self.schema_store))
        self.test_schema_store()

    def load_schema_store(self):
        schema_store = {}

        for schema_path in [x for x in self.schema_dir.iterdir() if x.suffix == ".json"]:
            with schema_path.open() as schema_fp:
                try:
                    schema = json.load(fp=schema_fp)
                    if "$id" in schema.keys():
                        schema_store[schema["$id"]] = {"schema": schema}
                except Exception as e:
                    # TODO: Fix Exceptions
                    self.logger.error("Could not load valid JSON from: '{}' Exception: {}".format(schema_path, repr(e)))
        return schema_store

    @functools.lru_cache()
    def test_schema(self, schema_id):
        try:
            schema = self.schema_store["{}/{}".format(self.base_uri, schema_id)]["schema"]
            resolver = jsonschema.RefResolver(base_uri="file://{}/{}.json".format(self.schema_dir, schema_id), referrer=schema, store={k: v["schema"] for k, v in self.schema_store.items()})
            self.schema_store["{}/{}".format(self.base_uri, schema_id)]["resolver"] = resolver
            validator = jsonschema.Draft7Validator(schema=schema, resolver=resolver)
            self.schema_store["{}/{}".format(self.base_uri, schema_id)]["validator"] = validator
            validator.check_schema(schema=validator.schema)
            self.logger.debug("Schema '{}' is valid.".format(schema_id))
            return True
        except KeyError as e:
            self.logger.error("Schema '{}' not found in schema store. Exception: {}".format(schema_id, repr(e)))
            return False
        except jsonschema.exceptions.SchemaError as e:
            self.logger.error("Schema Error on '{}'. Exception: {}".format(schema_id, repr(e)))
        except Exception as e:
            self.logger.critical("Unhandled Exception occurred when validating schema: '{}' Exception: {}".format(schema_id, repr(e)))
            return False

    def validate(self, data, schema_id):
        result = False
        validator = self.schema_store["{}/{}".format(self.base_uri, schema_id)]["validator"]
        try:
            self.logger.debug("Validating data against schema: {}. Data: '{}'".format(schema_id, data))
            validator.validate(data)
            self.logger.debug("Data is valid acording to schema: {}. Data: '{}'".format(schema_id, data))
            result = True
        except jsonschema.exceptions.ValidationError as e:
            self.logger.warning("ValidationError: Data is not valid against the schema: {}. Data: '{}' Exception: {}".format(schema_id, data, repr(e)))
            result = False
        except Exception as e:
            self.logger.critical("Unhandled Exception occurred when validating data with schema: '{}' Exception: {}".format(schema_id, repr(e)))
            result = False
        finally:
            return result

    def test_schema_store(self):
        for schema_id in [x.split("/")[-1] for x in self.schema_store.keys()]:
            self.logger.debug("Validating schema: '{}'".format(schema_id))
            result = self.test_schema(schema_id=schema_id)
            if result:
                pass
            else:
                self.logger.error("Schema '{}' is NOT valid.".format(schema_id))

