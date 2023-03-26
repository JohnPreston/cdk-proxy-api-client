#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import Union

from requests import Response

from cdk_proxy_api_client.common.logging import LOG
from cdk_proxy_api_client.proxy_api import ApiApplication


class AdminAuth(ApiApplication):
    """Class to managed admin/auth endpoint"""

    app_path: str = "admin/auth"

    def create_tenant_credentials(
        self,
        tenant_id: str,
        token_lifetime_seconds: int = None,
        token_only: bool = False,
    ) -> Union[Response, str]:
        """Creates a new token for a given tenant name. Default lifetime 900s (15 minutes)"""
        payload: dict = {
            "lifeTimeSeconds": token_lifetime_seconds if token_lifetime_seconds else 900
        }
        _path: str = f"{self.base_path}/tenants/{tenant_id}"
        LOG.debug(f"create_tenant_credentials path {_path}")
        req = self.proxy.client.post(
            _path,
            json=payload,
            headers=self.proxy.client.json_headers,
        )
        if token_only:
            return req.json()["token"]
        return req
