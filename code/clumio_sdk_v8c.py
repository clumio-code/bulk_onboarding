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


import requests
from datetime import datetime, timedelta, timezone
import boto3
import time
import json
import random
import string
from botocore.exceptions import ClientError
import re
import urllib.parse

api_dict = {
    "001": {"name": "EC2BackupList", "api": "backups/aws/ec2-instances",
            "header": "application/api.clumio.backup-aws-ebs-volumes=v2+json", "version": "v2",
            "desc": "List EC2 instance backups", "type": "get", "success": 200,
            "query_parms": {"limit": 100, "start": 1,
                            "filter": {
                                "start_timestamp": [
                                    "$lte", "$gt"],
                                "instance_id": [
                                    "$eq"]},
                            "sort": [
                                "-start_timestamp",
                                "start_timestamp"]}},
    "002": {"name": "environment_id",
            "api": "datasources/aws/environments",
            "header": "application/api.clumio.aws-environments=v1+json",
            "version": "v1",
            "desc": "List AWS environments",
            "type": "get",
            "success": 200,
            "query_parms": {
                "limit": 100,
                "start": 1,
                "filter": {
                    "account_native_id": [
                        "$eq",
                        "$begins_with"],
                    "aws_region": ["$eq"],
                    "connection_status": [
                        "$eq"],
                    "services_enabled": [
                        "$contains"]
                }
            }
            },
    "003": {"name": "RestoreEC2",
            "api": "restores/aws/ec2-instances",
            "header": "application/api.clumio.restored-aws-ec2-instances=v1+json",
            "version": "v1",
            "body_parms": {"source": None,
                           "target": ["ami_restore_target", "instance_restore_target", "volumes_restore_target"]},
            "PayloadTemplates": {
                "ebs_block_device_mappings": {
                    "condition": {"xor": [], "and": ["volume_native_id"]},
                    "volume_native_id": None,
                    "kms_key_native_id": None,
                    "name": None,
                    "tags": {}
                },
                "network_interfaces": {
                    "condition": {"xor": [], "and": ["device_index"]},
                    "device_index": None,
                    "network_interface_native_id": None,
                    "restore_default": False,
                    "restore_from_backup": False,
                    "security_group_native_ids": [None],
                    "subnet_native_id": None
                },
                "tags": {
                    "condition": {"xor": [], "and": ["key", "value"]},
                    "key": None,
                    "value": None
                },
                "ami_restore_target": {
                    "condition": {"xor": [], "and": ["ebs_block_device_mappings", "environment_id", "name"]},
                    "description": None,
                    "ebs_block_device_mappings": {},
                    "environment_id": None,
                    "name": None,
                    "tags": {}
                },
                "volumes_restore_target": {
                    "condition": {"xor": ["aws_az", "target_instance_native_id"],
                                  "and": ["ebs_block_device_mappings", "environment_id"]},
                    "aws_az": None,
                    "ebs_block_device_mappings": {},
                    "target_instance_native_id": None,
                    "environment_id": None
                },
                "instance_restore_target": {
                    "condition": {"xor": [],
                                  "and": ["ebs_block_device_mappings", "environment_id", "network_interfaces",
                                          "subnet_native_id", "vpc_native_id"]},
                    "should_power_on": False,
                    "ami_native_id": None,
                    "aws_az": None,
                    "ebs_block_device_mappings": {},
                    "environment_id": None,
                    "iam_instance_profile_name": None,
                    "key_pair_name": None,
                    "subnet_native_id": None,
                    "tags": {},
                    "vpc_native_id": None,
                    "network_interfaces": {}
                }
            },
            "desc": "Restore an EC2 instance",
            "type": "post",
            "success": 202,
            "query_parms": {
                "embed": [
                    "read-task"
                ]
            }
            },
    "004": {"name": "EBSBackupList",
            "api": "backups/aws/ebs-volumes",
            "header": "application/api.clumio.backup-aws-ebs-volumes=v2+json",
            "version": "v2",
            "desc": "List EBS volume backups",
            "type": "get",
            "success": 200,
            "query_parms": {
                "limit": 100,
                "start": 1,
                "filter": {
                    "start_timestamp": [
                        "$lte", "$gt"],
                    "volume_id": [
                        "$eq"]
                },
                "sort": [
                    "-start_timestamp",
                    "start_timestamp"]
            }
            },
    "005": {"name": "RestoreEBS",
            "api": "restores/aws/ebs-volumes",
            "header": "application/api.clumio.restored-aws-ebs-volumes=v2+json",
            "version": "v2",
            "body_parms": {"source": None,
                           "target": {"condition": {"xor": [], "and": ["aws_az", "environment_id"]},
                                      "aws_az": None,
                                      "environment_id": None,
                                      "iops": 0,
                                      "kms_key_native_id": None,
                                      "tags": {},
                                      "type": None
                                      }
                           },
            "desc": "Restore an EBS Volume",
            "type": "post",
            "success": 202,
            "query_parms": {
                "embed": [
                    "read-task"
                ]
            }
            },
    "006": {"name": "ListEC2Instances",
            "api": "datasources/aws/ec2-instances",
            "header": "application/api.clumio.aws-ec2-instances=v1+json",
            "version": "v1",
            "desc": "List EC2 instances",
            "type": "get",
            "success": 200,
            "query_parms": {
                "limit": 100,
                "start": 1,
                "filter": {
                    "environment_id": [
                        "$eq"],
                    "name": [
                        "$contains", "$eq"],
                    "instance_native_id": [
                        "$contains", "$eq"],
                    "account_native_id": [
                        "$eq"],
                    "protection_status": [
                        {"$eq": ["protected", "unprotected", "unsupported"]}],
                    "tags.id": [
                        "$all"],
                    "is_deleted": [
                        {"$eq": ["true", "false"]}],
                    "availability_zone": [
                        "$eq"]
                },
                "embed": [
                    "read-policy-definition"
                ]
            }
            },
    "007": {"name": "BackupEC2",
            "api": "backups/aws/ec2-instances",
            "header": "application/api.clumio.backup-aws-ec2-instances=v1+json",
            "version": "v2",
            "body_parms": {
                "type:": {
                    "condition": {"xor": ["clumio_backup", "aws_snapshot"], "and": []}
                },
                "instance_id": None,
                "setting": {
                    "retention_duration": {
                        "condition": {"xor": [], "and": ["unit", "value"]},
                        "unit": {"condition": {"xor": ["hours", "days", "weeks", "months", "years"], "and": []}},
                        "value": 0
                    },
                    "advanced_settings": {
                        "condition": {"xor": ["aws_ebs_volume_backup", "aws_ec2_instance_backup"], "and": []},
                        "aws_ebs_volume_backup": {"condition": {"xor": ["standard", "lite"], "and": []}},
                        "aws_ec2_instance_backup": {"condition": {"xor": ["standard", "lite"], "and": []}},
                    },
                    "backup_aws_region": None
                },
            },
            "desc": "Backup an EC2 instance on demand",
            "type": "post",
            "success": 202,
            "query_parms": {
                "embed": [
                    "read-task"
                ]
            }
            },
    "008": {"name": "Connections",
            "api": "connections/aws/connection-groups",
            "header": "application/api.clumio.aws-environments=v1+json",
            "version": "v1",
            "desc": "Add AWS Connections",
            "type": "post",
            "success": 200,
            "query_parms": {
                "limit": 100,
                "start": 1,
                "filter": {
                    "account_native_id": [
                        "$eq",
                        "$begins_with"],
                    "master_region": ["$eq"],
                    "aws_region": ["$eq"],
                    "asset_types_enabled": ["ebs", "rds", "DynamoDB", "EC2MSSQL", "S3", "ec2"],
                    "description": ["$eq"]
                }
            }
            },
    "010": {"name": "ListS3Bucket",
            "api": "datasources/aws/s3-buckets",
            "header": "application/api.clumio.aws-s3-buckets=v1+json",
            "version": "v1",
            "desc": "Returns a list of S3 buckets",
            "type": "get",
            "success": 200,
            "query_parms": {
                "limit": 100,
                "start": 1,
                "filter": {
                    "environment_id": [
                        "$eq"],
                    "name": [
                        "$contains", "$in"],
                    "account_native_id": [
                        "$eq"],
                    "aws_region": [
                        "$eq", "$in"],
                    "is_deleted": [
                        "$eq"],
                    "tags.id": [
                        "$all"],
                    "aws_tag": [
                        "$in", "$all"],
                    "excluded_aws_tag": [
                        "$all"],
                    "organizational_unit_id": [
                        "$in"],
                    "asset_id": [
                        "$in"],
                    "event_bridge_enabled": [
                        "$eq"],
                    "is_versioning_enabled": [
                        "$eq"],
                    "is_encryption_enabled": [
                        "$eq"],
                    "is_replication_enabled": [
                        "$eq"],
                    "is_supported": [
                        "$eq"],
                    "is_active": [
                        "$eq"]
                }
            }
            },
    "011": {"name": "RetrieveTask",
            "api": "tasks",
            "header": "application/api.clumio.tasks=v1+json",
            "version": "v1",
            "desc": "Retrieve a task",
            "type": "get",
            "success": 200,
            },
    "012": {"name": "DynamoDBBackupList",
            "api": "backups/aws/dynamodb-tables",
            "header": "application/api.clumio.backup-aws-dynamodb-tables=v1+json",
            "version": "v2",
            "desc": "Retrieves a list of DynamoDB table backups",
            "type": "get",
            "success": 200,
            "query_parms": {
                "limit": 100,
                "start": 1,
                "filter": {
                    "start_timestamp": [
                        "$lte", "$gt"],
                    "table_id": [
                        "$eq"],
                    "type": ["$all"],  # clumio_backup,aws_snapshot
                    "condition": {"type": {"xor": ["clumio_backup", "aws_snapshot"],
                                           "and": []}},
                },
                "sort": [
                    "-start_timestamp",
                    "start_timestamp"]
            }
            },
    "013": {"name": "RestoreDDN",
            "api": "restores/aws/dynamodb-tables",
            "header": "application/api.clumio.restored-aws-dynamodb-tables=v1+json",
            "version": "v1",
            "body_parms": {"source": {"condition": {"xor": ["securevault_backup", "continuous_backup"], "and": []},
                                    "continuous_backup":{
                                            "table_id":None,
                                            "timestamp":None,
                                            "use_latest_restorable_time":False
                                        },
                                    "securevault_backup":{
                                            "backup_id": None
                                        },
                           "target": {"condition": {"xor": [], "and": ["table_name", "environment_id"]},
                                      "table_name": None,
                                      "environment_id": None,
                                      "iops": 0,
                                      "kms_key_native_id": None,
                                      "tags": {},
                                      "type": None,
                                      "provisioned_throughput": {
                                            "read_capacity_units": None,
                                            "write_capacity_units": None
                                        },
                                       "sse_specification": {
                                            "kms_key_type": "DEFAULT",
                                            "kms_master_key_id": "null"
                                        },
                                       "billing_mode": None,
                                       "global_secondary_indexes": [
                                            {
                                                "projection": {
                                                    "projection_type": None,
                                                    "non_key_attributes": [None]
                                                },
                                                "provisioned_throughput": {
                                                    "read_capacity_units": None,
                                                    "write_capacity_units": None
                                                },
                                                "index_name": "a",
                                                "key_schema": [
                                                    {
                                                        "attribute_name": "a",
                                                        "key_type": "HASH"
                                                    }
                                                ]
                                            }
                                        ],
                                       "local_secondary_indexes": [
                                            {
                                                "projection": {
                                                    "projection_type": None,
                                                    "non_key_attributes": [None]
                                                },
                                                "index_name": None,
                                                "key_schema": [
                                                    {
                                                        "attribute_name": None,
                                                        "key_type": None
                                                    }
                                                ]
                                            }
                                        ],
                                       "table_class": None,
                                       "table_name_": None
                                      }
                           },
                    },
            "desc": "Restores the specified DynamoDB table backup to the specified target destination",
            "type": "post",
            "success": 202,
            "query_parms": {
                    "embed": [
                        "read-task"
                        ]
                    }
            },
    "109": {"name": "ManageAWS",
            "api": "none",
            "header": "none",
            "version": "v1",
            "desc": "manage AWS",
            "type": "get",
            "success": 200,
            },
    "999": {"api": "test002", "version": "v1", "desc": 'List EC2 instance backups', "type": "get", "success": 200,
            "payload": {"a": 73, "b": "bye", "theRitz": "Gazila"}},
}


