#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from argparse import ArgumentParser

TENANT_PARSER = ArgumentParser(add_help=False)
TENANT_PARSER.add_argument(
    "--tenant-name", required=True, help="Name of the tenant to make operations for"
)


def set_admin_auth_parser(token_parser: ArgumentParser):
    auth_admin_subparsers = token_parser.add_subparsers(
        dest="action", help="Token actions to execute"
    )
    tenant_token_create_parser = auth_admin_subparsers.add_parser(
        name="create",
        help="Create a new tenant proxy JWT Token",
        parents=[TENANT_PARSER],
    )
    tenant_token_create_parser.add_argument(
        "--lifetime-in-seconds",
        dest="token_lifetime_in_seconds",
        type=int,
        help="Token lifetime in seconds. Sets expiry. Defaults 1 day (86400)",
        default=86400,
    )


def set_tenant_mappings_subparsers(mappings_parser: ArgumentParser):
    mappings_subparser = mappings_parser.add_subparsers(
        dest="action", help="Mappings management"
    )
    mappings_subparser.add_parser(
        name="list",
        help="List tenant mappings",
        parents=[TENANT_PARSER],
    )
    mappings_subparser.add_parser(
        name="create",
        help="Create a new tenant mapping",
        parents=[TENANT_PARSER],
    )
    import_from_tenants_parser = mappings_subparser.add_parser(
        name="import-from-tenants-config",
        help="Create topic mappings from existing tenants",
    )
    import_from_tenants_parser.add_argument(
        "-f",
        "--import-config-file",
        dest="import_config_file",
        help="Path to the mappings import file",
        required=True,
        type=str,
    )
    import_from_tenant_parser = mappings_subparser.add_parser(
        name="import-from-tenant",
        help="Import all topics from a existing tenant",
        parents=[TENANT_PARSER],
    )
    import_from_tenant_parser.add_argument(
        "--src",
        "--source-tenant",
        dest="source_tenant",
        help="Name of the source tenant to import the mappings from",
        type=str,
        required=True,
    )
    delete_all_mappings_parser = mappings_subparser.add_parser(
        name="delete-all-mappings",
        help="Delete all topics mappings for a given tenant",
        parents=[TENANT_PARSER],
    )
    delete_topic_mapping_parser = mappings_subparser.add_parser(
        name="delete-topic-mapping",
        help="Delete a topic mapping for a given tenant",
        parents=[TENANT_PARSER],
    )
    delete_topic_mapping_parser.add_argument(
        "--logical-topic-name",
        dest="logicalTopicName",
        required=True,
        help="Topic name as seen in the tenant.",
    )


def set_parser():
    main_parser = ArgumentParser("CDK Proxy CLI", add_help=True)
    main_parser.add_argument(
        "--format",
        "--output-format",
        dest="output_format",
        help="output format",
        default="yaml",
    )
    main_parser.add_argument(
        "--log-level", dest="loglevel", type=str, help="Set loglevel", required=False
    )
    main_parser.add_argument("--username", required=True)
    main_parser.add_argument("--password", required=True)
    main_parser.add_argument("--url", required=True)
    cmd_parser = main_parser.add_subparsers(dest="category", help="Resources to manage")
    auth_admin_parser = cmd_parser.add_parser(
        name="auth",
        help="Manages proxy tenant token",
    )
    set_admin_auth_parser(auth_admin_parser)

    mappings_parser = cmd_parser.add_parser(
        name="tenant-topic-mappings", help="Manages tenant mappings"
    )
    set_tenant_mappings_subparsers(mappings_parser)

    tenants_parser = cmd_parser.add_parser(name="tenants", help="Manage tenants")
    tenants_subparser = tenants_parser.add_subparsers(
        dest="action", help="Manage tenants"
    )
    tenants_subparser.add_parser(name="list", help="List tenants", parents=[])
    return main_parser
