# Cloud One Conformity: Automated Setup

Automates the rollout of Conformity across AWS accounts. 

## Installation

Run the following command:

```
pip3 install -r requirements.txt
```

## Usage

1. Set the `CC_API_KEY` and `CC_REGION` environment variables to your Conformity API key and region respectively.

2. Run the script with the `csv` argument:

    ```
    python3 cas.py csv
    ```

    This creates a CSV file called `aws_conformity_accounts.csv`. The contents will look like this:
    
    ```
    Id,Arn,Email,Name,Status,JoinedMethod,JoinedTimestamp,ConformityAccountName,ConformityEnvironment,ConformityCostPackage,ConformityRTM   
    123456789012,arn:aws:organizations::555555555555:account/o-632fj3kfna/123456789012,john@example.com,John Doe,ACTIVE,CREATED,2020-01-13 13:55:33.504000+11:00,,,,
    098765432109,arn:aws:organizations::555555555555:account/o-632fj3kfna/098765432109,jane@example.com,Jane Doe,ACTIVE,CREATED,2020-03-30 16:09:40.916000+11:00,,,,
    ```

3. Open the CSV file and remove the accounts you don't want monitored by Conformity. 
   
4. (Optional) Fill in the following columns:
    * **ConformityAccountName** (Default: AWS account name)
    * **ConformityEnvironment** (No default)
    * **ConformityCostPackage** (Default: None)
    * **ConformityRTM** (Default: Disabled) 

5.  Run the script with the `enable` argument:

    ```
    python3 cas.py enable
    ```
    
## Example

Example output:

```
03-Jun-20 13:27:58 - INFO - system - Obtaining required environment variables...
03-Jun-20 13:27:58 - INFO - system - Getting Conformity Organization ID...
03-Jun-20 13:27:59 - INFO - system - Assuming role ARN: arn:aws:iam::123456789012:role/OrganizationAccountAccessRole...
03-Jun-20 13:28:00 - INFO - system - Creating "cloudformation" client object...
03-Jun-20 13:28:00 - INFO - system - Assuming role ARN: arn:aws:iam::098765432109:role/OrganizationAccountAccessRole...
03-Jun-20 13:28:00 - INFO - system - Creating "cloudformation" client object...
03-Jun-20 13:28:00 - INFO - system - Creating "CloudConformity" stack in account "Lab2"...
03-Jun-20 13:28:02 - INFO - system - Creating "CloudConformity" stack in account "Lab1"...
03-Jun-20 13:28:03 - INFO - system - Waiting for all CloudFormation templates to finish building...
03-Jun-20 13:29:07 - INFO - system - Creating Conformity subscriptions...
03-Jun-20 13:29:07 - INFO - system - Checking if AWS account ID 123456789012 already has a Conformity subscription...
03-Jun-20 13:29:07 - INFO - system - Getting list of Conformity subscriptions...
03-Jun-20 13:29:08 - INFO - system - Creating Conformity subscription for AWS account ID 123456789012...
03-Jun-20 13:29:11 - INFO - system - Checking if AWS account ID 098765432109 already has a Conformity subscription...
03-Jun-20 13:29:11 - INFO - system - Getting list of Conformity subscriptions...
03-Jun-20 13:29:12 - INFO - system - Creating Conformity subscription for AWS account ID 098765432109...
03-Jun-20 13:29:15 - INFO - system - Done
```

# Contact

* Blog: [oznetnerd.com](https://oznetnerd.com)
* Email: will@oznetnerd.com