#   SPDX-License-Identifier: Apache-2.0
#   Copyright 2023 John Mille <john@ews-network.net>

from __future__ import annotations

from argparse import ArgumentParser
from os import environ

VCLUSTER_PARSER = ArgumentParser(add_help=False)
VCLUSTER_PARSER.add_argument(
    "--vcluster-name",
    dest="vcluster_name",
    required=True,
    help="Name of the vcluster to make operations for",
)


def set_vclusters_actions_parsers(vclusters_subparsers):
    """Creates all the parser and subparsers for vClusters API endpoints"""

    # List all
    list_parser = vclusters_subparsers.add_parser(
        name="list", help="List all vClusters"
    )

    # Auth / Token
    tenant_token = vclusters_subparsers.add_parser(
        name="auth",
        help="Create a new JWT for vCluster/Username",
        parents=[VCLUSTER_PARSER],
    )
    tenant_token_subparsers = tenant_token.add_subparsers(dest="sub_action")
    tenant_token_create_parser = tenant_token_subparsers.add_parser(name="create")
    tenant_token_create_parser.add_argument(
        "--lifetime-in-seconds",
        dest="token_lifetime_in_seconds",
        type=int,
        help="Token lifetime in seconds. Sets expiry. Defaults 1 day (86400)",
        default=86400,
    )
    tenant_token_create_parser.add_argument(
        "--username",
        type=str,
        help="Sets the username to use for sasl.username to connect to the virtual cluster",
        required=False,
    )
    set_vcluster_mappings_actions(vclusters_subparsers)


def set_vcluster_mappings_actions(vclusters_subparsers):
    # Mappings
    mappings_parser = vclusters_subparsers.add_parser(
        name="mappings",
        help="Manages vCluster mappings",
        parents=[VCLUSTER_PARSER],
    )
    mappings_subparsers = mappings_parser.add_subparsers(dest="sub_action")
    mappings_subparsers.add_parser(
        name="list",
        help="List vCluster mappings",
    )
    create_parser = mappings_subparsers.add_parser(
        name="create",
        help="Create a new vCluster mapping",
    )
    create_parser.add_argument("--logical-topic-name", type=str, required=True)
    create_parser.add_argument("--physical-topic-name", type=str, required=True)
    create_parser.add_argument(
        "--read-only",
        required=False,
        default=False,
        dest="ReadOnly",
        action="store_true",
        help="Creates mapping in ReadOnly (defaults to Read-Write)",
    )
    create_parser.add_argument(
        "--concentrated",
        required=False,
        default=False,
        action="store_true",
        help="Create concentrated mapping",
    )
    # Delete action parsers
    delete_all_mappings_parser = mappings_subparsers.add_parser(
        name="delete-all-mappings",
        help="Delete all topics mappings for a given vCluster",
        parents=[VCLUSTER_PARSER],
    )
    delete_topic_mapping_parser = mappings_subparsers.add_parser(
        name="delete-topic-mapping",
        help="Delete a topic mapping for a given vCluster",
        parents=[VCLUSTER_PARSER],
    )
    delete_topic_mapping_parser.add_argument(
        "--logical-topic-name",
        dest="logicalTopicName",
        required=True,
        help="Topic name as seen in the vCluster.",
    )

    # Custom actions
    import_from_vclusters_parser = mappings_subparsers.add_parser(
        name="import-from-vclusters-config",
        help="Create topic mappings from existing vclusters",
    )
    import_from_vclusters_parser.add_argument(
        "-f",
        "--import-config-file",
        dest="import_config_file",
        help="Path to the mappings import file",
        required=True,
        type=str,
    )
    import_from_vcluster_parser = mappings_subparsers.add_parser(
        name="import-from-vcluster",
        help="Import all topics from a existing vCluster",
        parents=[VCLUSTER_PARSER],
    )
    import_from_vcluster_parser.add_argument(
        "--src",
        "--source-vcluster",
        dest="source_vcluster",
        help="Name of the source vCluster to import the mappings from",
        type=str,
        required=True,
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
    main_parser.add_argument("--url", required=False)
    main_parser.add_argument("--username", required=False)
    main_parser.add_argument("--password", required=False)
    main_parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        help="Path to the profiles files",
        default="{}/.cdk_gw.yaml".format(environ.get("HOME", ".")),
    )
    main_parser.add_argument(
        "-p",
        "--profile-name",
        type=str,
        help="Name of the profile to use to make API Calls",
    )

    cmd_parser = main_parser.add_subparsers(dest="category", help="Resources to manage")
    vclusters_parser = cmd_parser.add_parser(
        name="vclusters",
        help="Manages vClusters",
    )
    vclusters_subparsers = vclusters_parser.add_subparsers(
        dest="action", help="vCluster tokens management"
    )
    set_vclusters_actions_parsers(vclusters_subparsers)
    return main_parser
