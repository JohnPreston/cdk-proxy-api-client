#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>


from __future__ import annotations

from typing import Union

from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.errors import GenericNotFound
from cdk_proxy_api_client.proxy_api import ApiApplication, Multitenancy
from cdk_proxy_api_client.tenant_mappings.exceptions import (
    TenantNotFound,
    TopicOrTenantNotFound,
)


class TenantTopicMappings(ApiApplication):
    """Manage admin/multitenancy tenancy topics mappings"""

    app_path: str = f"{Multitenancy.app_path}"

    def create_tenant_topic_mapping(
        self,
        tenant_id: str,
        logical_topic_name: str,
        physical_topic_name: str,
        read_only: bool = False,
    ) -> Response:
        """Create a new logical to physical topic mapping for tenant"""
        payload: dict = {
            "physicalTopicName": physical_topic_name,
            "readOnly": read_only,
        }
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics/{logical_topic_name}"
        LOG.debug(f"create_tenant_topic_mapping path {_path}")
        req = self.proxy.client.post(
            _path,
            headers=self.proxy.client.json_headers,
            json=payload,
        )
        return req

    def list_tenant_topics_mappings(
        self, tenant_id: str, as_list: bool = False
    ) -> Union[Response, list[dict]]:
        """Lists all the tenant topic mappings"""
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics"
        LOG.debug(f"list_tenant_topics_mappings path {_path}")
        try:
            req = self.proxy.client.get(
                _path,
                headers={"Accept": "application/json"},
            )
            if as_list:
                return req.json()
            return req
        except GenericNotFound as error:
            raise TenantNotFound(tenant_id)

    def delete_all_tenant_topics_mappings(self, tenant_id: str) -> Response:
        """Deletes all the topic mappings for a given tenant"""
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics"
        LOG.debug(f"delete_all_tenant_topics_mappings path {_path}")
        try:
            req = self.proxy.client.delete(_path)
            return req
        except GenericNotFound as error:
            raise TenantNotFound(tenant_id)

    def delete_tenant_topic_mapping(
        self, tenant_id: str, logical_topic_name: str
    ) -> Response:
        """Deletes a specific topic mapping for a given tenant"""
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics/{logical_topic_name}"
        LOG.debug(f"delete_tenant_topic_mapping path {_path}")
        try:
            req = self.proxy.client.delete(_path)
            return req
        except GenericNotFound:
            raise TopicOrTenantNotFound(tenant_id, logical_topic_name)
