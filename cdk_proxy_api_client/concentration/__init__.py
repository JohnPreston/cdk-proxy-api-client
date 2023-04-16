#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>


from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.proxy_api import ApiApplication, Multitenancy


class TenantContentrationMapping(ApiApplication):
    app_path: str = "topicMappings"

    @property
    def base_path(self) -> str:
        return f"/{self.app_path}"

    def create_tenant_concentration(
        self,
        tenant_id: str,
        logical_regex: str,
        physical_topic_name: str,
        cluster_id: str = None,
    ) -> Response:
        """
        Creates a concentration topic mapping for a given tenant.
        The
        :param tenant_id:
        :param logical_regex:
        :param physical_topic_name:
        :param cluster_id:
        :return:
        """
        payload: dict = {"isConcentrated": True, "topicName": physical_topic_name}
        if cluster_id:
            payload["clusterId"] = cluster_id

        _path: str = f"{self.base_path}/{tenant_id}/{logical_regex}"
        LOG.debug(f"create_tenant_topic_mapping path {_path}")
        req = self.proxy.client.post(
            _path, headers=self.proxy.client.json_headers, json=payload
        )
        return req