class API:
    def __init__(self, id, url):
        self.id = id
        self.good = True
        self.name = api_dict.get(id, {}).get('api', None)
        self.version = api_dict.get(id, {}).get('version', None)
        self.type = api_dict.get(id, {}).get('type', None)
        self.pagnation = False
        self.debug = 0
        if api_dict.get(id, {}).get('success', None):
            self.success = api_dict.get(id, {}).get('success', None)
        else:
            if self.debug > 7: print(
                f"API init debug new APIs {id},  success {api_dict.get(id, {}).get('success', None)}")
            self.good = False

        self.url_prefix = f'{url}/'
        self.header = {}
        self.payload = {}
        self.payload_flag = False
        self.body_parms_flag = False
        self.body_parms = {}
        self.token_flag = False
        self.token = None
        self.good = True
        self.type_get = False
        self.type_post = False
        self.current_count = 0
        self.total_count = 0
        self.total_pages_count = 0
        self.error_msg = None
        self.exec_error_flag = False
        self.aws_account_id = "080005437757"
        self.aws_account_id_flag = False
        self.aws_region = "us-east-1"
        self.aws_region_flag = False
        self.region_option = ["us-east-1", "us-west-2", "us-east-2", "us-west-1"]
        self.aws_tag_key = ""
        self.aws_tag_value = ""
        self.aws_tag_flag = False
        self.usage_type = "S3"
        self.aws_credentials = None
        self.aws_connect_good = False
        self.dump_to_file_flag = False
        self.dump_file_name = None
        self.dump_bucket = None
        self.aws_bucket_region = None
        self.file_iam_role = None
        self.import_bucket = None
        self.aws_import_bucket_region = None
        self.import_file_name = None
        self.import_file_flag = False
        self.import_data = {}
        self.type_post = False
        self.task_id = None
        self.task_id_flag = False
        self.pagination = False
        # #print("Hello world its me Dave")
        # Function to Create an AWS Session using IAM role

        if api_dict.get(id, {}).get('header', None):
            self.accept_api = api_dict.get(id, {}).get('header', None)
        else:
            if self.debug > 7: print(
                f"API init debug new APIs {id},  header {api_dict.get(id, {}).get('header', None)}")
            self.good = False
        # #print(f"DICT {api_dict.get(id, {}).get('type', None)}")
        if api_dict.get(id, {}).get('type', None):
            type = api_dict.get(id, {}).get('type', None)
            if type == 'get':
                self.type_get = True
                # #print("found get")
            elif type == 'post':
                self.type_post = True
            else:
                if self.debug > 7: print(
                    f"API init debug new APIs {id},  type {api_dict.get(id, {}).get('type', None)}")
                self.good = False
        else:
            if self.debug > 7: print(
                f"API init debug new APIs {id},  type {api_dict.get(id, {}).get('type', None)}")
            self.good = False
        if api_dict.get(id, {}).get('api', None):
            self.url = self.url_prefix + api_dict.get(id, {}).get('api', None)
            self.url_full = self.url
        else:
            self.good = False
        if api_dict.get(id, {}).get('body_parms', False):
            self.body_parms_flag = True
            self.body_parms = api_dict.get(id, {}).get('body_parms', {})
        else:
            self.payload_flag = False
            self.payload = {}
        if api_dict.get(id, {}).get('query_parms', False):
            self.query_parms_flag = True
            self.query_parms = api_dict.get(id, {}).get('query_parms', {})
        else:
            self.query_parms_flag = False
            self.query_parms = {}
        if api_dict.get(id, {}).get('body_parms', False):
            self.body_parms_flag = True
            self.body_parms = api_dict.get(id, {}).get('body_parms', {})
        else:
            self.body_parms_flag = False
            self.body_parms = {}
        if api_dict.get(id, {}).get('pathParms', False):
            self.pathParms_flag = True
            self.pathParms = api_dict.get(id, {}).get('query_parms', {})
        else:
            self.pathParms_flag = False
            self.pathParms = {}

    # Set debug Level
    def set_debug(self, value):
        try:
            self.debug = int(value)
            return True
        except ValueError:
            return False

    def get_task_id(self):
        if self.task_id_flag:
            return self.task_id
        else:
            return False

    # Function for user to setup Dump file to S3
    def setup_dump_file_s3(self, filename, bucket, prefix, role, aws_session, region="us-east-2"):
        self.usage_type = "S3"
        self.aws_bucket_region = region

        if self.set_dump_bucket(bucket):
            self.set_iam_file_role(role)

            if self.connect_aws(aws_session):

                s3FilePath = f"{prefix}/{filename}"
                if self.set_dump_file(s3FilePath, True):
                    self.dump_to_file_flag = True
                    return True
        if self.debug > 3: print(
            f"set_dump_fileS3 failed {filename}, {bucket}, {prefix}, {role}, {aws_session}, {region}")
        return False

    # Function to set Dump to File option
    def set_dump_file(self, filename, timestamp_flag=False):

        check_re = re.compile('[a-zA-Z0-9_/-]+$')

        if check_re.match(filename):

            # If use timestamp flag is passed add timestamp to file name
            if timestamp_flag:

                today = datetime.now().astimezone(timezone.utc)

                now_date_str = today.strftime('%Y%m%d%H%M%S')
                self.dump_file_name = f"{filename}-{now_date_str}.json"

            else:

                self.dump_file_name = f"{filename}.json"
            return True
        if self.debug > 3: print(f"set_dump_file failed {filename}, {timestamp_flag}")
        return False

    # Function to set Dump Bucket
    def set_dump_bucket(self, bucket):
        # Only allow lower case characters, numbers, -
        check_re = re.compile('[a-z0-9-]+$')

        if check_re.match(bucket):

            self.dump_bucket = bucket
            return True
        else:
            status_msg = f"failed {bucket} is invalid name format"
            self.error_msg = f"status {status_msg}"
            if self.debug > 3: print(f"set_dump_bucket failed {bucket}")
            return False

    def set_iam_file_role(self, role):
        self.file_iam_role = role

    # Function to clear Dump to File option
    def clear_dump_to_file(self):
        self.dump_to_file_flag = False

    def data_dump(self, dict_data):

        if self.usage_type == "S3" and self.aws_connect_good:

            json_data = json.dumps(dict_data, indent=2)
            s3_key = self.dump_file_name
            access_key_id = self.aws_credentials.get("access_key_id", None)
            secret_access_key = self.aws_credentials.get('secret_access_key', None)
            session_token = self.aws_credentials.get('session_token', None)
            region = self.aws_bucket_region
            try:
                aws_session = boto3.Session(
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    aws_session_token=session_token,
                    region_name=region
                )
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                self.error_msg = "failed to initiate session {ERROR}"
                if self.debug > 3: print(f"data_dump failed in AWS Session cmd {dict_data}")
                return False
            s3_client = aws_session.client("s3")
            s3_resource = aws_session.resource('s3')
            data_encoded = json_data.encode('ascii')
            object1 = s3_resource.Object(self.dump_bucket, s3_key)
            try:
                result = object1.put(Body=data_encoded)
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                status_msg = f"failed to write ClumioResourceList file {s3_key}"
                self.error_msg = f"status: {status_msg}, msg: {ERROR}"
                if self.debug > 3: print(f"data_dump failed in AWS s3 put cmd {dict_data}")
                return False
            return result
        else:
            self.error_msg = "status: not supporting other dump methods yet"
            return False

    # Function to Create an AWS Session using IAM role
    def connect_aws(self, session):

        if self.usage_type == "S3":

            # BOILER PLATE AWS CONNECT STUFF
            client = session.client('sts')
            if self.file_iam_role:

                role_arn = self.file_iam_role
                external_id = "clumio"
                sessionName = "mysesino"
                try:
                    response = client.assume_role(
                        role_arn=role_arn,
                        role_session_name=sessionName,
                        external_id=external_id
                    )
                except ClientError as e:
                    ERROR = e.response['Error']['Code']
                    status_msg = f"failed to assume role {role_arn}"
                    self.error_msg = f"status {status_msg} Error {ERROR}"
                    if self.debug > 3: print(f"connect_aws failed in AWS s3 assume role cmd {session}")
                    return False
                credentials = response.get('credentials', None)
                if not credentials == None:
                    # #print("in connect_aws 05")
                    access_key_id = credentials.get("access_key_id", None)
                    secret_access_key = credentials.get('secret_access_key', None)
                    session_token = credentials.get('session_token', None)
                    if not access_key_id == None and not secret_access_key == None and not session_token == None:
                        # #print(f"status: passed, access_key_id: {access_key_id}, secret_access_key: {secret_access_key},session_token: {session_token}")
                        self.aws_credentials = credentials
                        self.aws_connect_good = True
                        return True
                    else:
                        # #print("in connect_aws 05")
                        status_msg = "failed AccessKey or SecretKey or session_token are blank"
                        self.error_msg = f"status {status_msg}"
                        # #print(status_msg)
                        # return {"status": status_msg, "msg": ""}
                else:
                    # #print("in connect_aws 06")
                    status_msg = "failed Credentilas are blank"
                    self.error_msg = f"status {status_msg}"
            else:
                # #print("in connect_aws 07")
                status_msg = "failed Role is blank"
                self.error_msg = f"status {status_msg}"
        else:
            # #print("in connect_aws 08")
            status_msg = "Usage Type is not S3"
            self.error_msg = f"status {status_msg}"
        # #print("in connect_aws 09")
        self.aws_connect_good = False
        if self.debug > 3: print(f"connect_aws failed error_msg {self.error_msg}, {session}")
        return False
        # END OF BOILER PLATE

    def get_error(self):
        return self.error_msg

    def get_version(self):
        # #print(self.version,type(self.version))
        ##print("hi")
        return self.version

    def set_token(self, token):
        self.token = token
        self.token_flag = True
        bear = f"Bearer {self.token}"

        if self.good:
            if self.type_get:
                self.header = {"accept": self.accept_api, "authorization": bear}
            elif self.type_post:
                self.header = {"accept": self.accept_api, "content-type": "application/json", "authorization": bear}
            return self.header

    def set_url(self, suffix):
        # #print(f"hi in set {prefix}")
        if self.good:
            self.url_full = self.url + suffix
            # #print(self.url_full)

    def get_url(self):
        if self.good:
            return self.url_full
        else:
            return False

    def set_pagination(self):
        self.pagination = True

    def get_header(self):
        if self.good:
            return self.header
        else:
            return False

    def set_bad(self):
        self.good = False

    def set_get(self):

        self.type_get = True

    def set_post(self):

        self.type_post = True

    def set_aws_tag_key(self, aws_tag_key):
        self.aws_tag_key = aws_tag_key
        self.aws_tag_flag = True
        if self.debug > 5: print(f"set_aws_tag_key: value {aws_tag_key}")
        return True

    def clear_aws_tag(self):
        self.aws_tag_key = ""
        self.aws_tag_value = ""
        self.aws_tag_flag = False

    def set_aws_tag_value(self, aws_tag_value=None):
        self.aws_tag_value = aws_tag_value
        return True

    def set_aws_account_id(self, aws_account_id):
        try:
            int(aws_account_id)
            self.aws_account_id = aws_account_id
            self.aws_account_id_flag_flag = False
            return True
        except ValueError:
            return False

    def set_aws_region(self, aws_region):

        if aws_region in self.region_option:

            self.aws_region = aws_region
            self.aws_region_flag = True
            return True
        else:
            return False

    def exec_api(self):
        if self.debug > 7: print(f"exec_api: In Post {self.id},  type post {self.type_post} type get {self.type_get}")
        if self.type_get:

            if self.good and self.token_flag:

                url = self.get_url()
                header = self.get_header()
                if self.debug > 0: print(f"exec_api - url {url}")
                if self.debug > 0: print(f"exec_api - header {header}")

                try:
                    response = requests.get(url, headers=header)
                except ClientError as e:
                    ERROR = e.response['Error']['Code']
                    status_msg = "failed to initiate session"
                    if self.debug > 3: print("exec_api failed in request")
                    return {"status": status_msg, "msg": ERROR}
                status = response.status_code

                response_text = response.text
                if self.debug > 1: print(f"exec_api - get request response {response_text}")
                response_dict = json.loads(response_text)

                if not status == self.success:
                    status_msg = f"API status {status}"
                    ERROR = response_dict.get('errors')
                    self.exec_error_flag = True
                    self.error_msg = f"status: {status_msg}, msg: {ERROR}"
                    if self.debug > 3: print(f"exec_api get request error resonse - {self.error_msg}")
                    self.good = False
                if self.pagination:
                    self.current_count = response_dict.get("current_count")
                    self.total_count = response_dict.get("total_count")
                    self.total_pages_count = response_dict.get("total_pages_count")
                    if self.debug > 1: print(
                        f"exec_api - pagination info current, total, total pages {self.current_count} {self.total_count} {self.total_pages_count}")
                return response_dict
        elif self.type_post:
            if self.debug > 7: print(f"exec_api: post Post  {id},  header {api_dict.get(id, {}).get('header', None)}")
            if self.good and self.token_flag and self.payload_flag:
                if self.debug > 7: print(f"exec_api: In Post {id},  header {api_dict.get(id, {}).get('header', None)}")
                url = self.get_url()
                header = self.get_header()
                payload = self.get_payload()
                if self.debug > 0: print(f"exec_api - url {url}")
                if self.debug > 0: print(f"exec_api - header {header}")
                if self.debug > 0: print(f"exec_api - payload {payload}")
                try:
                    response = requests.post(url, json=payload, headers=header)
                    if self.debug > 1: print(f"exec_api - response {response}")
                except ClientError as e:
                    ERROR = e.response['Error']['Code']
                    status_msg = "failed to initiate session"
                    if self.debug > 3: print(f"exec_api post request failed - {self.error_msg}")
                    return {"status": status_msg, "msg": ERROR}
                status = response.status_code

                response_text = response.text
                if self.debug > 1: print(f"exec_api - request response {response_text}")
                response_dict = json.loads(response_text)
                self.task_id = response_dict.get("task_id", None)
                print(f"resposne {response_dict} task id {self.task_id}")
                if self.task_id:
                    self.task_id_flag = True
                else:
                    self.task_id_flag = False

                if not status == self.success:
                    status_msg = f"API status {status}"
                    ERROR = response_dict.get('errors')
                    self.exec_error_flag = True
                    self.error_msg = f"status: {status_msg}, msg: {ERROR}"
                    self.good = False
                    if self.debug > 3: print(f"exec_api post request response - {self.error_msg}")
                return response_dict
        else:
            self.good = False
            return False

    # Function to set Import Bucket
    def set_import_bucket(self, bucket):
        # Only allow lower case characters, numbers, -
        check_re = re.compile('[a-z0-9-]+$')
        if check_re.match(bucket):
            self.import_bucket = bucket
            return True
        else:
            status_msg = f"failed {bucket} is invalid name format"
            self.error_msg = f"status {status_msg}"
            # #print("in SetUploadBucket 03")
            return False

    def setup_import_file_s3(self, filename, bucket, prefix, role, aws_session, region="us-east-2"):
        self.usage_type = "S3"
        self.aws_bucket_region = region
        # print("in SetupFileS3 01")
        if self.set_import_bucket(bucket):
            # print("in SetupFileS3 02")
            self.set_iam_file_role(role)
            # #print("in setup_dump_file_s3 02")
            if self.connect_aws(aws_session):
                # print("in setup_dump_file_s3 03")
                s3FilePath = f"{prefix}/{filename}"
                if self.set_import_file(s3FilePath):
                    # print("in SetupFileS3 04")
                    return True
        return False

    # Function to set Upload from File option
    def set_import_file(self, filename):
        # print(f"set_import_file 01 {filename}")
        self.import_file_name = filename
        self.import_file_flag = True
        return True

        # Function to clear import File option

    def clear_import_file(self, filename):
        self.import_file_name = None
        self.import_file_flag = False

    def data_import(self):
        if self.usage_type == "S3" and self.import_file_flag and self.aws_connect_good:
            # json_data = json.dumps(dict_data, indent=2)
            s3_key = self.import_file_name
            access_key_id = self.aws_credentials.get("access_key_id", None)
            secret_access_key = self.aws_credentials.get('secret_access_key', None)
            session_token = self.aws_credentials.get('session_token', None)
            region = self.aws_bucket_region
            try:
                aws_session = boto3.Session(
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    aws_session_token=session_token,
                    region_name=region
                )
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                self.error_msg = "failed to initiate session {ERROR}"
                # #print("in data_dump 03")
                return False
            s3_client = aws_session.client("s3")
            s3_resource = aws_session.resource('s3')

            try:

                obj3 = s3_resource.Object(self.import_bucket, s3_key)
                jsonFile3 = obj3.get()['Body'].read().decode('utf-8')
                self.import_data = json.loads(jsonFile3)
                # print(type(self.import_data), self.import_data)
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                status_msg = f"failed read input file{s3_key}"
                # print(f"status: {status_msg}, msg: {ERROR}")
                self.error_msg = f"status: {status_msg}, msg: {ERROR}"
                return False

            return True
        else:
            self.error_msg = "status: not supporting other import methods yet"
            return False

    def clear_payload(self):
        self.payload = None
        self.payload_flag = False

    def get_payload(self):
        if self.payload_flag:
            return self.payload


