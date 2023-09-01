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
from requests import Response

from cdk_proxy_api_client.cli.main_parser import set_parser
from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.plugins import Plugins
from cdk_proxy_api_client.proxy_api import ApiClient, ProxyClient
from cdk_proxy_api_client.tools import load_config_file
from cdk_proxy_api_client.tools.import_from_config import import_clients
from cdk_proxy_api_client.tools.import_tenants_mappings import import_tenants_mappings
from cdk_proxy_api_client.vclusters import VirturalClusters


def format_return(function):
    """
    Decorator to evaluate the requests payload returned
    """

    def wrapped_answer(*args, **kwargs):
        """
        Decorator wrapper
        """
        req = function(*args, **kwargs)
        if isinstance(req, Response):
            try:
                return req.json()
            except Exception as error:
                print(error)
                return req.text
        return req

    return wrapped_answer


@format_return
def vclusters_actions(proxy: ProxyClient, action: str, **kwargs):
    """Manages execution of vClusters"""
    vclusters = VirturalClusters(proxy)
    if action == "list":
        req = vclusters.list_vclusters(as_list=True)
    elif action == "auth":
        req = auth_actions(vclusters, kwargs.pop("sub_action"), **kwargs)
    elif action == "mappings":
        req = tenant_mappings_actions(
            proxy, vclusters, kwargs.pop("sub_action"), **kwargs
        )
    else:
        raise NotImplementedError(f"Action {action} not yet implemented.")
    return req


def auth_actions(vcluster: VirturalClusters, action: str, **kwargs):
    """Manages actions for auth vClusters subparser"""
    username = kwargs.get("username") or kwargs["vcluster_name"]
    if action == "create":
        req = vcluster.create_vcluster_user_token(
            vcluster=kwargs.get("vcluster_name"),
            username=username,
            lifetime_in_seconds=int(kwargs.get("token_lifetime_in_seconds")),
            token_only=keyisset("token_only", kwargs),
        )
    else:
        raise NotImplementedError(f"Action {action} not yet implemented.")
    if keyisset("as_kafka_config", kwargs):
        req = req.json()
        return """security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="{}" password="{}";
client.id=CLI_{}
        """.format(
            username, req["token"], username
        )
    return req


def tenant_mappings_actions(
    proxy: ProxyClient, vcluster: VirturalClusters, action: str, **kwargs
):
    """Manages actions for mappings vClusters actions"""

    vcluster_name = set_else_none("vcluster_name", kwargs)
    if action == "list":
        req = vcluster.list_vcluster_topic_mappings(vcluster_name).json()
    elif action == "import-from-vclusters-config":
        content = load_config_file(path.abspath(kwargs["import_config_file"]))
        req = import_tenants_mappings(proxy, content, vcluster_name)
    elif action == "create":
        req = vcluster.create_vcluster_topic_mapping(
            vcluster=vcluster_name,
            logical_topic_name=kwargs["logical_topic_name"],
            physical_topic_name=kwargs["physical_topic_name"],
            read_only=keyisset("ReadOnly", kwargs),
            concentrated=keyisset("concentrated", kwargs),
            cluster_id=kwargs.get("cluster_id"),
        )
    elif action == "import-from-tenant":
        source_tenant = kwargs.pop("source_tenant")
        content = {
            "vcluster_name": vcluster_name,
            "mappings": [],
            "ignore_duplicates_conflict": True,
            "import_from_tenant": {"include_regex": [rf"^{source_tenant}$"]},
        }
        req = import_tenants_mappings(proxy, content, vcluster_name)
    elif action == "delete-topic-mapping":
        to_delete = kwargs.pop("logicalTopicName")
        req = vcluster.delete_vcluster_topic_mapping(
            vcluster=vcluster_name, logical_topic_name=to_delete
        )
    elif action == "delete-all-mappings":
        req = vcluster.delete_vcluster_topics_mappings(vcluster_name)
    else:
        raise NotImplementedError(f"Action {action} not yet implemented.")
    return req


@format_return
def plugins_actions(proxy: ProxyClient, action: str, **kwargs):
    _plugins = Plugins(proxy)
    if action == "list":
        req = _plugins.list_all_plugins(
            extended=keyisset("extended", kwargs), as_list=keyisset("as_list", kwargs)
        )
    else:
        raise NotImplementedError("Action {} is not implemented yet.".format(action))
    return req


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
    if _args.url:
        if not _args.username or not _args.password:
            raise Exception(
                "If you specify URL, you must specify username and password too"
            )
        _client = ApiClient(
            username=_vars.pop("username"),
            password=_vars.pop("password"),
            url=_vars.pop("url"),
        )
    elif _args.profile_name:
        _clients = import_clients(_args.config_file)
        _client = _clients[_args.profile_name]
    else:
        raise Exception(
            "You must either set --profile-name (possibly -c) or define --url, --username and --password"
        )
    _category = _vars.pop("category")
    _action = _vars.pop("action")
    _proxy = ProxyClient(_client)

    _categories_mappings: dict = {
        "vclusters": vclusters_actions,
        "plugins": plugins_actions,
    }
    dest_function = _categories_mappings[_category]
    response = dest_function(_proxy, _action, **_vars)
    if not response:
        return
    if isinstance(response, str):
        print(response)
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
