# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 John Mille <john@ews-network.net>

from __future__ import annotations

from urllib.parse import quote

from requests import Response

from cdk_proxy_api_client.proxy_api import ApiApplication


class UserMappings(ApiApplication):
    """
    https://developers.conduktor.io/#tag/User-mappings
    """

    app_path: str = "admin/userMappings"

    def set_update_payload(
        self,
        username: str,
        principal: str = None,
        groups: list = None,
        vcluster_name: str = None,
    ):
        if groups is None:
            groups = []
        if vcluster_name:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}/username/{quote(username)}"
            )
        else:
            _path: str = f"{self.base_path}/username/{quote(username)}"
        payload: dict = {
            "username": username,
            "principal": principal if principal else username,
            "groups": groups,
        }
        return payload, _path

    def create_mapping(
        self,
        username: str,
        principal: str = None,
        groups: list[str] = None,
        vcluster_name: str = None,
    ) -> Response:
        """
        Docs:
        * https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_createOrUpdatePassThroughUserMapping
        * https://developers.conduktor.io/#tag/VCluster-User-mappings/operation/Clusters_v1_createOrUpdateUserMapping

        Paths:
        * /admin/userMappings/v1/username/{username}
        * /admin/userMappings/v1/vcluster/{vcluster}/username/{username}
        """
        _payload, _ = self.set_update_payload(
            username, principal, groups, vcluster_name
        )
        if vcluster_name:
            _path: str = f"{self.base_path}/vcluster/{vcluster_name}"
        else:
            _path: str = self.base_path
        req = self.proxy.client.post(_path, json=_payload)
        return req

    def update_mapping(
        self,
        username: str,
        principal: str = None,
        groups: list[str] = None,
        vcluster_name: str = None,
    ) -> Response:
        """
        Docs:
        * https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_createOrUpdatePassThroughUserMapping
        * https://developers.conduktor.io/#tag/VCluster-User-mappings/operation/Clusters_v1_createOrUpdateUserMapping

        Paths:
        * /admin/userMappings/v1/username/{username}
        * /admin/userMappings/v1/vcluster/{vcluster}/username/{username}
        """
        _payload, _path = self.set_update_payload(
            username, principal, groups, vcluster_name
        )
        req = self.proxy.client.put(_path, json=_payload)
        return req

    def delete_mapping(self, username: str, vcluster_name: str = None) -> Response:
        """
        https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_deletePassThroughUserMapping
        https://developers.conduktor.io/#tag/VCluster-User-mappings/operation/Clusters_v1_deleteUserMapping

        Path:
        * /admin/userMappings/v1/username/{username}
        """
        if vcluster_name:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}/username/{quote(username)}"
            )
        else:
            _path: str = f"{self.base_path}/username/{quote(username)}"
        req = self.proxy.client.delete(_path)
        return req

    def get_user_mapping(self, username: str, vcluster_name: str = None) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_getPassThroughUserMapping
        Path:
        * /admin/userMappings/v1/username/{username}
        * /admin/userMappings/v1/vcluster/{vcluster}/username/{username}
        """
        if vcluster_name:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}/username/{quote(username)}"
            )
        else:
            _path: str = f"{self.base_path}/username/{quote(username)}"
        req = self.proxy.client.get(_path)
        return req

    def list_mappings(self, vcluster_name: str = None) -> Response:
        """
        https://developers.conduktor.io/#tag/User-mappings/operation/Clusters_v1_listUserMappings
        https://developers.conduktor.io/admin/userMappings/v1/vcluster/{vcluster}
        """
        if vcluster_name:
            _path: str = f"{self.base_path}/vcluster/{vcluster_name}"
        else:
            _path: str = self.base_path
        req = self.proxy.client.get(_path)
        return req

    def list_mappings_detailed(self, vcluster_name: str = None) -> list[dict]:
        """
        Given the list of mappings only returns the usernames, we might want the full picture
        about the identity.
        For each username, retrieve the whole identity.
        """
        usernames: list[str] = self.list_mappings(vcluster_name=vcluster_name).json()
        identities: list[dict] = []
        for username in usernames:
            identities.append(self.get_user_mapping(username, vcluster_name).json())
        return identities
