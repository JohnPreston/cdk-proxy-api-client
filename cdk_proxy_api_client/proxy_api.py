#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>


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


class ProxyAuth(ApiApplication):
    app_path: str = "admin/auth"

    def create_tenant_credentials(
        self,
        tenant_id: str,
        token_lifetime_seconds: int = None,
        token_only: bool = False,
    ) -> Union[Response, str]:
        payload: dict = {
            "lifeTimeSeconds": token_lifetime_seconds if token_lifetime_seconds else 900
        }
        req = self.proxy.client.post(
            f"{self.base_path}/tenants/{tenant_id}",
            json=payload,
            headers=self.proxy.client.json_headers,
        )
        if token_only:
            return req.json()["token"]
        return req


class Multitenancy(ApiApplication):
    app_path: str = "admin/multitenancy"

    def list_tenants(self, as_list: bool = False) -> Union[Response, list[str]]:
        _path: str = f"{self.base_path}/tenants"
        print("list_tenants path", _path)
        req = self.proxy.client.get(_path, headers={"Accept": "application/json"})
        if as_list:
            return req.json()
        return req


class TenantMappings(ApiApplication):
    app_path: str = f"{Multitenancy.app_path}"

    def create_tenant_topic_mapping(
        self,
        tenant_id: str,
        logical_topic_name: str,
        physical_topic_name: str,
        read_only: bool = False,
    ) -> Response:
        payload: dict = {
            "physicalTopicName": physical_topic_name,
            "readOnly": read_only,
        }
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics/{logical_topic_name}"
        print("create_tenant_topic_mapping path", _path)
        req = self.proxy.client.post(
            _path,
            headers=self.proxy.client.json_headers,
            json=payload,
        )
        return req

    def list_tenant_topics_mappings(
        self, tenant_id: str, as_list: bool = False
    ) -> Union[Response, list[dict]]:
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics"
        print("list_tenant_topics_mappings path", _path)
        req = self.proxy.client.get(
            _path,
            headers={"Accept": "application/json"},
        )
        if as_list:
            return req.json()
        return req

    def delete_all_tenant_topics_mappings(self, tenant_id: str) -> Response:
        _path: str = f"{self.base_path}/tenants/{tenant_id}"
        print("delete_all_tenant_topics_mappings path", _path)
        req = self.proxy.client.delete(_path)
        return req

    def delete_tenant_topic_mapping(
        self, tenant_id: str, logical_topic_name: str
    ) -> Response:
        _path: str = f"{self.base_path}/tenants/{tenant_id}/topics/{logical_topic_name}"
        print("delete_tenant_topic_mapping path", _path)
        req = self.proxy.client.delete(_path)
        return req
