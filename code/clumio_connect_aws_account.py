# Copyright 2025. Clumio, a Commvault Company.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import clumio_sdk_v8c
import logging

logger = logging.getLogger(__name__)

def lambda_handler(events, context):
    bear = events.get("bear")
    organization_role_arn = events.get("organization_role_arn")
    api_url = events.get("api_url")
    stack_name = events.get("stack_name", None)
    account = events.get("account", None)
    if account:
        account_id_list = account.get("aws_account_id_list", None)
        region_list = account.get("aws_region_list", None)
        aws_service_list = account.get("aws_service_list", None)
    else:
        raise clumio_sdk_v8c.InvalidInputException("No account detail provided.")
    if not all((account_id_list, region_list, aws_service_list)):
        raise clumio_sdk_v8c.InvalidInputException(
            "Missing account detail. Make sure to provide account_id_list, region_list, "
            f"and aws_service_list for account {account}."
        )

    deploy_region = region_list[0]

    for account_id in account_id_list:
        aws_account_mng = clumio_sdk_v8c.AWSOrgAccount(
            api_url, account_id, deploy_region, organization_role_arn
        )
        admin_creds = aws_account_mng.connect_assume_role()
        admin_session = aws_account_mng.get_session(admin_creds)

        # Initiate Clumio API for onboarding an AWS account
        clumio_connect_api = clumio_sdk_v8c.ClumioConnectAccount(
            api_url, bear, account_id, region_list, aws_service_list
        )
        rsp = clumio_connect_api.create_connection_group()
        # Parse the Clumio token, URL, and id to run the Clumio deployment stack
        deployment_template_url_clumio = rsp.get("deployment_template_url")
        clumio_token = rsp.get("id")
        external_id = rsp.get("external_id")
        # Deploy CFT stack to connect AWS account to Clumio
        aws_account_mng.run_clumio_deploy_stack(
            admin_session,
            account_id,
            deploy_region,
            deployment_template_url_clumio,
            clumio_token,
            external_id,
            stack_name,
        )

        logger.info(
            'Stack %s deployment completed for %s, %s, %s',
            stack_name,
            account_id,
            region_list,
            aws_service_list,
        )

    return f'Initiated deployment of stack {stack_name} for account {account_id_list}, ' \
        f'region {region_list} for services {aws_service_list}.'