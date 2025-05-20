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


## Build

To build you will need a Unix type shell (`bash`, `zsh`, ...), Python 3.12, `make` and `zip`.

```bash
make build
```

## Steps
### Role creation
* Follow the reference https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-prereqs-self-managed.html
* Please make sure `AWSCloudFormationStackSetAdministrationRole` is created in a control tower account.
* Please make sure `AWSCloudFormationStackSetExecutionRole` is created in each account to deploy stack.


### Deployment in a control tower account
1. Upload `build/clumio_bulk_onboarding.zip` to s3 bucket.
2. Upload cloudformation template `build/clumio_bulk_onboarding_deploy_cft.yaml` and create stack.
3. Execute step function named `clumio-bulk-restore-state-machine` using example input `build/clumio_bulk_onboarding_input.json`.
