#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John Mille <john@ews-network.net>


from cdk_proxy_api_client.client_wrapper import ApiClient


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
    app_path: str = "auth"

    @classmethod
    def change_version(cls, version: str):
        ProxyAuth.version = version

    def create_tenant_credentials(
        self,
        tenant_id: str,
        token_lifetime_seconds: int = None,
        token_only: bool = False,
    ):
        if token_lifetime_seconds:
            payload: dict = {"lifeTimeSeconds": token_lifetime_seconds}
            req = self.proxy.client.post(f"{self.base_path}/{tenant_id}", json=payload)
        else:
            req = self.proxy.client.post(f"{self.base_path}/{tenant_id}")
        if token_only:
            return req["token"]
        return req


class Multitenancy(ApiApplication):
    app_path: str = "multitenancy"

    def list_tenants(self) -> list[str]:
        req = self.proxy.client.get(f"{self.app_path}/tenants")
        return req


class TenantMappings(ApiApplication):
    app_path: str = f"{Multitenancy.app_path}/"

    def list_tenant_topics_mappings(self, tenant_id: str) -> list[dict]:
        req = self.proxy.client.get(
            f"{self.app_path}/tenants/{tenant_id}",
            headers={"Accept": "application/json"},
        )
        return req

    def delete_all_tenant_topics_mappings(self, tenant_id: str):
        req = self.proxy.client.delete(f"{self.app_path}/tenants/{tenant_id}")

    def delete_tenant_topic_mapping(
        self, tenant_id: str, logical_topic_name: str
    ) -> None:
        req = self.proxy.client.delete(
            f"{self.app_path}/tenants/{tenant_id}/topics/{logical_topic_name}"
        )

    def create_tenant_topic_mapping(
        self,
        tenant_id: str,
        logical_topic_name: str,
        physical_topic_name: str,
        read_only: bool = False,
    ):
        payload: dict = {
            "physicalTopicName": physical_topic_name,
            "readOnly": read_only,
        }
        req = self.proxy.client.post(
            f"{self.app_path}/tenants/{tenant_id}/topics/{logical_topic_name}",
            headers=self.proxy.client.json_headers,
            json=payload,
        )
