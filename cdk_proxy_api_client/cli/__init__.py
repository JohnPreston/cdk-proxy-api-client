#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

import json
import logging
import sys
from os import path

import yaml

try:
    from yaml import Dumper
except ImportError:
    from yaml import CDumper as Dumper

from compose_x_common.compose_x_common import keyisset, set_else_none

from cdk_proxy_api_client.admin_auth import AdminAuth
from cdk_proxy_api_client.cli.main_parser import set_parser
from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.concentration import TenantContentrationMapping
from cdk_proxy_api_client.proxy_api import ApiClient, Multitenancy, ProxyClient
from cdk_proxy_api_client.tenant_mappings import TenantTopicMappings
from cdk_proxy_api_client.tools import load_config_file
from cdk_proxy_api_client.tools.import_tenants_mappings import import_tenants_mappings


def auth_actions(proxy: ProxyClient, action: str, **kwargs):
    """Manages actions for AdminAuth"""
    admin_auth = AdminAuth(proxy)
    if action == "create":
        try:
            return admin_auth.create_tenant_credentials(
                tenant_id=kwargs.get("tenant_name"),
                token_lifetime_seconds=int(kwargs.get("token_lifetime_in_seconds")),
            ).json()
        except Exception as error:
            LOG.exception(error)
            LOG.error(
                "Failed to create new Proxy token for {}".format(kwargs["tenant_name"])
            )


def tenants_actions(proxy: ProxyClient, action: str, **kwargs):
    """Manages execution of Multitenancy"""
    multitenancy = Multitenancy(proxy)
    if action == "list":
        return multitenancy.list_tenants(as_list=True)


def tenant_mappings_actions(proxy: ProxyClient, action: str, **kwargs):
    """Manages actions for TenantMappings"""
    tenants_mappings = TenantTopicMappings(proxy)
    tenant_name = set_else_none("tenant_name", kwargs)
    if action == "list":
        return tenants_mappings.list_tenant_topics_mappings(tenant_name).json()
    elif action == "import-from-tenants-config":
        content = load_config_file(path.abspath(kwargs["import_config_file"]))
        topics_mappings = import_tenants_mappings(proxy, content, tenant_name)
        return topics_mappings
    elif action == "create":
        tenants_mappings.create_tenant_topic_mapping(
            tenant_name,
            kwargs["logical_topic_name"],
            kwargs["physical_topic_name"],
            keyisset("ReadWrite", kwargs),
        )
    elif action == "import-from-tenant":
        source_tenant = kwargs.pop("source_tenant")
        content = {
            "tenant_name": tenant_name,
            "mappings": [],
            "ignore_duplicates_conflict": True,
            "import_from_tenant": {"include_regex": [rf"^{source_tenant}$"]},
        }
        topics_mappings = import_tenants_mappings(proxy, content, tenant_name)
        return topics_mappings
    elif action == "delete-topic-mapping":
        to_delete = kwargs.pop("logicalTopicName")
        tenants_mappings.delete_tenant_topic_mapping(
            tenant_id=tenant_name, logical_topic_name=to_delete
        )
        return tenants_mappings.list_tenant_topics_mappings(tenant_name).json()
    elif action == "delete-all-mappings":
        tenants_mappings.delete_all_tenant_topics_mappings(tenant_name)


def tenant_concentrated_mappings_actions(proxy: ProxyClient, action: str, **kwargs):
    """
    Manage concentrated topic mappings.
    :param proxy:
    :param action:
    :param kwargs:
    :return:
    """
    concentration_mgmr = TenantContentrationMapping(proxy)
    if action == "create":
        req = concentration_mgmr.create_tenant_concentration(
            kwargs["tenant_name"],
            logical_regex=kwargs["topicRegex"],
            physical_topic_name=kwargs["physicalTopicName"],
        )
        try:
            return req.json()
        except Exception as error:
            print(error)
            return req.text


def main():
    _PARSER = set_parser()
    _args = _PARSER.parse_args()
    if hasattr(_args, "loglevel") and _args.loglevel:
        valid_levels = [
            "FATAL",
            "CRITICAL",
            "ERROR",
            "WARNING",
            "WARN",
            "INFO",
            "DEBUG",
            "INFO",
        ]
        if _args.loglevel.upper() in valid_levels:
            LOG.setLevel(logging.getLevelName(_args.loglevel.upper()))
            LOG.handlers[0].setLevel(logging.getLevelName(_args.loglevel.upper()))
        else:
            print(
                f"Log level value {_args.loglevel} is invalid. Must me one of {valid_levels}"
            )
    _vars = vars(_args)
    _client = ApiClient(
        username=_vars.pop("username"),
        password=_vars.pop("password"),
        url=_vars.pop("url"),
    )
    _category = _vars.pop("category")
    _action = _vars.pop("action")
    _proxy = ProxyClient(_client)

    _categories_mappings: dict = {
        "tenants": tenants_actions,
        "tenant-topic-mappings": tenant_mappings_actions,
        "auth": auth_actions,
        "tenant-concentrated-mappings": tenant_concentrated_mappings_actions,
    }
    dest_function = _categories_mappings[_category]
    response = dest_function(_proxy, _action, **_vars)
    if not response:
        return
    try:
        if _args.output_format == "json":
            print(json.dumps(response, indent=2))
        else:
            print(yaml.dump(response, Dumper=Dumper))
    except Exception as error:
        print(error)
        print(response)


if __name__ == "__main__":
    sys.exit(main())
