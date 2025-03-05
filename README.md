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
### Manage Accont
1. Create IAM role to grant account-cross access.
```
// Accounts belongs the declared org will have access.
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalOrgID": "${ORG_ID}"
                }
            }
        }
}
```
2. Create IAM policy.
```
// Option 1. All accounts belongs to the declared org can be accessed.
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": "sts:AssumeRole",
			"Resource": [
				"arn:aws:iam::*:role/OrganizationAccountAccessRole"
			],
			"Condition": {
				"StringEquals": {
					"aws:PrincipalOrgID": "o-u65n3fuskf"
				}
			}
		}
	]
}

// Option 2. Only specified accounts can be accessed.
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": "sts:AssumeRole",
			"Resource": [
				"arn:aws:iam::156041431578:role/OrganizationAccountAccessRole"
			]
		}
	]
}
```

### Local Account
1. Upload `build/clumio_bulk_onboarding.zip` to s3 bucket.
2. Upload cloudformation template `build/clumio_bulk_onboarding_deploy_cft.yaml` and create stack.
3. Execute step function using example input `build/clumio_bulk_onboarding_input.json`.

