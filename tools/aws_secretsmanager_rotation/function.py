#!/usr/bin/env python

from __future__ import annotations

import json
import logging
import os
import re
from copy import deepcopy
from datetime import datetime
from typing import Union

import jwt
import yaml
from boto3.session import Session
from compose_x_common.aws import get_assume_role_session
from compose_x_common.compose_x_common import keyisset

from cdk_proxy_api_client.admin_auth import AdminAuth
from cdk_proxy_api_client.proxy_api import ApiClient, Multitenancy, ProxyClient

if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


CDK_API_ENDPOINT = os.environ.get("CDK_API_ENDPOINT")
if not CDK_API_ENDPOINT:
    raise OSError("CDK_API_ENDPOINT must be set.")
NEW_TOKEN_LIFETIME_IN_SECONDS = int(
    os.environ.get("NEW_TOKEN_LIFETIME_IN_SECONDS", 3660)
)


def lambda_handler(event, context):
    secret_arn = event["SecretId"]
    token = event["ClientRequestToken"]
    step = event["Step"]

    lambda_session = Session()
    current_value = lambda_session.client("secretsmanager").get_secret_value(
        SecretId=secret_arn, VersionStage="AWSCURRENT"
    )["SecretString"]
    if isinstance(current_value, str):
        try:
            current_value = json.loads(current_value)
            logger.info("Successfully decode JSON value from SecretString")
        except json.JSONDecodeError:
            logger.info(
                "The secret content is not a valid JSON. Treating as raw/plain string instead."
            )

    if step == "createSecret":
        get_cdk_gw_admin_creds(lambda_session)
        create_secret(lambda_session, secret_arn, token, current_value)

    elif step == "setSecret":
        pass

    elif step == "testSecret":
        pass

    elif step == "finishSecret":
        finish_secret(lambda_session, secret_arn, token)

    else:
        raise ValueError("Invalid step parameter")


def create_secret(lambda_session: Session, arn, token, current_value):
    """
    Creates the new secret for tenant and stores in Secret with AWSPENDING stage.
    First, we check that there are no AWSPENDING secret value already in place.
    """
    client = lambda_session.client("secretsmanager")
    try:
        client("secretsmanager").get_secret_value(
            SecretId=arn, VersionId=token, VersionStage="AWSPENDING"
        )
        logger.warning(
            "createSecret: AWSPENDING already set for secret for {} - {}".format(
                arn, token
            )
        )
    except:
        logger.debug("No AWSPENDING secret already set. Clear to proceed.")
        try:
            gw_api_admin_secret = get_cdk_gw_admin_creds(lambda_session)
            logger.info(f"Successfully fetched GW API Secret")
            new_secret_value = new_gateway_tenant_secrets(
                gw_api_admin_secret, current_value
            )
            client.put_secret_value(
                SecretId=arn,
                ClientRequestToken=token,
                SecretString=json.dumps(new_secret_value)
                if not isinstance(new_secret_value, str)
                else new_secret_value,
                VersionStages=["AWSPENDING"],
            )
            logger.info(
                "createSecret: Successfully put AWSPENDING stage secret for ARN %s and version %s."
                % (arn, token)
            )
        except Exception as error:
            logger.exception(error)
            logger.error(
                "createSecret: Failed to create a new secret for ARN %s and version %s."
                % (arn, token)
            )
            raise


def finish_secret(lambda_session: Session, arn, token):
    """
    Finalizes/Promotes the rotation process by marking the secret version passed in as the AWSCURRENT secret
    from AWSPENDING stage
    """
    # First describe the secret to get the current version
    service_client = lambda_session.client("secretsmanager")
    metadata = service_client.describe_secret(SecretId=arn)
    current_version = None
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info(
                    "finishSecret: Version %s already marked as AWSCURRENT for %s"
                    % (version, arn)
                )
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    service_client.update_secret_version_stage(
        SecretId=arn,
        VersionStage="AWSCURRENT",
        MoveToVersionId=token,
        RemoveFromVersionId=current_version,
    )
    logger.info(
        "finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s."
        % (token, arn)
    )


