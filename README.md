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
### Deploy in a control tower account
1. Upload `build/clumio_bulk_onboarding.zip` to s3 bucket.
2. Create a *Stack* using cloudformation template `build/lambda_stack.yaml`.
3. Create a *StackSet* using cloudformation template `build/cross_account_role_stackset.yaml`.
4. Wait for all stacks to be deployed.
5. Execute step function `clumio-bulk-restore-state-machine` using example input `build/step_function_input.json`.