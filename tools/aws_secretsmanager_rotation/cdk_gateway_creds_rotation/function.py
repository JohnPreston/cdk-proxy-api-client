"""
Entrypoint functions of the rotation.
The lambda handler first evaluates whether the request received is to simply request a new token for a given
tenant and duration/expiry, or to manage the secret rotation itself.

"""
from __future__ import annotations

import json
import logging
import os

from boto3.session import Session
from compose_x_common.compose_x_common import keyisset

from .cdk_gateway_management import (
    get_cdk_gw_admin_creds,
    get_new_token_for_tenant,
    new_gateway_tenant_secret_value,
)

if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()

CDK_API_ENDPOINT = os.environ.get("CDK_API_ENDPOINT")
NEW_TOKEN_LIFETIME_IN_SECONDS = int(
    os.environ.get("NEW_TOKEN_LIFETIME_IN_SECONDS", 3660)
)
CENTRAL_FUNCTION_ARN_TO_INVOKE = os.environ.get("GW_ROTATION_MANAGER_FUNCTION_ARN")
if not CENTRAL_FUNCTION_ARN_TO_INVOKE:
    print(
        "No GW_ROTATION_MANAGER_FUNCTION_ARN set. Will attempt talking to GW directly."
    )
if not CENTRAL_FUNCTION_ARN_TO_INVOKE and not CDK_API_ENDPOINT:
    raise OSError(
        "CDK_API_ENDPOINT not set and no GW_ROTATION_MANAGER_FUNCTION_ARN to invoke."
        "One of the two must be set."
    )


def lambda_handler(event, context):
    lambda_session = Session()
    if keyisset("tenant", event) and keyisset("expiry", event):
        gateway_secret = get_cdk_gw_admin_creds(lambda_session)
        return {
            "token": get_new_token_for_tenant(
                gateway_secret,
                {"tenant": event["tenant"]},
                int(event["expiry"]),
                token_only=True,
            )
        }
    else:
        secret_arn = event["SecretId"]
        token = event["ClientRequestToken"]
        step = event["Step"]

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
            new_secret_value = new_gateway_tenant_secret_value(
                current_value, arn, token, lambda_session
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
        except client.exceptions.ResourceExistsException as error:
            logger.exception(error)
            logger.error(
                "A previous secret execution used this ClientToken. Must re-rotate the secret afterwards."
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
