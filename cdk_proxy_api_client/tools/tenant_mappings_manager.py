#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

"""Wrapper to configure mappings for a given tenant"""

from __future__ import annotations

import sys

import yaml

try:
    from yaml import Dumper
except ImportError:
    from yaml import CDumper as Dumper

from json import loads
from os import path

from compose_x_common.compose_x_common import keyisset
from importlib_resources import files as pkg_files
from jsonschema import validate

from cdk_proxy_api_client.errors import ProxyGenericException
from cdk_proxy_api_client.proxy_api import ApiClient, ProxyClient
from cdk_proxy_api_client.tenant_mappings import TenantMappings

DEFAULT_SCHEMA_PATH = pkg_files("cdk_proxy_api_client").joinpath(
    "specs/tenant_mappings-input.json"
)


def mappings_manager(
    client: ProxyClient, config_content: dict, schema: dict = None
) -> list[dict]:
    """Will create mappings from the config content, and return the final mappings for the tenant"""
    if not schema:
        schema = loads(DEFAULT_SCHEMA_PATH.read_text())
    validate(config_content, schema)
    tenant_name = config_content["tenant_name"]
    ignore_conflicts = keyisset("ignore_duplicates_conflict", config_content)
    mappings = config_content["mappings"]
    tenant_mappings = TenantMappings(client)

    for mapping in mappings:
        try:
            tenant_mappings.create_tenant_topic_mapping(
                tenant_name,
                mapping["logicalTopicName"],
                mapping["physicalTopicName"],
                read_only=keyisset("readOnly", mapping),
            )
        except ProxyGenericException as error:
            if error.code == 409 and ignore_conflicts:
                pass

    return tenant_mappings.list_tenant_topics_mappings(tenant_name, True)


def main():
    from argparse import ArgumentParser
    from json import dumps

    from cdk_proxy_api_client.tools import load_config_file

    _parser = ArgumentParser("Create tenant mappings from configuration file")
    _parser.add_argument(
        "-f",
        "--mappings-file",
        help="Path to the tenants mappings config file",
        required=True,
    )
    _parser.add_argument("--username", required=True)
    _parser.add_argument("--password", required=True)
    _parser.add_argument("--url", required=True, default=None)
    _parser.add_argument(
        "--to-yaml", action="store_true", help="Output the mappings in YAML"
    )
    _args = _parser.parse_args()
    _content = load_config_file(_args.mappings_file)
    _client = ApiClient(username=_args.username, password=_args.password, url=_args.url)
    _proxy = ProxyClient(_client)
    _MAPPINGS = mappings_manager(_proxy, _content)
    if _args.to_yaml:
        print(yaml.dump(_MAPPINGS, Dumper=Dumper))
    else:
        print(dumps(_MAPPINGS, indent=2))


if __name__ == "__main__":
    sys.exit(main())
