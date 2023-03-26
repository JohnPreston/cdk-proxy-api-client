#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from cdk_proxy_api_client.client_wrapper import ApiClient

if TYPE_CHECKING:
    from requests import Response


class ProxyClient:
    version: str = "v1beta1"

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


class Multitenancy(ApiApplication):
    app_path: str = "admin/multitenancy"

    def list_tenants(self, as_list: bool = False) -> Union[Response, list[str]]:
        _path: str = f"{self.base_path}/tenants"
        print("list_tenants path", _path)
        req = self.proxy.client.get(_path, headers={"Accept": "application/json"})
        if as_list:
            return req.json()["tenants"]
        return req
