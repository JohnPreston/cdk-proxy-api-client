#!/usr/bin/env python

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
from cdk_proxy_api_client.plugins import Plugins
from cdk_proxy_api_client.proxy_api import ProxyClient
from cdk_proxy_api_client.vclusters import VirtualClusters


def generate_random_string(length=10):
    """Generate a random string of specified length."""
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))


@pytest.fixture(scope="session")
def proxy_client(base_url):
    return ProxyClient(ApiClient(url=base_url, username="admin", password="conduktor"))


def test_list_vclusters_unauthorized(base_url):
    proxy = ProxyClient(ApiClient(url=base_url))
    plugins_c = Plugins(proxy)
    with pytest.raises(GenericUnauthorized):
        plugins_c.list_all_plugins()


def test_forbidden(base_url):
    proxy = ProxyClient(
        ApiClient(url=base_url, username="readonly", password="conduktor")
    )
    vclusters_c = VirtualClusters(proxy)
    with pytest.raises(GenericForbidden):
        client_token = vclusters_c.create_vcluster_user_token(
            "testing", username="admin_client", token_only=True
        )


def test_list_plugings(proxy_client, base_url):
    plugins_c = Plugins(proxy_client)
    plugins = plugins_c.list_all_plugins()


def test_simple_vcluster(proxy_client, kafka_bootstrap, gateway_bootstrap):
    vclusters_c = VirtualClusters(proxy_client)
    vclusters_l = vclusters_c.list_vclusters().json()["vclusters"]
    assert not vclusters_l

    client_token = vclusters_c.create_vcluster_user_token(
        "testing", username="admin_client", token_only=True
    )
    assert client_token

    phy_client_config: dict = {
        "bootstrap.servers": kafka_bootstrap,
        "security.protocol": "PLAINTEXT",
    }
    phy_admin_client = AdminClient(phy_client_config)
    _return_values = phy_admin_client.create_topics(
        [NewTopic("simple_topic", num_partitions=2)]
    )
    for _future in _return_values.values():
        while not _future.done():
            pass

    phy_topics_list: list[str] = list(phy_admin_client.list_topics().topics.keys())
    assert "simple_topic" in phy_topics_list

    virt_client_config: dict = {
        "bootstrap.servers": gateway_bootstrap,
        "security.protocol": "SASL_PLAINTEXT",
        "sasl.mechanism": "PLAIN",
        "sasl.username": "admin_client",
        "sasl.password": client_token,
    }
    virt_admin_client = AdminClient(virt_client_config)
    virt_topics_list: list[str] = list(virt_admin_client.list_topics().topics.keys())
    assert not virt_topics_list
    _return_values: dict = virt_admin_client.create_topics([NewTopic("simple_topic")])
    for _future in _return_values.values():
        while not _future.done():
            if _future.exception():
                raise _future.exception()
    virt_topics_list: list[str] = list(virt_admin_client.list_topics().topics.keys())
    assert "simple_topic" in virt_topics_list

    vclusters_l = vclusters_c.list_vcluster_topic_mappings("testing", as_list=True)
    assert not vclusters_l

    vclusters_c.create_vcluster_topic_mapping(
        vcluster="testing",
        logical_topic_name="phy.simple-topic",
        physical_topic_name="simple_topic",
    )
    vclusters_l: list[dict] = vclusters_c.list_vcluster_topic_mappings(
        "testing", as_list=True
    )
    print(vclusters_l)
    assert "phy.simple-topic" in [
        _mapping["logicalTopicName"] for _mapping in vclusters_l
    ]

    virt_producer_config: dict = deepcopy(virt_client_config)
    virt_producer_config.update(
        {
            "client.id": "producer_test",
            "acks": "all",
            "compression.type": "zstd",
            "linger.ms": 200,
        }
    )
    virt_producer = Producer(virt_client_config)
    messages: dict = {
        str(uuid.uuid4()): generate_random_string() for _ in range(1, 100)
    }

    for key, value in messages.items():
        virt_producer.produce("phy.simple-topic", value=value, key=key)
    virt_producer.poll(0.5)
    virt_producer.flush()

    virt_consumer_config: dict = deepcopy(virt_client_config)
    virt_consumer_config.update(
        {
            "group.id": "consumer_test",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    virt_consumer = Consumer(virt_consumer_config)
    virt_consumer.subscribe(["phy.simple-topic"])
    consumed_messages: int = 0
    while True:
        msg = virt_consumer.poll(1000)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event, not an error
                print("EOP")
                break
            print(f"Consumer error: {msg.error()}")
        assert (
            msg.key().decode() in messages
            and msg.value().decode() == messages[msg.key().decode()]
        )
        consumed_messages += 1
        if consumed_messages == len(messages.keys()):
            break

    print("Sucessfully validated virtual topic data")
    phy_consumer_config: dict = deepcopy(phy_client_config)
    phy_consumer_config.update(
        {
            "group.id": "phy_consumer_test",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    virt_producer = None
    virt_consumer.close()
    phy_consumer = Consumer(phy_consumer_config)
    virt_admin_client = None
    phy_consumer.subscribe(["simple_topic"])
    consumed_messages: int = 0
    while True:
        msg = phy_consumer.poll(1000)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event, not an error
                print("EOP")
                break
            print(f"Consumer error: {msg.error()}")
        assert (
            msg.key().decode() in messages
            and msg.value().decode() == messages[msg.key().decode()]
        )
        consumed_messages += 1
        if consumed_messages == len(messages.keys()):
            break
