#!/usr/bin/env python

"""tests for interceptors"""

from __future__ import annotations

import random
import string
import uuid
from copy import deepcopy

import pytest
from confluent_kafka import Consumer, KafkaError, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from cdk_proxy_api_client.client_wrapper import ApiClient
from cdk_proxy_api_client.errors import GenericForbidden, GenericUnauthorized
from cdk_proxy_api_client.interceptors import Interceptors
from cdk_proxy_api_client.plugins import Plugins
from cdk_proxy_api_client.proxy_api import ProxyClient
from cdk_proxy_api_client.vclusters import VirtualClusters


@pytest.fixture(scope="session")
def interceptors() -> dict:
    interceptors = {
        "defaultCreatePolicy": {
            "priority": 1001,
            "pluginClass": "io.conduktor.gateway.interceptor.safeguard.CreateTopicPolicyPlugin",
            "config": {
                "topic": ".*",
                "numPartition": {"min": 1, "max": 2, "action": "BLOCK"},
                "replicationFactor": {
                    "min": 1,
                    "max": 3,
                    "action": "OVERRIDE",
                    "overrideValue": 1,
                },
            },
        },
        "producerDynamicHeaderInjectionInterceptor": {
            "pluginClass": "io.conduktor.gateway.interceptor.DynamicHeaderInjectionPlugin",
            "priority": 100,
            "config": {
                "topic": "(.*)",
                "headers": {
                    "X-GW-VCLUSTER": "{{vcluster}}",
                    "X-GW-CLIENTID": "{{clientId}}",
                    "X-GW-USERID": "{{user}}",
                    "X-GW-APIKEYVERSION": "{{apiKeyVersion}}",
                },
            },
        },
        "defaultProducePolicy": {
            "pluginClass": "io.conduktor.gateway.interceptor.safeguard.ProducePolicyPlugin",
            "priority": 1001,
            "config": {
                "topic": ".*",
                "acks": {"value": [-1], "action": "BLOCK"},
                "compressions": {
                    "value": ["GZIP", "LZ4", "ZSTD", "SNAPPY"],
                    "action": "BLOCK",
                },
            },
        },
        "defaultRemoveHeaders": {
            "pluginClass": "io.conduktor.gateway.interceptor.safeguard.MessageHeaderRemovalPlugin",
            "priority": 100,
            "config": {"topic": "phy.*", "headerKeyRegex": "X-GW-USER(.*)"},
        },
    }
    return interceptors


@pytest.fixture()
def proxy_client(base_url):
    return ProxyClient(ApiClient(url=base_url, username="admin", password="conduktor"))


def test_interceptors(proxy_client, interceptors):
    interceptors_c = Interceptors(proxy_client)
    assert not interceptors_c.list_all_interceptors().json()["interceptors"]
    assert not interceptors_c.get_all_gw_interceptors().json()["interceptors"]
    assert not interceptors_c.get_all_interceptor().json()["interceptors"]

    interceptors_c.create_interceptor(
        "defaultCreatePolicy", interceptors["defaultCreatePolicy"], is_global=True
    )
    all_interceptors: list[dict] = interceptors_c.get_all_gw_interceptors().json()[
        "interceptors"
    ]
    print("All?", all_interceptors)
    assert "defaultCreatePolicy" in [_i["name"] for _i in all_interceptors]


def test_vcluster_interceptors(proxy_client, interceptors):
    interceptors_c = Interceptors(proxy_client)
    override_create_config: dict = {
        "priority": 1001,
        "pluginClass": "io.conduktor.gateway.interceptor.safeguard.CreateTopicPolicyPlugin",
        "config": {
            "topic": ".*",
            "numPartition": {"min": 1, "max": 4, "action": "BLOCK"},
            "replicationFactor": {
                "min": 1,
                "max": 3,
                "action": "OVERRIDE",
                "overrideValue": 1,
            },
        },
    }

    interceptors_c.create_interceptor(
        "defaultCreatePolicy",
        override_create_config,
        vcluster_name="testing",
        is_global=False,
    )
    default_create_override = interceptors_c.get_interceptor(
        "defaultCreatePolicy", vcluster_name="testing"
    ).json()
    print(default_create_override)

    default_create = interceptors_c.get_interceptor(
        "defaultCreatePolicy", is_global=True
    ).json()
    print(default_create)

    resolve = interceptors_c.get_target_resolve({"vcluster": "testing"}).json()
    print(resolve)

    for _interceptor_name in [
        "defaultProducePolicy",
        "producerDynamicHeaderInjectionInterceptor",
        "defaultRemoveHeaders",
    ]:
        interceptors_c.create_interceptor(
            _interceptor_name,
            interceptors[_interceptor_name],
            vcluster_name="testing",
            username="admin_client",
        )

    resolve = interceptors_c.get_target_resolve(
        {"vcluster": "testing", "username": "admin_client"}
    ).json()
    print(resolve)
