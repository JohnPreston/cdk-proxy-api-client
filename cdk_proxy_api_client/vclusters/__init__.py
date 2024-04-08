#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2024 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import Union
from urllib.parse import quote

from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.errors import GenericNotFound
from cdk_proxy_api_client.exceptions import (
    TopicOrVirtualClusterNotFound,
    VirtualClusterNotFound,
)
from cdk_proxy_api_client.proxy_api import ApiApplication


class VirtualClusters(ApiApplication):
    app_path: str = "admin/vclusters"

    def list_vclusters(self, as_list: bool = False) -> Response | list[str]:
        _path: str = f"{self.base_path}/"
        LOG.debug(f"list_vclusters path {_path}")
        req = self.proxy.client.get(_path, headers={"Accept": "application/json"})
        if as_list:
            return req.json()
        return req

    def create_vcluster_user_token(
        self,
        vcluster: str,
        username: str = None,
        lifetime_in_seconds: int = 86400,
        token_only: bool = False,
    ) -> Response | str:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/Auth_v1_createClusterAccountToken
        Path: /admin/vclusters/v1/vcluster/{vcluster}/username/{username}
        """
        if not username:
            username = vcluster
        payload = {"lifeTimeSeconds": lifetime_in_seconds}
        _path: str = f"{self.base_path}/vcluster/{vcluster}/username/{username}"
        LOG.debug(f"create_vcluster_user_token path {_path}")
        req = self.proxy.client.post(
            _path, headers={"Accept": "application/json"}, json=payload
        )
        if token_only:
            return req.json()["token"]
        return req

    def create_concentration_rule(
        self,
        vcluster_name: str,
        pattern: str,
        delete_topic_name: str,
        compact_topic_name: str = None,
        compact_delete_topic_name: str = None,
        cluster_id: str = None,
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/ConcentrationRule_createConcentrationRule
        Path: /admin/vclusters/v1/vcluster/{vcluster}/concentration-rules
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster_name}/concentration-rules"
        LOG.debug(f"create_concentration_rule path {_path}")
        payload: dict = {
            "pattern": pattern,
            "physicalTopicName": delete_topic_name,
            "physicalTopicCompactedName": compact_topic_name
            if compact_topic_name
            else f"{delete_topic_name}_compacted",
            "physicalTopicCompactedDeletedName": compact_delete_topic_name
            if compact_delete_topic_name
            else f"{delete_topic_name}_compact_delete",
        }
        if cluster_id:
            payload["clusterId"] = cluster_id
        req = self.proxy.client.post(
            _path, headers={"Accept": "application/json"}, json=payload
        )
        return req

    def get_concentration_rules(self, vcluster_name: str) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/ConcentrationRule_getConcentrationRules
        Path: /admin/vclusters/v1/vcluster/{vcluster}/concentration-rules
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster_name}/concentration-rules"
        LOG.debug(f"get_concentration_rules path {_path}")
        req = self.proxy.client.get(
            _path,
        )
        return req

    def delete_concentration_rule(self, vcluster_name: str) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/ConcentrationRule_deleteConcentrationRule
        Path: /admin/vclusters/v1/vcluster/{vcluster}/concentration-rules
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster_name}/concentration-rules"
        LOG.debug(f"delete_concentration_rule path {_path}")
        req = self.proxy.client.delete(
            _path,
        )
        return req

    def create_vcluster_topic_mapping(
        self,
        vcluster: str,
        logical_topic_name: str,
        physical_topic_name: str,
        mapping_type: str = "alias",
        read_only: bool = False,
        cluster_id: str = None,
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/Clusters_v1_createClusterTopicMapping
        Path: /admin/vclusters/v1/vcluster/{vcluster}/topics/{logicalTopicName}
        """
        if mapping_type not in ["alias", "concentrated"]:
            raise ValueError("mapping_type must be alias or concentrated")
        if mapping_type == "concentrated":
            raise ValueError("Must use concentration rules functions.")
        _path: str = (
            f"{self.base_path}/vcluster/{vcluster}/topics/{quote(logical_topic_name)}"
        )
        payload: dict = {
            "physicalTopicName": physical_topic_name,
            "readOnly": read_only,
            "type": mapping_type,
        }
        if cluster_id:
            payload["clusterId"] = cluster_id
        LOG.debug(f"create_vcluster_topic_mapping path: {_path}")
        req = self.proxy.client.post(_path, json=payload)
        return req

    def list_vcluster_topic_mappings(
        self, vcluster: str, as_list: bool = False
    ) -> Response | list[dict]:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/Clusters_v1_listClusterTopicMapping
        Path: /admin/vclusters/v1/vcluster/{vcluster}/topics
        """
        _path = f"{self.base_path}/vcluster/{vcluster}/topics"
        LOG.debug(f"list_vcluster_topic_mappings path: {_path}")
        try:
            req = self.proxy.client.get(_path, headers={"Accept": "application/json"})
            if as_list:
                return req.json()
            return req
        except GenericNotFound:
            raise VirtualClusterNotFound(vcluster)

    def delete_vcluster_topics_mappings(self, vcluster: str) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/Clusters_v1_deleteClusters
        Path: /admin/vclusters/v1/vcluster/{vcluster}/topics
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster}/topics"
        LOG.debug(f"delete_vcluster_topics_mappings path: {_path}")
        try:
            req = self.proxy.client.delete(_path)
            return req
        except GenericNotFound as error:
            raise VirtualClusterNotFound(vcluster)

    def delete_vcluster_topic_mapping(
        self, vcluster: str, logical_topic_name: str
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/Clusters_v1_deleteClusterTopicMapping
        Path: /admin/vclusters/v1/vcluster/{vcluster}/topics/{logicalTopicName}
        """
        _path: str = (
            f"{self.base_path}/vcluster/{vcluster}/topics/{quote(logical_topic_name)}"
        )
        LOG.debug(f"delete_tenant_topic_mapping path {_path}")
        try:
            req = self.proxy.client.delete(_path)
            return req
        except GenericNotFound:
            raise TopicOrVirtualClusterNotFound(vcluster, logical_topic_name)

    def reroute_vcluster_topic_mappings(
        self, src_vcluster: str, dest_vcluster: str
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Virtual-Clusters/operation/Clusters_v1_clusterRerouting
        Path: /admin/vclusters/v1/rerouting/{fromVCluster}/{toVCluster}

        :param src_vcluster: Source vcluster to move the mappings from
        :param dest_vcluster: Destination vcluster to set the mappings to
        """
        _path: str = f"{self.base_path}/rerouting/{src_vcluster}/{dest_vcluster}"
        req = self.proxy.client.post(_path)
        return req
