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

from typing import TypedDict, Optional, Literal


class ApiDict(TypedDict, total=False):
    name: str
    api: str
    header: str
    version: str
    desc: str
    type: Literal['get', 'post']
    success: int
    query_parms: Optional[dict]
    body_parms: Optional[dict]


API_DICT: dict[str, ApiDict] = {
    "001": {
        "name": "EC2BackupList",
        "api": "backups/aws/ec2-instances",
        "header": "application/api.clumio.backup-aws-ebs-volumes=v2+json",
        "version": "v2",
        "desc": "List EC2 instance backups",
        "type": "get",
        "success": 200,
        "query_parms": {
            "limit": 100,
            "start": 1,
            "filter": {"start_timestamp": ["$lte", "$gt"], "instance_id": ["$eq"]},
            "sort": ["-start_timestamp", "start_timestamp"],
        },
    },
    "002": {
        "name": "environment_id",
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
                "account_native_id": ["$eq", "$begins_with"],
                "aws_region": ["$eq"],
                "connection_status": ["$eq"],
                "services_enabled": ["$contains"],
            },
        },
    },
    "003": {
        "name": "RestoreEC2",
        "api": "restores/aws/ec2-instances",
        "header": "application/api.clumio.restored-aws-ec2-instances=v1+json",
        "version": "v1",
        "body_parms": {
            "source": None,
            "target": [
                "ami_restore_target",
                "instance_restore_target",
                "volumes_restore_target",
            ],
        },
        "desc": "Restore an EC2 instance",
        "type": "post",
        "success": 202,
        "query_parms": {"embed": ["read-task"]},
    },
    "004": {
        "name": "EBSBackupList",
        "api": "backups/aws/ebs-volumes",
        "header": "application/api.clumio.backup-aws-ebs-volumes=v2+json",
        "version": "v2",
        "desc": "List EBS volume backups",
        "type": "get",
        "success": 200,
        "query_parms": {
            "limit": 100,
            "start": 1,
            "filter": {"start_timestamp": ["$lte", "$gt"], "volume_id": ["$eq"]},
            "sort": ["-start_timestamp", "start_timestamp"],
        },
    },
    "005": {
        "name": "RestoreEBS",
        "api": "restores/aws/ebs-volumes",
        "header": "application/api.clumio.restored-aws-ebs-volumes=v2+json",
        "version": "v2",
        "body_parms": {
            "source": None,
            "target": {
                "condition": {"xor": [], "and": ["aws_az", "environment_id"]},
                "aws_az": None,
                "environment_id": None,
                "iops": 0,
                "kms_key_native_id": None,
                "tags": {},
                "type": None,
            },
        },
        "desc": "Restore an EBS Volume",
        "type": "post",
        "success": 202,
        "query_parms": {"embed": ["read-task"]},
    },
    "006": {
        "name": "ListEC2Instances",
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
                "environment_id": ["$eq"],
                "name": ["$contains", "$eq"],
                "instance_native_id": ["$contains", "$eq"],
                "account_native_id": ["$eq"],
                "protection_status": [
                    {"$eq": ["protected", "unprotected", "unsupported"]}
                ],
                "tags.id": ["$all"],
                "is_deleted": [{"$eq": ["true", "false"]}],
                "availability_zone": ["$eq"],
            },
            "embed": ["read-policy-definition"],
        },
    },
    "007": {
        "name": "BackupEC2",
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
                    "unit": {
                        "condition": {
                            "xor": ["hours", "days", "weeks", "months", "years"],
                            "and": [],
                        }
                    },
                    "value": 0,
                },
                "advanced_settings": {
                    "condition": {
                        "xor": ["aws_ebs_volume_backup", "aws_ec2_instance_backup"],
                        "and": [],
                    },
                    "aws_ebs_volume_backup": {
                        "condition": {"xor": ["standard", "lite"], "and": []}
                    },
                    "aws_ec2_instance_backup": {
                        "condition": {"xor": ["standard", "lite"], "and": []}
                    },
                },
                "backup_aws_region": None,
            },
        },
        "desc": "Backup an EC2 instance on demand",
        "type": "post",
        "success": 202,
        "query_parms": {"embed": ["read-task"]},
    },
    "008": {
        "name": "Connections",
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
                "account_native_id": ["$eq", "$begins_with"],
                "master_region": ["$eq"],
                "aws_region": ["$eq"],
                "asset_types_enabled": [
                    "ebs",
                    "rds",
                    "DynamoDB",
                    "EC2MSSQL",
                    "S3",
                    "ec2",
                ],
                "description": ["$eq"],
            },
        },
    },
    "010": {
        "name": "ListS3Bucket",
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
                "environment_id": ["$eq"],
                "name": ["$contains", "$in"],
                "account_native_id": ["$eq"],
                "aws_region": ["$eq", "$in"],
                "is_deleted": ["$eq"],
                "tags.id": ["$all"],
                "aws_tag": ["$in", "$all"],
                "excluded_aws_tag": ["$all"],
                "organizational_unit_id": ["$in"],
                "asset_id": ["$in"],
                "event_bridge_enabled": ["$eq"],
                "is_versioning_enabled": ["$eq"],
                "is_encryption_enabled": ["$eq"],
                "is_replication_enabled": ["$eq"],
                "is_supported": ["$eq"],
                "is_active": ["$eq"],
            },
        },
    },
    "011": {
        "name": "RetrieveTask",
        "api": "tasks",
        "header": "application/api.clumio.tasks=v1+json",
        "version": "v1",
        "desc": "Retrieve a task",
        "type": "get",
        "success": 200,
    },
    "012": {
        "name": "DynamoDBBackupList",
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
                "start_timestamp": ["$lte", "$gt"],
                "table_id": ["$eq"],
                "type": ["$all"],  # clumio_backup,aws_snapshot
                "condition": {
                    "type": {"xor": ["clumio_backup", "aws_snapshot"], "and": []}
                },
            },
            "sort": ["-start_timestamp", "start_timestamp"],
        },
    },
    "013": {
        "name": "RestoreDDN",
        "api": "restores/aws/dynamodb-tables",
        "header": "application/api.clumio.restored-aws-dynamodb-tables=v1+json",
        "version": "v1",
        "body_parms": {
            "source": {
                "condition": {
                    "xor": ["securevault_backup", "continuous_backup"],
                    "and": [],
                },
                "continuous_backup": {
                    "table_id": None,
                    "timestamp": None,
                    "use_latest_restorable_time": False,
                },
                "securevault_backup": {"backup_id": None},
                "target": {
                    "condition": {"xor": [], "and": ["table_name", "environment_id"]},
                    "table_name": None,
                    "environment_id": None,
                    "iops": 0,
                    "kms_key_native_id": None,
                    "tags": {},
                    "type": None,
                    "provisioned_throughput": {
                        "read_capacity_units": None,
                        "write_capacity_units": None,
                    },
                    "sse_specification": {
                        "kms_key_type": "DEFAULT",
                        "kms_master_key_id": "null",
                    },
                    "billing_mode": None,
                    "global_secondary_indexes": [
                        {
                            "projection": {
                                "projection_type": None,
                                "non_key_attributes": [None],
                            },
                            "provisioned_throughput": {
                                "read_capacity_units": None,
                                "write_capacity_units": None,
                            },
                            "index_name": "a",
                            "key_schema": [{"attribute_name": "a", "key_type": "HASH"}],
                        }
                    ],
                    "local_secondary_indexes": [
                        {
                            "projection": {
                                "projection_type": None,
                                "non_key_attributes": [None],
                            },
                            "index_name": None,
                            "key_schema": [{"attribute_name": None, "key_type": None}],
                        }
                    ],
                    "table_class": None,
                    "table_name_": None,
                },
            },
        },
        "desc": "Restores the specified DynamoDB table backup to the specified target destination",
        "type": "post",
        "success": 202,
        "query_parms": {"embed": ["read-task"]},
    },
    "109": {
        "name": "ManageAWS",
        "api": "none",
        "header": "none",
        "version": "v1",
        "desc": "manage AWS",
        "type": "get",
        "success": 200,
    },
}
