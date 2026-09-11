# Clumio Bulk Onboard Automation

> [!IMPORTANT]
> Copyright 2024, Clumio, a Commvault Company.
> Licensed under the Apache License, Version 2.0 (the "License");
> you may not use this file except in compliance with the License.
> You may obtain a copy of the License at
>    http://www.apache.org/licenses/LICENSE-2.0
> Unless required by applicable law or agreed to in writing, software
> distributed under the License is distributed on an "AS IS" BASIS,
> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
> See the License for the specific language governing permissions and
> limitations under the License.


> [!WARNING]
> FOR EXAMPLE PURPOSES ONLY


Connects many AWS accounts to Clumio in one run. A Step Function fans out over the
connection list and invokes a Lambda per account, which creates the Clumio connection
group and deploys the Clumio stack into the target account through a cross-account role.

## Build

To build you will need a Unix type shell (`bash`, `zsh`, ...), Python 3.12, `make` and `zip`.

```bash
make build
```

Artifacts land in `build/`: the Lambda package `clumio_bulk_onboarding.zip`, the two
CloudFormation templates, and the example Step Function input.

## Steps
### Deploy in a control tower account
1. Upload `build/clumio_bulk_onboarding.zip` to s3 bucket.
2. Create a *Stack* using cloudformation template `build/lambda_stack.yaml`.
3. Create a *StackSet* using cloudformation template `build/cross_account_role_stackset.yaml`.
4. Wait for all stacks to be deployed.
5. Execute step function `clumio-bulk-onboard-state-machine` using example input `build/step_function_input.json`.

### Template parameters
`lambda_stack.yaml` (deployed in the control tower account):

| Parameter | Description |
| --- | --- |
| `Bucket` | Bucket holding the uploaded `clumio_bulk_onboarding.zip`. |
| `CrossAccountLambdaRole` | Name of the role the Lambda assumes in each target account. |

`cross_account_role_stackset.yaml` (deployed in every target account):

| Parameter | Description |
| --- | --- |
| `ManagementAccountId` | Control tower account ID that runs the Lambda. |
| `ClumioControlPlaneAccountID` | Clumio control plane account ID. |

### Step function input
| Field | Description |
| --- | --- |
| `bear` | Clumio API bearer token. |
| `api_url` | Clumio API URL. |
| `stack_name` | Name of the Clumio stack created in each target account. |
| `cross_account_cloudformation_role_name` | Cross-account role name, must match `CrossAccountLambdaRole`. |
| `connections` | List of `aws_account_id_list` / `aws_region_list` / `aws_service_list` groups. Each account in a group is connected to every listed region for the listed services. |

The first region in `aws_region_list` is where the Clumio stack is deployed.

## Development

```bash
make install-dev   # development dependencies
make lint          # ruff check
make format        # ruff format
make mypy          # type check
make clean         # remove build and cache directories
```
