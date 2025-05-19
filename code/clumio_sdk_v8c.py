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


import requests
import boto3
import json
import random
import functools
import string
from botocore.exceptions import ClientError
import api_dict
from mypy_boto3_sts import type_defs as sts_types

API_DICT = api_dict.API_DICT


class ClumioException(Exception):
    pass


class AWSException(Exception):
    pass


class InvalidInputException(Exception):
    pass


class API:
    def __init__(self, id: str, url: str, token: str):
        self._id = id
        self._url_prefix = f"{url}/"
        self._token = token
        self._payload: dict | None = None

    @functools.cached_property
    def token(self):
        return self._token

    @property
    def version(self):
        return API_DICT[self._id]["version"]

    @property
    def type(self):
        return API_DICT[self._id]["type"]

    @property
    def header(self):
        accept_header = API_DICT[self._id]["header"]
        header_dict = {"accept": accept_header, "authorization": f"Bearer {self.token}"}
        if self.type == "post":
            header_dict["content-type"] = "application/json"
        return header_dict

    @property
    def url(self):
        return self._url_prefix + API_DICT[self._id]["api"]

    @property
    def query_parms(self):
        return API_DICT[self._id]["query_parms"]

    @property
    def body_parms(self):
        return API_DICT[self._id]["body_parms"]

    @property
    def return_code(self):
        return API_DICT[self._id]["success"]

    def exec_api(self) -> dict:
        print("API Request: %s" % API_DICT[self._id]["desc"])
        print(f"{self.type} API Request to {self.url} with payload {self._payload}")

        if self.type == "get":
            res = requests.get(self.url, headers=self.header)
        elif self.type == "post":
            res = requests.post(self.url, json=self._payload, headers=self.header)

        res_text_dict: dict = json.loads(res.text)
        if res.status_code != self.return_code:
            status_msg = f"Unexpected API status: {res.status_code}"
            error_msg = (
                f"status: {status_msg}, msg: {res_text_dict.get("errors", None)}"
            )
            raise ClumioException(error_msg)

        print(
            f"API response: {res}, started task: {res_text_dict.get("task_id", None)}"
        )
        return res_text_dict


class ClumioConnectAccount(API):

    def __init__(
        self,
        url: str,
        token: str,
        account_id: str,
        regions: list[str],
        services: list[str],
    ):
        super(ClumioConnectAccount, self).__init__("008", url, token)
        self.aws_account_to_connect: str | None = None
        self.master_aws_region: str | None = None
        self.master_aws_account_id: str | None = None
        self.aws_region_list_to_connect: list[str] | None = None
        self.asset_types_to_enable: list[str] | None = None

        self.set_connect_params(account_id, regions, services)

    def set_connect_params(
        self, account_id: str, regions: list[str], services: list[str]
    ):
        self.aws_account_to_connect = account_id
        self.master_aws_account_id = account_id
        self.master_aws_region = regions[0]
        self.aws_region_list_to_connect = regions
        self.asset_types_to_enable = services
        self._payload = {
            "account_native_id": self.aws_account_to_connect,
            "master_region": self.master_aws_region,
            "master_aws_account_id": self.master_aws_account_id,
            "aws_regions": self.aws_region_list_to_connect,
            "asset_types_enabled": self.asset_types_to_enable,
            "template_permission_set": "all",
        }

    def create_connection_group(self):
        self._id = "008"
        return self.exec_api()


class AWSOrgAccount:

    def __init__(
        self,
        account_id: str,
        region: str,
        cft_admin_role: str = 'AWSCloudFormationStackSetAdministrationRole',
    ):
        self._account_id = account_id
        self._aws_region = region
        self._rnd_string = "".join(random.choices(string.ascii_letters, k=5))

        # Get the current session information
        sts_client = boto3.client('sts')
        self.account_id = sts_client.get_caller_identity()['Account']

        # Assume the role in the target account
        credentials = sts_client.assume_role(
            RoleArn=f'arn:aws:iam::{self.account_id}:role/{cft_admin_role}',
            RoleSessionName='ClumioBulkOnboardSession',
        )['Credentials']
        access_key = credentials['AccessKeyId']
        secret_key = credentials['SecretAccessKey']
        session_token = credentials['SessionToken']

        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name=self._aws_region,
        )

    def run_clumio_deploy_stack(
        self,
        child_account_id: str,
        template_url: str,
        external_id: str,
        clumio_token: str,
        stack_name: str,
    ):
        print(f"Deploying stack {stack_name} to {child_account_id}")
        cft_client = self.session.client("cloudformation")
        try:
            deploy_rsp = cft_client.create_stack(
                StackName=f"{stack_name}-{self._rnd_string}",
                TemplateURL=template_url,
                Parameters=[
                    {"ParameterKey": "ClumioToken", "ParameterValue": clumio_token},
                    {"ParameterKey": "RoleExternalId", "ParameterValue": external_id},
                    {
                        "ParameterKey": "PermissionModel",
                        "ParameterValue": "SELF_MANAGED",
                    },
                    {"ParameterKey": "PermissionsBoundaryARN", "ParameterValue": ""},
                ],
                Capabilities=["CAPABILITY_NAMED_IAM"],
                DisableRollback=True,
                TimeoutInMinutes=60,
            )
            print(f"deploy_status: {deploy_rsp}")
        except ClientError as err:
            error_msg = f"Failed to deploy stack {stack_name}: {err.response['Error']}"
            raise AWSException(error_msg) from err
