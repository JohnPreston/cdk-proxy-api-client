#!/usr/bin/env python

#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

import getpass
import json
from argparse import Action, ArgumentParser

from cdk_proxy_api_client.proxy_api import ApiClient, Multitenancy, ProxyClient
from cdk_proxy_api_client.tenant_mappings import TenantTopicMappings
from cdk_proxy_api_client.tenant_mappings import (
    exceptions as tenant_mappings_exceptions,
)


def get_proxy(hostname: str, port: int, username: str, password: str) -> ProxyClient:
    api = ApiClient(hostname, port, username=username, password=password)
    pxy = ProxyClient(api)
    return pxy


def test_all(
    tenant_name: str, hostname: str, port: int, username: str, password: str
) -> None:
    pxy = get_proxy(hostname, port, username, password)

    # new_tenant = AdminAuth(pxy)
    # creds = new_tenant.create_tenant_credentials(
    #     tenant_name, token_lifetime_seconds=900
    # )
    # print(creds.json())

    multi = Multitenancy(pxy)
    print("Initial tenants", multi.list_tenants().json())

    tenants_mappings = TenantTopicMappings(pxy)

    try:
        print(
            "MAPPINGS PRE",
            tenants_mappings.list_tenant_topics_mappings(tenant_name),
        )
    except tenant_mappings_exceptions.TenantNotFound as error:
        print(error)

    tenants_mappings.create_tenant_topic_mapping(
        tenant_name,
        "logical-icare",
        "ijustdontcare",
        False,
    )
    tenants_mappings.create_tenant_topic_mapping(
        tenant_name,
        "logical-icare-second",
        "ijustdontcare-second",
        True,
    )
    print("TENANTS POST MAPPING", multi.list_tenants().json())
    print(f"mappings for {tenant_name}")
    print(
        json.dumps(
            tenants_mappings.list_tenant_topics_mappings(tenant_name).json(),
            indent=1,
        ),
    )
    print("DELETE ONE MAPPING")
    tenants_mappings.delete_tenant_topic_mapping(
        tenant_name,
        "logical-icare",
    )
    print("MAPPINGS POST DELETE 1 MAPPING")
    print(
        json.dumps(
            tenants_mappings.list_tenant_topics_mappings(tenant_name).json(),
            indent=1,
        ),
    )
    print("MAPPINGS PRE DELETE")

    print(
        json.dumps(
            tenants_mappings.list_tenant_topics_mappings(tenant_name).json(),
            indent=1,
        ),
    )
    tenants_mappings.delete_all_tenant_topics_mappings(tenant_name)
    try:
        print("MAPPINGS POST DELETE")
        print(
            tenants_mappings.list_tenant_topics_mappings(tenant_name),
        )
    except tenant_mappings_exceptions.TenantNotFound as error:
        print(error)

    print("Tenants", multi.list_tenants().json())


class PasswordPromptAction(Action):
    """https://stackoverflow.com/questions/27921629/python-using-getpass-with-argparse"""

    def __init__(
        self,
        option_strings,
        dest=None,
        nargs=0,
        default=None,
        required=False,
        type=None,
        metavar=None,
        help=None,
    ):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            default=default,
            required=required,
            metavar=metavar,
            type=type,
            help=help,
        )

    def __call__(self, parser, args, values, option_string=None):
        password = getpass.getpass()
        setattr(args, self.dest, password)


if __name__ == "__main__":
    PARSER = ArgumentParser()
    PARSER.add_argument("--tenant-name", required=True)
    PARSER.add_argument("--username", required=True)
    PARSER.add_argument("--password", required=True, action=PasswordPromptAction)
    PARSER.add_argument("--hostname", required=False, default="localhost", type=str)
    PARSER.add_argument("--port", required=False, default=8888, type=int)

    ARGS = PARSER.parse_args()
    test_all(ARGS.tenant_name, ARGS.hostname, ARGS.port, ARGS.username, ARGS.password)
