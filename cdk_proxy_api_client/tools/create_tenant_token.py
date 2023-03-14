#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

"""Wrapper to configure mappings for a given tenant"""

from __future__ import annotations

import sys

from cdk_proxy_api_client.admin_auth import AdminAuth
from cdk_proxy_api_client.proxy_api import ApiClient, ProxyClient


def create_tenant_token(
    pxy: ProxyClient, tenant_name: str, expiry_in_seconds: int = 900
) -> str:
    """Creates a new token for a given tenant"""
    admin = AdminAuth(pxy)
    return admin.create_tenant_credentials(tenant_name, expiry_in_seconds, True)


def main():
    from argparse import ArgumentParser

    _parser = ArgumentParser("Create tenant token")
    _parser.add_argument("--username", required=True)
    _parser.add_argument("--password", required=True)
    _parser.add_argument("--url", required=True, default=None)
    _parser.add_argument("--tenant-name", required=True)
    _parser.add_argument("--lifetime-in-seconds", type=int, required=False, default=900)
    _args = _parser.parse_args()
    _client = ApiClient(username=_args.username, password=_args.password, url=_args.url)
    _proxy = ProxyClient(_client)
    token = create_tenant_token(_proxy, _args.tenant_name, _args.lifetime_in_seconds)
    print(token)


if __name__ == "__main__":
    sys.exit(main())
