# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 John Mille <john@ews-network.net>


class TopicOrVirtualClusterNotFound(Exception):
    def __init__(self, tenant_id: str, logical_topic_name: str):
        super().__init__(f"No mapping for {tenant_id} and {logical_topic_name}")


class VirtualClusterNotFound(Exception):
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant {tenant_id} not found")