class ClumioConnectAccount(API):
    def __init__(self, url: str):
        super(ClumioConnectAccount, self).__init__("008", url)
        self.id = "008"
        self.aws_account_to_connect = None
        self.master_aws_region = None
        self.master_aws_account_id = None
        self.aws_region_list_to_connect = []
        self.asset_types_to_enable = []
        self.aws_account_list_to_connect_flag = False
        self.master_aws_region_flag = False
        self.master_aws_account_id_flag = False
        self.aws_region_list_to_connect_flag = False
        self.asset_types_to_enable_flag = False
        self.good = True

        if api_dict.get(self.id, {}).get('type', None):
            # print(f"api_dict 01")
            if self.good:
                # print(f"api_dict 02")
                if api_dict.get(self.id, {}).get('type', None) == "get":
                    # print(f"api_dict 03")
                    self.set_get()
                elif api_dict.get(self.id, {}).get('type', None) == "post":
                    # print(f"api_dict 04")
                    self.set_post()
                else:
                    # print(f"api_dict 05")
                    self.set_bad()

    def confirm_payload(self):
        if self.aws_account_list_to_connect_flag and self.master_aws_account_id_flag and self.master_aws_region_flag and self.aws_region_list_to_connect_flag and self.asset_types_to_enable_flag:
            self.payload_flag = True
            self.payload = {
                "account_native_id": self.aws_account_to_connect,
                "master_region": self.master_aws_region,
                "master_aws_account_id": self.master_aws_account_id,
                "aws_regions": self.aws_region_list_to_connect,
                "asset_types_enabled": self.asset_types_to_enable,
                "template_permission_set": "all"
            }
        else:
            self.payload_flag = False
        return self.payload_flag

    def set_account(self, account_id):
        self.aws_account_to_connect = account_id
        self.master_aws_account_id = account_id
        self.aws_account_list_to_connect_flag = True
        self.master_aws_account_id_flag = True
        self.confirm_payload()

    def set_regions(self, region_list):
        self.master_aws_region = region_list[0]
        self.aws_region_list_to_connect = region_list
        self.master_aws_region_flag = True
        self.aws_region_list_to_connect_flag = True
        self.confirm_payload()

    def set_aws_services(self, service_list):
        self.asset_types_to_enable = service_list
        self.asset_types_to_enable_flag = True
        self.confirm_payload()

    def test(self):
        self.aws_account_to_connect = "323724565630"
        self.master_aws_region = "us-east-2"
        self.master_aws_account_id = "323724565630"
        self.aws_region_list_to_connect = ["us-east-2"]
        self.asset_types_to_enable = ["S3"]
        self.aws_account_list_to_connect_flag = True
        self.master_aws_region_flag = True
        self.master_aws_account_id_flag = True
        self.aws_region_list_to_connect_flag = True
        self.asset_types_to_enable_flag = True

        self.payload = {
            "account_native_id": self.aws_account_to_connect,
            "master_region": self.master_aws_region,
            "master_aws_account_id": self.master_aws_account_id,
            "aws_regions": self.aws_region_list_to_connect,
            "asset_types_enabled": self.asset_types_to_enable,
            "template_permission_set": "all"
        }
        self.payload_flag = True
        result = self.exec_api()
        print(result)
        return result

    def run(self):
        if self.payload_flag:
            result = self.exec_api()
            # print(result)
            return result
        else:
            raise Exception("Payload not set to run connect API")

    def set_import_bucket(self, bucket):
        # Only allow lower case characters, numbers, -
        check_re = re.compile('[a-z0-9-]+$')
        if check_re.match(bucket):
            self.import_bucket = bucket
            return True
        else:
            status_msg = f"failed {bucket} is invalid name format"
            self.error_msg = f"status {status_msg}"
            # #print("in SetUploadBucket 03")
            return False

    def setup_import_file_s3(self, filename, bucket, prefix, role, aws_session, region="us-east-2"):
        self.usage_type = "S3"
        self.aws_bucket_region = region
        # print("in SetupFileS3 01")
        if self.set_import_bucket(bucket):
            # print("in SetupFileS3 02")
            self.set_iam_file_role(role)
            # #print("in setup_dump_file_s3 02")
            if self.connect_aws(aws_session):
                # print("in setup_dump_file_s3 03")
                s3FilePath = f"{prefix}/{filename}"
                if self.set_import_file(s3FilePath):
                    # print("in SetupFileS3 04")
                    return True
        return False

    # Function to set Upload from File option
    def set_import_file(self, filename):
        # print(f"set_import_file 01 {filename}")
        self.import_file_name = filename
        self.import_file_flag = True
        return True

        # Function to clear import File option

    def clear_import_file(self, filename):
        self.import_file_name = None
        self.import_file_flag = False

    def data_import(self):
        if self.usage_type == "S3" and self.import_file_flag and self.aws_connect_good:
            # json_data = json.dumps(dict_data, indent=2)
            s3_key = self.import_file_name
            access_key_id = self.aws_credentials.get("access_key_id", None)
            secret_access_key = self.aws_credentials.get('secret_access_key', None)
            session_token = self.aws_credentials.get('session_token', None)
            region = self.aws_bucket_region
            try:
                aws_session = boto3.Session(
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    aws_session_token=session_token,
                    region_name=region
                )
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                self.error_msg = "failed to initiate session {ERROR}"
                # #print("in data_dump 03")
                return False
            s3_client = aws_session.client("s3")
            s3_resource = aws_session.resource('s3')

            try:

                obj3 = s3_resource.Object(self.import_bucket, s3_key)
                jsonFile3 = obj3.get()['Body'].read().decode('utf-8')
                self.import_data = json.loads(jsonFile3)
                # print(type(self.import_data), self.import_data)
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                status_msg = f"failed read input file{s3_key}"
                # print(f"status: {status_msg}, msg: {ERROR}")
                self.error_msg = f"status: {status_msg}, msg: {ERROR}"
                return False

            return True
        else:
            self.error_msg = "status: not supporting other import methods yet"
            return False

    def clear_payload(self):
        self.payload = None
        self.payload_flag = False

    def get_payload(self):
        if self.payload_flag:
            return self.payload


