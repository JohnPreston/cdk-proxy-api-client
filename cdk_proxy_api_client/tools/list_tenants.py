#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

"""Wrapper to list tenants"""

from __future__ import annotations

import re
import sys

import yaml

try:
    from yaml import Dumper
except ImportError:
    from yaml import CDumper as Dumper

from json import loads

from compose_x_common.compose_x_common import keyisset, set_else_none
from importlib_resources import files as pkg_files
from jsonschema import validate

from cdk_proxy_api_client.errors import ProxyGenericException
from cdk_proxy_api_client.proxy_api import ApiClient, Multitenancy, ProxyClient
from cdk_proxy_api_client.tenant_mappings import TenantMappings


def list_tenant_mappings():
    from argparse import ArgumentParser
    from json import dumps

    _parser = ArgumentParser("List tenants")
    _parser.add_argument("--tenant-name", required=True, type=str)
    _parser.add_argument("--username", required=True)
    _parser.add_argument("--password", required=True)
    _parser.add_argument("--url", required=True, default=None)
    _parser.add_argument(
        "--to-yaml", action="store_true", help="Output the mappings in YAML"
    )
    _args = _parser.parse_args()
    _client = ApiClient(username=_args.username, password=_args.password, url=_args.url)
    _proxy = ProxyClient(_client)
    __tenant_mappings = TenantMappings(_proxy)

    if _args.to_yaml:
        print(
            yaml.dump(
                __tenant_mappings.list_tenant_topics_mappings(_args.tenant_name).json(),
                Dumper=Dumper,
            )
        )
    else:
        print(
            dumps(
                __tenant_mappings.list_tenant_topics_mappings(_args.tenant_name).json(),
                indent=2,
            )
        )


def list_tenants():
    from argparse import ArgumentParser
    from json import dumps

    _parser = ArgumentParser("List tenants")
    _parser.add_argument("--username", required=True)
    _parser.add_argument("--password", required=True)
    _parser.add_argument("--url", required=True, default=None)
    _parser.add_argument(
        "--to-yaml", action="store_true", help="Output the mappings in YAML"
    )
    _args = _parser.parse_args()
    _client = ApiClient(username=_args.username, password=_args.password, url=_args.url)
    _proxy = ProxyClient(_client)
    __tenants = Multitenancy(_proxy)

    if _args.to_yaml:
        print(yaml.dump(__tenants.list_tenants().json(), Dumper=Dumper))
    else:
        print(dumps(__tenants.list_tenants().json(), indent=2))


if __name__ == "__main__":
    sys.exit(list_tenants())
