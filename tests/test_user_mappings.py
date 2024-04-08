#!/usr/bin/env python

"""tests for interceptors"""

from __future__ import annotations

import json

import pytest

from cdk_proxy_api_client.client_wrapper import ApiClient
from cdk_proxy_api_client.proxy_api import ProxyClient
from cdk_proxy_api_client.user_mappings import UserMappings


@pytest.fixture()
def proxy_client(base_url):
    return ProxyClient(ApiClient(url=base_url, username="admin", password="conduktor"))


def test_empty_user_mappings(proxy_client):
    user_mappings = UserMappings(proxy_client)
    assert user_mappings.list_mappings().json() == []


def test_create_user_mappings(proxy_client):
    user_mappings = UserMappings(proxy_client)
    user_mappings.create_mapping("test", "some-identity-something")
    assert "test" in user_mappings.list_mappings().json()


def test_update_user_mappings(proxy_client):
    user_mappings = UserMappings(proxy_client)
    user_mappings.update_mapping(
        "test", "some-identity-something-else", groups=["dummy-users"]
    )
    assert "test" in user_mappings.list_mappings().json()
    the_user = user_mappings.get_user_mapping(username="test").json()
    assert "dummy-users" in the_user["groups"]
    user_mappings.update_mapping(
        "test", "some-identity-something-else", groups=["beta-testers"]
    )
    the_user = user_mappings.get_user_mapping(username="test").json()
    print(json.dumps(the_user))
    assert "dummy-users" not in the_user["groups"]