class AWSOrgAccount(API):
    def __init__(self, url: str):
        super(AWSOrgAccount, self).__init__("109", url)
        self.id = "109"
        self.token = ''.join(random.choices(string.ascii_letters, k=7))
        self.rnd_string = ''.join(random.choices(string.ascii_letters, k=5))
        self.ou_assume_policy = 'arn:aws:iam::156041431578:policy/AdministratorAccess'
        self.ou_role_child_name = 'OrganizationAccountAccessRole'
        self.required_policy_access = 'AWSAdministratorAccess'
        self.ou_role_arn = 'arn:aws:iam::803530060635:role/bulk_onboarding_rule'
        self.reserve_ou = 'ou-s6m3-q82210z1'
        self.log_bucket = '757214333202-clumio-se-training-useast1757214333202'
        self.log_prefix_parquet = '/prefix/my_file.parquet'
        self.log_prefix_csv = '/prefix/my_file.csv'
        self.log_mode = 'csv'  # could also be 'parquet'
        self.log_path = None

    def set_ou_assume_policy_arn(self, policy_arn):
        self.ou_assume_policy = policy_arn
        return True

    def set_ou_role_arn(self, role_arn):
        self.ou_role_arn = role_arn
        return True
    def set_log_mode(self, mode):
        if mode == 'csv':
            self.log_mode = mode
        elif mode == 'parquet':
            self.log_mode = mode
        else:
            return False
        return True

    def get_rnd_string(self):
        return self.rnd_string

    def set_ou_reserve(self, ou):
        self.reserve_ou = ou
        return

    def get_aws_org_token(self):
        # return ou admin role arn
        return self.token

    def get_ou_admin_role(self):
        return self.ou_role_arn

    def parse_arn(self, arn):
        # Parse an AWS Org Account Arn and return pieces in python dict
        elements = arn.split(':', 5)
        result = {
            'arn': elements[0],
            'partition': elements[1],
            'service': elements[2],
            'region': elements[3],
            'account': elements[4],
            'resource': elements[5],
            'ou_id': None,
            'resource_type': None
        }
        if '/' in result['resource']:
            result['resource_type'], result['resource'] = result['resource'].split('/', 1)
            if '/' in result['resource']:
                result['ou_id'], result['resource'] = result['resource'].split('/', 1)
            # print(f"in a {result['resource_type']} {result['resource']}")
        elif ':' in result['resource']:
            result['resource_type'], result['resource'] = result['resource'].split(':', 1)
            # print(f"in b {result['resource_type']}")
        return result

    def connect_assume_role(self, current_session, role, _id):
        # Manages an AWS Assume role operation from the current session to the role specified
        if current_session == "boto3":
            # If calling function is launched from a compute element that has a existing role relationship
            client = boto3.client('sts', region_name=self.aws_region)
        else:
            client = current_session.client('sts')
        if role:
            # print("in ConnectAWS 03")
            external_id = f"clumio{_id}"
            session_name = f"mysession{_id}"
            # AWS Assume Role API
            try:
                response = client.assume_role(
                    RoleArn=role,
                    RoleSessionName=session_name,
                    ExternalId=external_id
                )
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                status_msg = f"failed to assume role {role}"
                error_msg = f"status {status_msg} Error {ERROR}"
                # print(f"in ConnectAWS 04 {error_msg}")
                return False, error_msg, None
            credentials = response.get('Credentials', None)
            if not credentials == None:
                # print("in ConnectAWS 05")
                access_key_id = credentials.get("AccessKeyId", None)
                secret_access_key = credentials.get('SecretAccessKey', None)
                session_token = credentials.get('SessionToken', None)
                # If assume role was successfull return the credentials
                # for the new session  ALL other outcomes are failures
                if not access_key_id == None and not secret_access_key == None and not session_token == None:
                    # print(f"status: passed, AccessKeyId: {access_key_id}, SecretAccessKey: {secret_access_key},SessionToken: {SessionToken}")
                    aws_connect_good = True
                    return True, "", credentials
                else:
                    # print("in ConnectAWS 05")
                    status_msg = "failed AccessKey or SecretKey or SessionToken are blank"
                    error_msg = f"status {status_msg}"
                    return False, error_msg, None
                    # print(status_msg)
                    # return {"status": status_msg, "msg": ""}
            else:
                # print("in ConnectAWS 06")
                status_msg = f"failed Credentilas are blank"
                error_msg = f"status {status_msg}"
                return False, error_msg, None
        else:
            # print("in ConnectAWS 07")
            status_msg = f"failed Role is blank"
            error_msg = f"status {status_msg}"
            return False, error_msg, None

    def check_for_accounts(self, current_session, region):
        ou_client = current_session.client('organizations')
        try:
            response = ou_client.list_roots()
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"lookup root ou {error}"
            return False, error_msg, 0, None, None
        root_ou = response.get('Roots', [])[0].get('Id', None)
        rsp = ou_client.list_accounts()
        accounts = rsp.get('Accounts', [])
        # status_types = ['ACTIVE', 'SUSPENDED', 'PENDING_CLOSURE']
        usable_accounts = []
        for account in accounts:
            account_arn = account.get('Arn', None)
            result = self.parse_arn(account_arn)
            account_status = account.get('Status', None)
            child_account_id = result.get('resource', None)
            if child_account_id and account_status == 'ACTIVE':
                ou_result = ou_client.list_parents(ChildId=child_account_id)
                print(child_account_id, ou_result.get('Parents', [])[0].get('Id', None), self.reserve_ou)
                aws_session2 = {}
                if ou_result.get('Parents', [])[0].get('Id', None) == self.reserve_ou:
                    [status, msg, cred2] = self.connect_assume_role(current_session,
                                                     f'arn:aws:iam::{child_account_id}:role/{self.ou_role_child_name}',
                                                     '')
                    if not status:
                        error_msg = f'Unable to connect to arn:aws:iam::{child_account_id}:role/{self.ou_role_child_name} - {msg}'
                        return False, error_msg, 0, None, None
                    print(child_account_id, ou_result.get('Parents', [])[0].get('Id', None), self.reserve_ou)
                    access_key_id = cred2.get("AccessKeyId", None)
                    secret_access_key = cred2.get('SecretAccessKey', None)
                    session_token = cred2.get('SessionToken', None)
                    # region = AWSDumpBucketRegion

                    try:
                        aws_session2 = boto3.Session(
                            aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key,
                            aws_session_token=session_token,
                            region_name=region
                        )
                    except ClientError as e:
                        error = e.response['Error']['Code']
                        error_msg = f"failed to initiate session {error}"
                        return False, error_msg, 0, None, None
                    sts_client2 = aws_session2.client('sts')
                    try:
                        response2 = sts_client2.get_caller_identity()
                    except ClientError as e:
                        error = e.response['Error']['Code']
                        error_msg = f"failed to lookup account id {error}"
                        return False, error_msg, 0, None, None
                    # print(response2)
                    if response2.get('Account', None) == child_account_id:
                        # print(f"match & connectable {ou_result} {child_account_id} {account_status}")
                        usable_accounts.append(child_account_id)
                    else:
                        no_action = True
                        # print(f"match but not-connectable {ou_result} {child_account_id} {account_status}")

                else:
                    no_action = True
                    # print(f"no match {ou_result} {child_account_id} {account_status}")
            else:
                no_action = True
                # print(f"non-viable {child_account_id} {account_status}")
        # print(usable_accounts)
        random.shuffle(usable_accounts)
        return True, "", len(usable_accounts), root_ou, usable_accounts

    def confirm_ou_role(self, current_aws_session, account_id):
        iam_client = current_aws_session.client('iam')
        policy_arn = self.ou_assume_policy
        try:
            response = iam_client.list_policy_versions(
                PolicyArn=policy_arn
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to list policy {error}"
            if self.debug > 5: print(f"error: {error_msg}")
            return False, error_msg
        version_list = response.get('Versions', [])
        for version in version_list:
            if not version.get('IsDefaultVersion', False):
                ver_id = version.get('VersionId', None)
                print(f"deleting {ver_id}")
                try:
                    response = iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=ver_id
                    )
                except ClientError as e:
                    error = e.response['Error']['Code']
                    error_msg = f"failed to delete policy version(s) {error}"
                    if self.debug > 5: print(f"error: {error_msg}")
                    return False, error_msg
        try:
            response = iam_client.get_policy(
                PolicyArn=policy_arn
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to get policy {error}"
            if self.debug > 5: print(f"error: {error_msg}")
            return False, error_msg
        default_version = response.get('Policy', {}).get('DefaultVersionId', 'v1')
        try:
            old_policy_info = iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=default_version
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to get policy version {error}"
            if self.debug > 5: print(f"error: {error_msg}")
            return False, error_msg
        policy_doc = old_policy_info.get('PolicyVersion', {}).get('Document', {})

        # Make statement and resources as list.
        tmp_policy_statement = policy_doc.get('Statement', {})
        if isinstance(tmp_policy_statement, dict):
            policy_doc['Statement'] = [tmp_policy_statement]

        # Find the right place to add the new principal of ou role.
        new_principal = f'arn:aws:iam::{account_id}:role/{self.ou_role_child_name}'
        add_idx = -1
        for idx, statement in enumerate(policy_doc['Statement']):
            if statement.get('Effect') == 'Allow' and statement.get('Action') == 'sts:AssumeRole':
                add_idx = idx
                break
        # Add the new principal for ou role.
        if add_idx >= 0:
            resource = policy_doc['Statement'][add_idx].get('Resource', [])
            if isinstance(resource, str):
                resource = [resource]
            if new_principal not in resource:
                resource.append(new_principal)
            policy_doc['Statement'][add_idx]['Resource'] = resource
        else:
            new_statement = {
                'Effect': 'Allow',
                'Action': 'sts:AssumeRole',
                'Resource': [new_principal]
            }
            policy_doc['Statement'].append(new_statement)
        print(f"Updated policy doc = {policy_doc}")
        policy_doc_json = json.dumps(policy_doc)
        try:
            response = iam_client.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=policy_doc_json,
                SetAsDefault=True
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to apply updated policy {error}"
            if self.debug > 5: print(f"error: {error_msg}")
            return False, error_msg
        time.sleep(5)
        return True, None

    def create_new_ou(self, current_aws_session, customer, root_ou):
        ou_client = current_aws_session.client('organizations')
        try:
            new_ou = f"lab-{customer}-{self.rnd_string}"
            response = ou_client.create_organizational_unit(
                ParentId=root_ou,
                Name=new_ou,
                Tags=[
                    {
                        'Key': 'Customer',
                        'Value': customer
                    },
                ]
            )
        except ClientError as e:
            ERROR = e.response['Error']['Code']
            error_msg = "failed to create ou"
            raise Exception(error_msg.format(ERROR=ERROR))
        # print(response)
        new_ou = response.get('OrganizationalUnit', {}).get('Id', None)
        return new_ou

    def create_account(self, current_aws_session, master_user):
        ou_client = current_aws_session.client('organizations')
        try:
            new_account_name = f'lab-{self.rnd_string}'
            role = self.ou_role_child_name
            response = ou_client.create_account(
                Email=master_user,
                AccountName=new_account_name,
                RoleName=role,
                IamUserAccessToBilling='DENY',
            )
        except ClientError as e:
            ERROR = e.response['Error']['Code']
            error_msg = "failed to create account"
            # print("in data_dump 03")
            raise Exception(error_msg.format(ERROR=ERROR))
        # print(response)
        create_id = response.get('CreateAccountStatus', {}).get('Id', None)
        final_status = ['SUCCEEDED', 'FAILED']
        try:
            response = ou_client.describe_create_account_status(
                CreateAccountRequestId=create_id
            )
        except ClientError as e:
            ERROR = e.response['Error']['Code']
            error_msg = "failed to get create account status"
            # print("in data_dump 03")
            raise Exception(error_msg.format(ERROR=ERROR))
        # print(response)
        create_status = response.get('CreateAccountStatus', {}).get('State', None)
        # running_status = ['IN_PROGRESS']
        iter_count = 0
        while not create_status in final_status:
            time.sleep(5)
            try:
                response = ou_client.describe_create_account_status(
                    CreateAccountRequestId=create_id
                )
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                error_msg = "failed to get create account status"
                # print("in data_dump 03")
                raise Exception(error_msg.format(ERROR=ERROR))
            # print(response)
            create_status = response.get('CreateAccountStatus', {}).get('State', None)
            iter_count += 1
            if iter_count > 100:
                print("loser")
                break
            time.sleep(5)
        state = response.get("CreateAccountStatus", {}).get("State", None)
        if state == "SUCCEEDED":
            account_id = response.get("CreateAccountStatus", {}).get("AccountId", None)
            try:
                response = ou_client.list_parents(
                    ChildId=account_id,
                )
            except ClientError as e:
                ERROR = e.response['Error']['Code']
                error_msg = "failed to list parent OU"
                # print("in data_dump 03")
                raise Exception(error_msg.format(ERROR=ERROR))
            # print(response)
            parent_ou = response.get('Parents', [])[0].get('Id', None)
            return account_id, parent_ou
        else:
            try:
                int("eleven")
            except ValueError as e:
                errmsg = "Was not able to create an account."
                e.args += (errmsg,)
                raise e
        return False

    def account_prep(self, current_aws_session, account_id, new_ou, user):
        ou_client = current_aws_session.client('organizations')
        try:
            response = ou_client.move_account(
                AccountId=account_id,
                SourceParentId=self.reserve_ou,
                DestinationParentId=new_ou
            )
        except ClientError as e:
            ERROR = e.response['Error']['Code']
            error_msg = "failed to move account to new OU"
            # print("in data_dump 03")
            raise Exception(error_msg.format(ERROR=ERROR))
        idc_client = current_aws_session.client('sso-admin', region_name='us-east-2')
        ids_client = current_aws_session.client('identitystore', region_name='us-east-2')
        # response = idc_client.list_instances()
        idc_instance_arn = idc_client.list_instances().get('Instances', [])[0].get('InstanceArn', None)
        ids_id = idc_client.list_instances().get('Instances', [])[0].get('IdentityStoreId', None)
        print(idc_instance_arn, ids_id)

        permission_set_list = idc_client.list_permission_sets(InstanceArn=idc_instance_arn).get('PermissionSets', [])
        admin_permission_set_arn = ''
        for perm in permission_set_list:
            response = idc_client.describe_permission_set(
                InstanceArn=idc_instance_arn,
                PermissionSetArn=perm
            )
            if response.get('PermissionSet', {}).get('Name', None) == self.required_policy_access:
                admin_permission_set_arn = perm
                break
            print(response)
        print(admin_permission_set_arn)

        principal_id = ids_client.list_users(
            IdentityStoreId=ids_id,
            Filters=[
                {
                    'AttributePath': 'UserName',
                    'AttributeValue': user
                },
            ]
        ).get('Users', [])[0].get('UserId', None)
        print(principal_id)
        response = idc_client.create_account_assignment(
            InstanceArn=idc_instance_arn,
            PermissionSetArn=admin_permission_set_arn,
            PrincipalId=principal_id,
            PrincipalType='USER',
            TargetId=account_id,
            TargetType='AWS_ACCOUNT'
        )
        print(response)
        return True

    def run_clumio_deploy_stack(self, current_aws_session, child_account_id, region, url, token, id, stack_name):
        print("In deploy clumio stack")
        deployment_template_url = url
        clumio_token = token
        external_id = id
        role = f'arn:aws:iam::{child_account_id}:role/{self.ou_role_child_name}'
        [status, msg, cred2] = self.connect_assume_role(current_aws_session,
                                         role, 'x')
        if not status:
            print(f"connect failed to {role}")
            return False, msg
        access_key_id = cred2.get("AccessKeyId", None)
        secret_access_key = cred2.get('SecretAccessKey', None)
        session_token = cred2.get('SessionToken', None)
        try:
            new_aws_session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                aws_session_token=session_token,
                region_name=region
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to initiate session {error}"
            # print("in data_dump 03")
            return False, error_msg
        cft_client = new_aws_session.client('cloudformation')
        # response = cft_client.validate_template(
        #    TemplateURL=deployment_template_url
        # )
        # print(f"check clumio deploy url template {response}")
        try:
            deploy_rsp = cft_client.create_stack(
                StackName=f"{stack_name}-{self.rnd_string}",
                TemplateURL=deployment_template_url,
                Parameters=[
                    {
                        'ParameterKey': 'ClumioToken',
                        'ParameterValue': clumio_token
                    },
                    {
                        'ParameterKey': 'RoleExternalId',
                        'ParameterValue': external_id
                    },
                    {
                        'ParameterKey': 'PermissionModel',
                        'ParameterValue': 'SELF_MANAGED'
                    },
                    {
                        'ParameterKey': 'PermissionsBoundaryARN',
                        'ParameterValue': ''
                    },
                ],
                Capabilities=[
                    'CAPABILITY_NAMED_IAM'
                ],
                DisableRollback=True,
                TimeoutInMinutes=60,
            )
            print(f"deploy_status: {deploy_rsp}")
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to deploy stack {error}"
            if self.debug > 5: print(f"error: {error_msg}")
            return False, error_msg
        
        return True, ""

    def run_other_deploy_stack(self, current_aws_session, child_account_id, region, url, parameters):
        deployment_template_url = url
        [status, msg, cred2] = self.connect_assume_role(current_aws_session,
                                         f'arn:aws:iam::{child_account_id}:role/{self.ou_role_child_name}', '')
        if not status:
            return False, msg
            # S3Key = DumpFileName
        access_key_id = cred2.get("AccessKeyId", None)
        secret_access_key = cred2.get('SecretAccessKey', None)
        session_token = cred2.get('SessionToken', None)

        try:
            new_aws_session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                aws_session_token=session_token,
                region_name=region
            )
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to initiate session {error}"
            # print("in data_dump 03")
            return False, error_msg
        cft_client = new_aws_session.client('cloudformation')
        try:
            deploy_rsp = cft_client.create_stack(
                StackName=f'aws-resource-deploy-{self.rnd_string}',
                TemplateURL=deployment_template_url,
                Parameters=parameters,
                Capabilities=[
                    'CAPABILITY_NAMED_IAM'
                ],
                DisableRollback=True,
                TimeoutInMinutes=60,
            )
            print(f"deploy_status: {deploy_rsp}")
        except ClientError as e:
            error = e.response['Error']['Code']
            error_msg = f"failed to deploy stack {error}"
            if self.debug > 5: print(f"error: {error_msg}")
            return False, error_msg
        return True, ""

    def set_log_bucket(self, bucket_name):
        self.log_bucket = bucket_name
        return True

    def set_log_prefix(self, prefix):
        self.log_prefix = prefix
        return True
