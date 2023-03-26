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
from cdk_proxy_api_client.tenant_mappings import TenantTopicMappings

tenant_mappings_mgmt = TenantTopicMappings(proxy_client)
tenant_mappings_mgmt.create_tenant_topic_mapping(
    "tenant_name", "logical_name", "real_name"
)
tenant_mappings_mgmt.delete_tenant_topic_mapping("tenant_name", "logical_name")
```

## Testing
The testing is for now very manual. See ``e2e_testing.py``

Pytest will be added later on


## Tools & CLI

To simplify the usage of the client, you can use some CLI commands

```shell
usage: CDK Proxy CLI [-h] [--format OUTPUT_FORMAT] --username USERNAME --password PASSWORD --url URL {auth,tenant-topic-mappings,tenants} ...

positional arguments:
  {auth,tenant-topic-mappings,tenants}
                        Resources to manage
    auth                Manages proxy tenant token
    tenant-topic-mappings
                        Manages tenant mappings
    tenants             Manage tenants

optional arguments:
  -h, --help            show this help message and exit
  --format OUTPUT_FORMAT, --output-format OUTPUT_FORMAT
                        output format
  --username USERNAME
  --password PASSWORD
  --url URL

```

### cdk-cli tenant-topic-mappings

```shell
usage: CDK Proxy CLI tenant-topic-mappings [-h] {list,create,import-from-tenants-config,import-from-tenant,delete-all-mappings,delete-topic-mapping} ...

positional arguments:
  {list,create,import-from-tenants-config,import-from-tenant,delete-all-mappings,delete-topic-mapping}
                        Mappings management
    list                List tenant mappings
    create              Create a new tenant mapping
    import-from-tenants-config
                        Create topic mappings from existing tenants
    import-from-tenant  Import all topics from a existing tenant
    delete-all-mappings
                        Delete all topics mappings for a given tenant
    delete-topic-mapping
                        Delete a topic mapping for a given tenant

optional arguments:
  -h, --help            show this help message and exit
```

#### import-from-tenants-config

This command uses a configuration file that will be used to propagate mappings from one/multiple existing tenants to another.

example file:

```yaml
---
# example.config.yaml

tenant_name: application-01
ignore_duplicates_conflict: true
mappings:
  - logicalTopicName: data.stock
    physicalTopicName: data.stock
    readOnly: true
```

```shell
cdk-cli --username ${PROXY_USERNAME} \
        --password ${PROXY_PASSWORD} \
        --url ${PROXY_URL} \
        tenant-topic-mappings import-from-tenants-config -f example.config.yaml
```

### cdk-cli auth

```shell
cdk-cli auth --help
usage: CDK Proxy CLI auth [-h] {create} ...

positional arguments:
  {create}    Token actions to execute
    create    Create a new tenant proxy JWT Token

optional arguments:
  -h, --help  show this help message and exit
```

#### cdk-cli-create-tenant-token

Create a new user tenant token

```shell
cdk-cli \
        --username ${PROXY_USERNAME} \
        --password ${PROXY_PASSWORD} \
        --url ${PROXY_URL} \
        auth create \
        --lifetime-in-seconds 3600  \
        --tenant-name js-fin-panther-stg
```

### cdk-cli tenants

Manage tenants

```shell
cdk-cli tenants --help
usage: CDK Proxy CLI tenants [-h] {list} ...

positional arguments:
  {list}      Manage tenants
    list      List tenants

optional arguments:
  -h, --help  show this help message and exit
```
