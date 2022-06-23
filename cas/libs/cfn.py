import csv
import boto3
from onnawscfn import Cfn
from onnawsorgs import Orgs

STS_SESSION_NAME = 'CcAutomatedSetup'
CC_CFN_REGION = 'us-east-1'
CC_AWS_ACCOUNT_ID = '717210094962'
STACK_NAME = 'CloudConformity'
TEMPLATE_URL = 'https://s3-us-west-2.amazonaws.com/cloudconformity/CloudConformity.template'


class CcCfn:
    def __init__(self, logger):
        self.logger = logger
        self.onn_cfn = Cfn(self.logger)
        self.onn_orgs = Orgs(self.logger)

    def generate_account_csv(self, output_file_path):
        """Creates CSV file containing AWS account numbers

        Default filename is `aws_conformity_accounts.csv`

        Examples:
            Example output:

            Id,Arn,Email,Name,Status,JoinedMethod,JoinedTimestamp,ConformityAccountName,ConformityEnvironment,ConformityCostPackage
            123456789012,arn:aws:organizations::555555555555:account/o-632fj3kfna/123456789012,john@example.com,John Doe,ACTIVE,CREATED,2020-01-13 13:55:33.504000+11:00,,,,
            098765432109,arn:aws:organizations::555555555555:account/o-632fj3kfna/098765432109,jane@example.com,Jane Doe,ACTIVE,CREATED,2020-03-30 16:09:40.916000+11:00,,,,

        Returns:
            None
        """
        account_details = self.onn_orgs.get_accounts()

        aws_headers = list(account_details[0].keys())
        cc_headers = ['ConformityAccountName', 'ConformityEnvironment', 'ConformityCostPackage']
        csv_headers = aws_headers + cc_headers

        self.logger.entry('info', 'Exporting accounts to CSV file...')

        with open(output_file_path, 'w') as f:
            dict_writer = csv.DictWriter(f, csv_headers)
            dict_writer.writeheader()
            dict_writer.writerows(account_details)

        self.logger.entry('debug', 'Done')

    def enable(self, org_id, csv_entries):
        aws_account_ids = list(csv_entries.keys())
        assumed_cfn_objects = self._get_cfn_assumed_objects(aws_account_ids)

        for account_id, settings in csv_entries.items():
            self.logger.entry('debug', f'Creating assumed CloudFormation client for {account_id}')
            assumed_cf_client = assumed_cfn_objects[account_id]
            aws_account_name = settings['Name']
            self._create_cc_stack(org_id, assumed_cf_client, aws_account_name)

        self.logger.entry('info', 'Waiting for all CloudFormation templates to finish building...')

        for account_id, settings in csv_entries.items():
            self.logger.entry('debug', f'Waiting for "{STACK_NAME}" in {account_id} to complete...')
            assumed_cf_client = assumed_cfn_objects[account_id]
            self.onn_cfn.waiter('stack_create_complete', STACK_NAME, assumed_cf_client)

            cfn_outputs = assumed_cf_client.describe_stacks(StackName=STACK_NAME)['Stacks'][0]['Outputs']
            dict_outputs = self.onn_cfn.outputs_to_dict(cfn_outputs)
            conformity_arn = dict_outputs['CloudConformityRoleArn']
            settings['CloudConformityRoleArn'] = conformity_arn

            self.logger.entry('debug', 'Done')

    def _get_cfn_assumed_objects(self, account_ids):
        assumed_cfn_objects = {}

        for account_id in account_ids:
            if self.onn_orgs.root_account_id == account_id:
                self.logger.entry('debug', f'Account ID "{account_id}" is the parent account. Skipping assume role '
                                           f'process and used the default client instead')

                cf_client = boto3.client('cloudformation', region_name=CC_CFN_REGION)

            else:
                assumed_credentials = self.onn_orgs.assume_role(account_id, STS_SESSION_NAME)
                cf_client = self.onn_orgs.get_assumed_client('cloudformation', assumed_credentials,
                                                             region_name=CC_CFN_REGION)

            assumed_cfn_objects[account_id] = cf_client

        return assumed_cfn_objects

    def _create_cc_stack(self, org_id, assumed_cf_client, aws_account_name):
        params = {
            'AccountId': CC_AWS_ACCOUNT_ID,
            'ExternalId': org_id,
        }

        cfn_params = self.onn_cfn.dict_to_cfn_params(params)

        cfn_settings = {
            'StackName': STACK_NAME,
            'TemplateURL': TEMPLATE_URL,
            'Parameters': cfn_params,
            'Capabilities': ['CAPABILITY_NAMED_IAM'],
        }

        cfn_obj = self.onn_cfn.create_stack(account_name=aws_account_name, cf_client=assumed_cf_client, **cfn_settings)

        return cfn_obj
