# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import Union
from urllib.parse import quote

from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.proxy_api import ApiApplication


class Interceptors(ApiApplication):
    app_path: str = "admin/interceptors"

    def list_all_interceptors(self, as_list: bool = False) -> Union[Response, list]:
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

    def get_vcluster_intereceptor_info(
        self,
        vcluster_name: str,
        interceptor_name: str,
        as_dict: bool = False,
        username: str = None,
    ) -> Union[Response, dict]:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors-for-Virtual-Cluster/operation/Interceptor_v1_getClusterInterceptor
        Path: /admin/interceptors/v1/vcluster/{vcluster}/interceptor/{interceptorName}
        Path: /admin/interceptors/v1/vcluster/{vcluster}/username/{username}/interceptors
        """
        if username:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}"
                f"/username/{username}/interceptor/{quote(interceptor_name)}"
            )
        else:
            _path: str = f"{self.base_path}/vcluster/{vcluster_name}/interceptor/{quote(interceptor_name)}"
        LOG.debug(f"get_vcluster_intereceptor_info path: {_path}")
        req = self.proxy.client.get(_path)
        if as_dict:
            return req.json()
        return req

    def list_vcluster_interceptors(
        self, vcluster_name: str, as_list: bool = False, username: str = None
    ) -> Union[Response, list]:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors-for-Virtual-Cluster/operation/Interceptor_v1_getClusterInterceptors
        Path: /admin/interceptors/v1/vcluster/{vcluster}/interceptors
        """
        if username:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}"
                f"/username/{username}/interceptors"
            )
        else:
            _path: str = f"{self.base_path}/vcluster/{vcluster_name}/interceptors"
        LOG.debug(f"list_vcluster_interceptors path: {_path}")
        req = self.proxy.client.get(_path)
        if as_list:
            return req.json()
        return req

    def create_vcluster_interceptor(
        self,
        vcluster_name: str,
        interceptor_name: str,
        plugin_class: str,
        priority: int,
        config: dict,
        username: str = None,
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors-for-Virtual-Cluster/operation/Interceptor_v1_createClusterInterceptor
        Path: /admin/interceptors/v1/vcluster/{vcluster}/interceptor/{interceptorName}
        """
        if username:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}"
                f"/username/{username}/interceptor/{quote(interceptor_name)}"
            )
        else:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}"
                f"/interceptor/{quote(interceptor_name)}"
            )
        _payload: dict = {
            "pluginClass": plugin_class,
            "priority": priority,
            "config": config,
        }
        LOG.debug(f"list_vcluster_interceptors path: {_path}")
        req = self.proxy.client.post(
            _path, json=_payload, headers=self.proxy.client.json_headers
        )
        return req

    def update_vcluster_interceptor(
        self,
        vcluster_name: str,
        interceptor_name: str,
        plugin_class: str,
        priority: int,
        config: dict,
        username: str = None,
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors-for-Virtual-Cluster/operation/Interceptor_v1_createClusterInterceptor
        Path: /admin/interceptors/v1/vcluster/{vcluster}/interceptor/{interceptorName}
        """
        if username:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}"
                f"/username/{username}/interceptor/{quote(interceptor_name)}"
            )
        else:
            _path: str = f"{self.base_path}/vcluster/{vcluster_name}/interceptor/{quote(interceptor_name)}"
        LOG.debug(f"update_vcluster_interceptor path: {_path}")
        _payload: dict = {
            "pluginClass": plugin_class,
            "priority": priority,
            "config": config,
        }
        LOG.debug(f"list_vcluster_interceptors path: {_path}")
        req = self.proxy.client.put(
            _path, json=_payload, headers=self.proxy.client.json_headers
        )
        return req

    def delete_vcluster_interceptor(
        self, vcluster_name: str, interceptor_name: str, username: str = None
    ) -> Response:
        """
        Docs: https://developers.conduktor.io/#tag/Interceptors-for-Virtual-Cluster/operation/Interceptor_v1_deleteClustertInterceptor
        Path: /admin/interceptors/v1/vcluster/{vcluster}/interceptor/{interceptorName}
        """
        if username:
            _path: str = (
                f"{self.base_path}/vcluster/{vcluster_name}"
                f"/username/{username}/interceptor/{quote(interceptor_name)}"
            )
        else:
            _path: str = f"{self.base_path}/vcluster/{vcluster_name}/interceptor/{quote(interceptor_name)}"
        LOG.debug(f"update_vcluster_interceptor path: {_path}")
        req = self.proxy.client.delete(_path)
        return req
