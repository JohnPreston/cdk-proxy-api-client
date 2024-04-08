from __future__ import annotations

import json
import random
import string
import uuid
from copy import deepcopy

import pytest
from confluent_kafka import Consumer, KafkaError, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from cdk_proxy_api_client.client_wrapper import ApiClient
from cdk_proxy_api_client.interceptors import Interceptors
from cdk_proxy_api_client.proxy_api import ProxyClient
from cdk_proxy_api_client.vclusters import VirtualClusters


def generate_random_string(length=10):
    """Generate a random string of specified length."""
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))


def on_delivery(err, msg):
    if err:
        print(f"Delivery failed for {msg.value()}: {err}")
        raise KafkaException(err)


@pytest.fixture()
def messages() -> dict:
    return {str(uuid.uuid4()): generate_random_string() for _ in range(1, 100)}


@pytest.fixture()
def proxy_client(base_url):
    return ProxyClient(ApiClient(url=base_url, username="admin", password="conduktor"))


def generate_random_string(length=10):
    """Generate a random string of specified length."""
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))


def on_delivery(err, msg):
    if err:
        print(f"Delivery failed for {msg.value()}: {err}")
        raise KafkaException(err)


@pytest.mark.timeout(60)
def test_vcluster_concentration(
    proxy_client, kafka_bootstrap, gateway_bootstrap, messages
):
    vclusters_c = VirtualClusters(proxy_client)
    vcluster_name: str = "all-in-one."
    vclusters_l = vclusters_c.list_vclusters().json()["vclusters"]
    assert vcluster_name not in vclusters_l

    client_token = vclusters_c.create_vcluster_user_token(
        vcluster_name, username="admin_client", token_only=True
    )
    assert client_token

    phy_client_config: dict = {
        "bootstrap.servers": kafka_bootstrap,
        "security.protocol": "PLAINTEXT",
    }
    phy_admin_client = AdminClient(phy_client_config)
    cleanup_policies: list[str] = ["delete", "compact", "compact,delete"]
    _return_values = phy_admin_client.create_topics(
        [
            NewTopic(
                f"concentrated.{_type.replace(',', '_')}",
                num_partitions=1,
                config={"cleanup.policy": _type},
            )
            for _type in cleanup_policies
        ]
    )
    for _future in _return_values.values():
        while not _future.done():
            pass

    phy_topics_list: list[str] = list(phy_admin_client.list_topics().topics.keys())
    print("PHY?", phy_topics_list)
    vclusters_c.create_concentration_rule(
        vcluster_name,
        r"new-topic(.*)",
        "concentrated.delete",
        "concentrated.compact",
        "concentrated.compact_delete",
    )
    vclusters_c.create_concentration_rule(
        vcluster_name,
        r"other-topics(.*)",
        "concentrated.delete",
        "concentrated.compact",
        "concentrated.compact_delete",
    )

    virt_client_config: dict = {
        "bootstrap.servers": gateway_bootstrap,
        "security.protocol": "SASL_PLAINTEXT",
        "sasl.mechanism": "PLAIN",
        "sasl.username": "admin_client",
        "sasl.password": client_token,
    }
    target_topic_name: str = "new-topic"

    virt_admin_client = AdminClient(virt_client_config)
    virt_topics_list: list[str] = list(virt_admin_client.list_topics().topics.keys())
    assert not virt_topics_list
    _return_values: dict = virt_admin_client.create_topics(
        [
            NewTopic(target_topic_name, num_partitions=2),
            NewTopic(
                f"{target_topic_name}-compacted",
                num_partitions=6,
                config={"cleanup.policy": "compact"},
            ),
        ]
    )
    for _future in _return_values.values():
        while not _future.done():
            if _future.exception():
                raise _future.exception()

    vclusters_l: list[dict] = vclusters_c.list_vcluster_topic_mappings(
        vcluster_name, as_list=True
    )
    print("Concentration mappings", vclusters_l)
    for topic_mapping in vclusters_l:
        if topic_mapping["logicalTopicName"] == target_topic_name:
            assert topic_mapping["physicalTopicName"] == "concentrated.delete"
        if topic_mapping["logicalTopicName"] == f"{target_topic_name}-compacted":
            assert topic_mapping["physicalTopicName"] == "concentrated.compact"
    assert target_topic_name in [
        _mapping["logicalTopicName"] for _mapping in vclusters_l
    ]

    virt_producer_config: dict = deepcopy(virt_client_config)
    virt_producer_config.update(
        {
            "client.id": "producer_test",
            "acks": "-1",
            "compression.codec": "gzip",
            "linger.ms": 100,
        }
    )
    print(
        json.dumps(
            Interceptors(proxy_client)
            .get_target_resolve(payload={"vcluster": vcluster_name})
            .json()
        )
    )
    virt_producer = Producer(virt_producer_config)
    for _topic in [target_topic_name, f"{target_topic_name}-compacted"]:
        for key, value in messages.items():
            virt_producer.produce(_topic, value=value, key=key, on_delivery=on_delivery)
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
    print("VIRT - CONSUMING MESSAGES")
    virt_consumer = Consumer(virt_consumer_config)
    virt_consumer.subscribe([target_topic_name])
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
        assert not msg.headers()
        consumed_messages += 1
        if consumed_messages == len(messages.keys()):
            break

    print("Sucessfully validated concentrated virtual topic data")


def test_delete_concentration_rule(proxy_client):
    vclusters_c = VirtualClusters(proxy_client)
    vcluster_name: str = "all-in-one."
    rules = vclusters_c.list_vcluster_topic_mappings(vcluster_name, as_list=True)
    print("PRE DELETE?", rules)
    vclusters_c.delete_concentration_rule(vcluster_name, pattern=r"new-topic(.*)")
    rules = vclusters_c.list_vcluster_topic_mappings(vcluster_name, as_list=True)
    for _rule in rules:
        if _rule["type"] != "concentration":
            continue
        assert _rule["logicalTopicName"] != "new-topic"
    print("mappings after concentration deleted?", rules)
