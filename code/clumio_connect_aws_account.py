# Copyright 2024, Clumio Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import boto3
import os
from botocore.exceptions import ClientError
from clumio_sdk_v8c import ClumioConnectAccount, AWSOrgAccount


class ClumioException(Exception):
    pass

class AWSException(Exception):
    pass


def lambda_handler(events, context):

    bear = events.get("bear", None)
    debug = events.get("debug", 0)
    organization_role_arn = events.get("organization_role_arn", None)
    assume_policy_arn = events.get("assume_policy_arn", None)
    api_url = events.get("api_url", None)
    stack_name = events.get("stack_name", None)
    account = events.get("account", None)
    if account:
        account_id = account.get("aws_account_id", None)
        region_list = account.get("aws_region_list", None)
        aws_service_list = account.get("aws_service_list", None)
    else:
        raise ClumioException({
            "status": 401,
            "msg": "No account is provided.",
            "account_id": "",
            "regions": [],
            "services": [],
        })

    # usage:
    aws_account_mng = AWSOrgAccount(api_url)
    region = region_list[0]
    aws_account_mng.set_ou_role_arn(organization_role_arn)
    aws_account_mng.set_ou_assume_policy_arn(assume_policy_arn)
    aws_account_mng.set_aws_region(region)
    ou_admin_role = aws_account_mng.get_ou_admin_role()
    [status, msg, cred] = aws_account_mng.connect_assume_role(
        "boto3", ou_admin_role, "a"
    )
    if not status:
        raise AWSException({
            "status": 407,
            "msg": msg,
            "account_id": account,
            "regions": [],
            "services": [],
        })

    aws_access_key_id = cred.get("AccessKeyId", None)
    aws_secret_access_key = cred.get("SecretAccessKey", None)
    aws_session_token = cred.get("SessionToken", None)

    try:
        aws_session1 = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region,
        )
    except ClientError as e:
        error = e.response["Error"]["Code"]
        error_msg = f"failed to initiate session {error}"
        # print("in DataDump 03")
        raise AWSException({
            "status": 402,
            "msg": error_msg,
            "account_id": account_id,
            "regions": [],
            "services": [],
        })

    # Initiate Clumio API for onboarding an AWS account
    clumio_connect_api = ClumioConnectAccount(api_url)
    clumio_connect_api.set_token(bear)
    clumio_connect_api.set_debug(debug)
    clumio_connect_api.set_account(account_id)
    clumio_connect_api.set_regions(region_list)
    clumio_connect_api.set_aws_services(aws_service_list)

    # Run the Clumio API for onboarding an AWS account
    rsp = clumio_connect_api.run()
    print(rsp)
    # Parse the Clumio token, URL, and id to run the Clumio deployment stack
    deployment_template_url_clumio = rsp.get("deployment_template_url", None)
    clumio_token = rsp.get("id", None)
    external_id = rsp.get("external_id", None)
    if not (deployment_template_url_clumio and clumio_token and external_id):
        raise ClumioException({"status": 408, "msg": f"clumio connect issue {rsp}", "account_id": account_id, "regions": [], "services": []})
    # Deploy CFT stack to connect AWS account to Clumio
    [status, msg, count, root_ou, accounts_] = aws_account_mng.check_for_accounts(aws_session1, region)
    if not status:
        raise ClumioException({"status": 406, "msg": msg, "account_id": account_id, "regions": [], "services": []})
    [status, msg] = aws_account_mng.confirm_ou_role(aws_session1, account_id)
    if not status:
        raise ClumioException({"status": 405, "msg": msg, "account_id": account, "regions": [], "services": []})
    [status, msg] = aws_account_mng.run_clumio_deploy_stack(aws_session1, account_id, region, deployment_template_url_clumio, clumio_token, external_id, stack_name)
    if status:
        return {
            "status": 200,
            "msg": f"stack {stack_name} deploy completed.",
            "account_id": account_id,
            "regions": region_list,
            "services": aws_service_list,
        }
    raise ClumioException(
        {
            "status": 403,
            "msg": msg,
            "account_id": account_id,
            "regions": [],
            "services": [],
        }
    )