def get_cdk_gw_admin_creds(lambda_session: Session) -> dict:
    cdk_api_secret_arn = os.environ.get("CDK_API_SECRET_ARN")
    if not cdk_api_secret_arn:
        raise OSError("CDK_API_SECRET_ARN must be set.")
    cdk_api_secret_role_arn = os.environ.get("CDK_API_SECRET_ARN_ROLE", None)
    if cdk_api_secret_role_arn and cdk_api_secret_arn.startswith("arn:aws"):
        client = get_assume_role_session(
            lambda_session, cdk_api_secret_role_arn
        ).client("secretsmanager")
    else:
        client = lambda_session.client("secretsmanager")
    try:
        secret_value = client.get_secret_value(SecretId=cdk_api_secret_arn)[
            "SecretString"
        ]
    except Exception as error:
        logger.exception(error)
        logger.error(f"Failed to retrieve the SecretString for {cdk_api_secret_arn}")
        raise

    try:
        gw_secret = yaml.safe_load(secret_value)
    except yaml.YAMLError as error:
        logger.exception(error)
        logger.info("Secret string is not YAML formatted")
        try:
            gw_secret = json.loads(secret_value)
        except json.JSONDecodeError as error:
            logger.exception(error)
            logger.info("Secret string is not JSON formatted.")
            gw_secret = secret_value

    if not isinstance(gw_secret, (list, dict)):
        raise TypeError(
            "The secret format is not valid. Got {}, expected one of {}".format(
                str, (list, dict)
            )
        )
    for secret in gw_secret:
        if keyisset("admin", secret):
            return secret
    raise ValueError(f"No admin user found in {cdk_api_secret_arn}")


def get_tenant_details_from_token(jwt_token: str) -> dict:
    """Uses existing secret JWT token to identify tenant owner"""
    try:
        jwt_content = jwt.decode(
            jwt_token,
            options={"verify_signature": False},
            algorithms=["HS256"],
        )
        return jwt_content
    except Exception as error:
        logger.error(f"Jwt token decode error + {error}")
        raise error


def get_new_token_for_tenant(secret: dict, tenant: dict, life) -> str:
    try:
        logger.info(
            f"creating secret for {tenant['tenant']} with user on host {CDK_API_ENDPOINT}"
        )
        api_client = ApiClient(
            username=secret["username"],
            password=secret["password"],
            url=CDK_API_ENDPOINT,
        )
        proxy_client = ProxyClient(api_client)
        admin_client = AdminAuth(proxy_client)
        logger.debug(Multitenancy(proxy_client).list_tenants().json())
        token = admin_client.create_tenant_credentials(
            tenant_id=tenant["tenant"], token_lifetime_seconds=life, token_only=True
        )
        return token
    except Exception as error:
        logger.exception(error)
        logger.error(
            "get_new_token_for_tenant : Failed to create new jwt token for {}".format(
                tenant["tenant"]
            )
        )


def replace_string_in_dict_values(
    input_dict: dict, src_value: str, new_value: str, copy: bool = False
) -> dict:
    """
    Function to update all values in an input dictionary that will match with the new value.
    It uses the new value to set as regex and replaces it in the dict values for each key,
    allowing for any secret value and dynamic dict content.
    """

    src_re = re.compile(re.escape(src_value))
    if copy:
        updated_dict = deepcopy(input_dict)
    else:
        updated_dict = input_dict
    for key, value in updated_dict.items():
        if isinstance(value, str) and src_re.findall(value):
            updated_dict[key] = src_re.sub(new_value, value)
        elif not isinstance(value, str):
            print(f"The value for {key} is not a string. Skipping")
    if copy:
        return updated_dict


def new_gateway_tenant_secrets(
    gateway_secret: dict,
    current_value: Union[dict, str],
) -> Union[dict, str]:
    """
    Calls the GW API Enpdoint to generate a new JWT token for the tenant.
    It will then use the value of the AWSCURRENT secret and replace the content wit the new token.
    If the current value is just a string, we replace it as-is.
    If the current value is a dict, we try upate the value of each key, if the old value is found in the dict value
    """
    if isinstance(current_value, dict):
        current_jwt_token = current_value["SASL_PASSWORD"]
        jwt_token_details = get_tenant_details_from_token(current_jwt_token)
    else:
        jwt_token_details = get_tenant_details_from_token(current_value)
    logger.info(
        "Token expiry was set to {}".format(
            datetime.utcfromtimestamp(jwt_token_details["exp"]).strftime("%FT%T")
        )
    )
    try:
        logger.info(f"creating token for tenant - {jwt_token_details['tenant']}")

        new_jwt_token = get_new_token_for_tenant(
            gateway_secret, jwt_token_details, NEW_TOKEN_LIFETIME_IN_SECONDS
        )
    except Exception as error:
        logger.exception(error)
        logger.error(
            "Failed to create a new JWT token for tenant {}".format(
                jwt_token_details["tenant"]
            )
        )
        raise
    if isinstance(current_value, dict):
        new_secret_value = replace_string_in_dict_values(
            current_value,
            current_value["SASL_USERNAME"],
            jwt_token_details["tenant"],
            True,
        )
        replace_string_in_dict_values(
            new_secret_value, current_value["SASL_PASSWORD"], new_jwt_token
        )
        return new_secret_value
    return new_jwt_token
