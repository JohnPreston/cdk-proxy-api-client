# cdk-proxy-api-client

API Client library to interact with Conduktor Proxy

Current version: v1beta1


## Getting started

First, create a Proxy Client

```python
from cdk_proxy_api_client.proxy_api import ApiClient, ProxyClient

api = ApiClient("localhost", port=8888, username="superUser", password="superUser")
proxy_client = ProxyClient(api)
```

### Features

Note: we assume you are re-using the ``proxy_client`` as shown above.

* Create new Token for a tenant

```python
from cdk_proxy_api_client.admin_auth import AdminAuth

admin = AdminAuth(proxy_client)
admin.create_tenant_credentials("a_tenant_name")
```

* List all topic mappings for a tenant

```python
from cdk_proxy_api_client.proxy_api import Multitenancy

tenants_mgmt = Multitenancy(proxy_client)
tenants = tenants_mgmt.list_tenants(as_list=True)
```

* Create a new mapping for a tenant
* Delete a tenant - topic mapping
* Delete all topic mappings for a tenant

```python
from cdk_proxy_api_client.tenant_mappings import TenantMappings

tenant_mappings_mgmt = TenantMappings(proxy_client)
tenant_mappings_mgmt.create_tenant_topic_mapping(
    "tenant_name", "logical_name", "real_name"
)
tenant_mappings_mgmt.delete_tenant_topic_mapping("tenant_name", "logical_name")
```

## Testing
The testing is for now very manual. See ``e2e_testing.py``

Pytest will be added later on
