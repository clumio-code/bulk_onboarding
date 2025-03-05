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

# FOR EXAMPLE PURPOSES ONLY

#
# Requirements: 
#  Local account to install lambda and step function
#  Role in local account that can assume OU role
#  OU role that can launch the deployment CFTs in all of the accounts to be onboarded
#  Policy in OU role that will contain the assume role information for the child accounts (note - automation updates this policy as it runs)
#  S3 bucket - needs to be in same region where lambda will run
#
# Upload lambda zip file "clumio_connect_code.zip" into S3 bucket
# Modify the lambda deployment cft "clumio_bulk_onboar_lambda_deploy_cft.yaml" to include your S3 bucket name and modify key name to include prefix if lambda zip is not in root of the bucket
# Run the lambda deployment CFT
# Modify step function json "clumio_bulk_onboard_aws_account_step_function.json" to point to your lambda function (line 32).  Note:  name will be the same but aws account id an region will be different.
# Create a new step function.  select on the code option in the builder.  copy and paste code from your modified step function json file.
#
# Modify inputs json "clumio_bulk_onbaord_example_inputs.json" to include your accounts, regions, and services"
# Execute the step function passing it the contents of the modified inputs json.

# clumio_connet_aws_account.py - this is the lambda function
# clumio_sdk_v8c.py - this is the "helper" sdk
