# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from requests import Response

from cdk_proxy_api_client.proxy_api import ApiApplication


class UserMappings(ApiApplication):
    """
    https://developers.conduktor.io/#tag/User-mappings
    """

    app_path: str = "admin/userMappings/v1"

    def create_mapping(self, vcluster: str, username: str) -> Response:
        """
        https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_createUserMapping
        https://developers.conduktor.io/admin/userMappings/v1/vcluster/{vcluster}
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster}"
        payload: dict = {
            "username": username,
        }
        req = self.proxy.client.post(_path, json=payload)
        return req

    def delete_mapping(self, vcluster: str, username: str) -> Response:
        """
        https://developers.conduktor.io/admin/userMappings/v1/vcluster/{vcluster}/username/{username}
        https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_deleteUserMapping
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster}/username/{username}"
        req = self.proxy.client.delete(_path)
        return req

    def list_mappings(self, vcluster: str) -> Response:
        """
        https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_listUserMappings
        https://developers.conduktor.io/admin/userMappings/v1/vcluster/{vcluster}
        """
        _path: str = f"{self.base_path}/vcluster/{vcluster}"
        req = self.proxy.client.get(_path)
        return req
