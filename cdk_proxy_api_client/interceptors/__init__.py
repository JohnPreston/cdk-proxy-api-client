# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import Union
from urllib.parse import quote

from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.proxy_api import ApiApplication


class Interceptors(ApiApplication):
    app_path: str = "admin/interceptors"

    def generate_interceptor_path(
        self,
        interceptor_name: str,
        is_global: bool = False,
        vcluster_name: str = None,
        username: str = None,
        group_name: str = None,
    ) -> str:
        """
        Generates the path to interceptors for username, groups, vClusters, etc.

        Docs:
        * https://developers.conduktor.io/#tag/Interceptors/operation/Interceptor_v1_createPassThroughClusterInterceptor
        * https://developers.conduktor.io/#tag/Group-Interceptors/operation/Interceptor_v1_createPassThroughGroupInterceptor
        * https://developers.conduktor.io/#tag/Username-Interceptors/operation/Interceptor_v1_createPassThroughAccountInterceptor
        * https://developers.conduktor.io/#tag/Virtual-Cluster-Interceptors/operation/Interceptor_v1_createClusterInterceptor
        * https://developers.conduktor.io/#tag/VCluster-Username-Interceptors/operation/Interceptor_v1_createAccountInterceptor
        * https://developers.conduktor.io/#tag/VCluster-Group-Interceptors/operation/Interceptor_v1_createGroupInterceptor

        Paths:
        * /admin/interceptors/v1/interceptor/{interceptorName}
        * /admin/interceptors/v1/group/{group}/interceptor/{interceptorName}
        * /admin/interceptors/v1/username/{username}/interceptor/{interceptorName}
        * /admin/interceptors/v1/vcluster/{vcluster}/interceptor/{interceptorName}
        * /admin/interceptors/v1/vcluster/{vcluster}/username/{username}/interceptor/{interceptorName}
        * /admin/interceptors/v1/vcluster/{vcluster}/group/{group}/interceptor/{interceptorName}

        """
        if is_global:
            _path: str = f"{self.base_path}/global/interceptor/{interceptor_name}"
            LOG.debug("global interceptor path: %s" % _path)
            return _path
        if username and group_name:
            raise ValueError("username and group_name are mutually exclusive")
        if vcluster_name:
            if username:
                _path: str = f"{self.base_path}/vcluster/{quote(vcluster_name)}/username/{quote(username)}/interceptor/{quote(interceptor_name)}"
            elif group_name:
                _path: str = f"{self.base_path}/vcluster/{quote(vcluster_name)}/group/{quote(group_name)}/interceptor/{quote(interceptor_name)}"
            else:
                _path: str = f"{self.base_path}/vcluster/{quote(vcluster_name)}/interceptor/{quote(interceptor_name)}"
            LOG.info("vCluster interceptor path: %s" % _path)
            return _path

        if username:
            _path: str = f"{self.base_path}/username/{quote(username)}/interceptor/{quote(interceptor_name)}"
        elif group_name:
            _path: str = f"{self.base_path}/group/{quote(group_name)}/interceptor/{quote(interceptor_name)}"
        else:
            _path: str = f"{self.base_path}/interceptor/{quote(interceptor_name)}"
        LOG.debug("passthrough interceptor path: %s" % _path)
        return _path

    def list_all_interceptors(self, as_list: bool = False) -> Response | list:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors-for-Virtual-Cluster/operation/Interceptor_v1_getInterceptors
        Path: /admin/interceptors/v1/interceptors
        """
        _path: str = f"{self.base_path}/interceptors"
        LOG.debug(f"list_all_interceptors path: {_path}")
        req = self.proxy.client.get(_path)
        if as_list:
            return req.json()
        return req

    def get_all_gw_interceptors(self) -> Response:
        """
        Returns all the interceptors (for users, groups, vClusters etc.).

        Docs: https://developers.conduktor.io/#tag/Interceptors/operation/Interceptor_v1_getInterceptors
        Path: /admin/interceptors/v1/all
        """
        _path: str = f"{self.base_path}/all"
        LOG.debug(f"get_all_interceptors path: {_path}")
        req = self.proxy.client.get(_path)
        return req

    def get_interceptor(
        self,
        interceptor_name,
        is_global: bool = False,
        vcluster_name: str = None,
        username: str = None,
        group_name: str = None,
    ) -> Response | dict:
        _path = self.generate_interceptor_path(
            interceptor_name, is_global, vcluster_name, username, group_name
        )
        LOG.debug(f"get_interceptor path: {_path}")
        req = self.proxy.client.get(_path)
        return req

    def create_interceptor(
        self,
        interceptor_name,
        interceptor_config: dict,
        is_global: bool = False,
        vcluster_name: str = None,
        username: str = None,
        group_name: str = None,
    ) -> Response:
        _path = self.generate_interceptor_path(
            interceptor_name, is_global, vcluster_name, username, group_name
        )
        LOG.debug(f"create_interceptor path: {_path}")
        req = self.proxy.client.post(
            _path, json=interceptor_config, headers=self.proxy.client.json_headers
        )
        return req

    def update_interceptor(
        self,
        interceptor_name,
        interceptor_config: dict,
        is_global: bool = False,
        vcluster_name: str = None,
        username: str = None,
        group_name: str = None,
    ) -> Response:
        """
        Update an interceptor for username, group, vCluster etc.
        """
        _path = self.generate_interceptor_path(
            interceptor_name, is_global, vcluster_name, username, group_name
        )
        LOG.debug(f"update_interceptor path: {_path}")
        req = self.proxy.client.put(
            _path, json=interceptor_config, headers=self.proxy.client.json_headers
        )
        return req

    def delete_interceptor(
        self,
        interceptor_name,
        is_global: bool = False,
        vcluster_name: str = None,
        username: str = None,
        group_name: str = None,
    ) -> Response:
        """
        Delete an interceptor for username, group, vCluster etc.
        """
        _path = self.generate_interceptor_path(
            interceptor_name, is_global, vcluster_name, username, group_name
        )
        LOG.debug(f"create_interceptor path: {_path}")
        req = self.proxy.client.delete(_path)
        return req

    def get_all_interceptor(
        self,
        is_global: bool = False,
        vcluster_name: str = None,
        username: str = None,
        group_name: str = None,
    ) -> Response:
        """
        Retrieves all the interceptors for a username, group, vCluster, etc.
        """
        if username and group_name:
            raise ValueError("username and group_name are mutually exclusive")
        if is_global:
            _path: str = f"{self.base_path}/global"
            LOG.debug("global interceptor path: %s" % _path)
            return self.proxy.client.get(_path)

        if vcluster_name:
            if username and not group_name:
                _path: str = f"{self.base_path}/vcluster/{quote(vcluster_name)}/username/{quote(username)}"
            elif not username and group_name:
                _path: str = f"{self.base_path}/vcluster/{quote(vcluster_name)}/group/{quote(group_name)}"
            else:
                _path: str = f"{self.base_path}/vcluster/{quote(vcluster_name)}"
            LOG.debug("vCluster interceptor path: %s" % _path)
            return self.proxy.client.get(_path)

        if username:
            _path: str = f"{self.base_path}/username/{quote(username)}"
        elif group_name:
            _path: str = f"{self.base_path}/group/{quote(group_name)}"
        else:
            _path: str = f"{self.base_path}"
        LOG.debug("passthrough interceptor path: %s" % _path)

        req = self.proxy.client.get(_path)
        return req

    def get_target_resolve(self, payload: dict) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors/operation/Interceptors_v1_resolveTargeting
        Path: /admin/interceptors/v1/resolve
        """
        _path: str = f"{self.base_path}/resolve"
        LOG.debug(f"get_target_resolve path: {_path}")
        req = self.proxy.client.post(
            _path, json=payload, headers=self.proxy.client.json_headers
        )
        return req
