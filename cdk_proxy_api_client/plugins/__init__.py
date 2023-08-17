# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import Union
from urllib.parse import quote

from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.errors import GenericNotFound
from cdk_proxy_api_client.proxy_api import ApiApplication


class Plugins(ApiApplication):
    app_path: str = "admin/plugins"

    def list_all_plugins(self, extended: bool = False, as_list: bool = False) -> Union[Response, list]:
        """
        Docs: https://developers.conduktor.io/#tag/Plugins/operation/Plugins_v1_getPlugins
        Path: /admin/plugins/v1
        Docs: https://developers.conduktor.io/#tag/Plugins/operation/Plugins_v1_getPluginsExtended
        Path: /admin/plugins/v1/extended
        """
        _path = self.base_path
        if extended:
            _path = f"{self.base_path}/extended"

        LOG.debug("list_all_plugins path: {}".format(_path))
        req = self.proxy.client.get(_path)
        if as_list:
            return req.json()["plugins"]
        return req
