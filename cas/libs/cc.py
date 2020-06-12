from onnconformity import Conformity
from onnmisc import csv_to_list


class Cc:
    def __init__(self, logger):
        self.logger = logger
        self.cc = Conformity(logger)
        self.org_id = self.cc.org_id

    def enable(self, csv_entries):
        self.logger.entry('info', 'Creating Conformity subscriptions...')

        for account_id, settings in csv_entries.items():
            role_arn = settings.get('CloudConformityRoleArn', f'arn:aws:iam::{account_id}:role/CloudConformity')
            account_env = settings.get('ConformityEnvironment')

            get_cost_package = settings.get('ConformityCostPackage')
            cost_package = True if 'true' in get_cost_package.lower() else False

            get_rtm = settings.get('ConformityRTM')
            rtm = True if 'true' in get_rtm.lower() else False

            account_name = settings['ConformityAccountName']

            # Use AWS account name if user did not specify a Conformity account name
            if not account_name:
                account_name = settings['Name']

            self.logger.entry('debug', f'Creating subscription for "{account_name}" ({account_id})')

            self.cc.create_subscription(account_id, role_arn, account_name, account_env, cost_package, rtm)

    def disable(self, csv_list):
        aws_ids_to_delete = self._get_delete_aws_ids(csv_list)
        conformity_delete_ids = self._get_delete_conformity_ids(aws_ids_to_delete)

        for conformity_id in conformity_delete_ids:
            self.cc.delete_subscription(conformity_id)

    def _get_delete_conformity_ids(self, aws_ids_to_delete):
        conformity_delete_ids = []

        conformity_subscriptions = self.cc.list_subscriptions()

        for to_delete_id in aws_ids_to_delete:
            for subscription in conformity_subscriptions['data']:
                sub_id = subscription['attributes'].get('awsaccount-id')

                if not sub_id or sub_id != to_delete_id:
                    continue

                conformity_id = subscription['id']
                conformity_delete_ids.append(conformity_id)

        return conformity_delete_ids

    def _get_delete_aws_ids(self, csv_list) -> list:
        self.logger.entry('info', 'Extracting AWS IDs from CSV file...')

        delete_list = []

        for entry in csv_list:
            aws_id = entry['Id']
            conformity_account_name = entry['ConformityAccountName']

            self.logger.entry('debug', f'Found: {conformity_account_name} ({aws_id})')
            delete_list.append(aws_id)

        return delete_list
