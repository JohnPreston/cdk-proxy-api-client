#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import TYPE_CHECKING

from cdk_proxy_api_client.client_wrapper import ApiClient

if TYPE_CHECKING:
    pass


class ProxyClient:
    version: str = "v1"

    def __init__(self, client: ApiClient):
        self._client = client

    @property
    def client(self) -> ApiClient:
        return self._client

    @classmethod
    def set_version(cls, version: str, client: ApiClient):
        ProxyClient.version = version
        return cls(client)


class ApiApplication:
    app_path: str = ""

    def __init__(self, proxy: ProxyClient):
        self._proxy = proxy

    @property
    def proxy(self) -> ProxyClient:
        return self._proxy

    @property
    def base_path(self) -> str:
        return f"/{self.app_path}/{self.proxy.version}"
