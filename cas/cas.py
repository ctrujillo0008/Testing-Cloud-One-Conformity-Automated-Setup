import os
from onnlogger import Loggers
from libs import CcCfn
from libs import Cc
from onnmisc import csv_to_list
import sys

DEFAULT_LOG_LEVEL = 'INFO'
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE_PATH = f'{CURRENT_DIR}/log.txt'
DEFAULT_CSV_FILENAME = f'{CURRENT_DIR}/aws_conformity_accounts.csv'


class CcAutoSetup:
    def __init__(self, logger):
        self.logger = logger
        self.cfn = CcCfn(self.logger)
        self.cc = Cc(self.logger)

    def generate_account_csv(self):
        """Creates CSV file containing AWS account numbers

        Default filename is `aws_conformity_accounts.csv`

        Examples:
            Example output:

            Id,Arn,Email,Name,Status,JoinedMethod,JoinedTimestamp,ConformityAccountName,ConformityEnvironment,ConformityCostPackage,ConformityRTM
            123456789012,arn:aws:organizations::555555555555:account/o-632fj3kfna/123456789012,john@example.com,John Doe,ACTIVE,CREATED,2020-01-13 13:55:33.504000+11:00,,,,
            098765432109,arn:aws:organizations::555555555555:account/o-632fj3kfna/098765432109,jane@example.com,Jane Doe,ACTIVE,CREATED,2020-03-30 16:09:40.916000+11:00,,,,

        Returns:
            None

        """
        self.cfn.generate_account_csv(DEFAULT_CSV_FILENAME)

        self.logger.entry('info', 'Done')

    def enable(self, enable_type='enable', input_file_path=DEFAULT_CSV_FILENAME):
        """Enable Conformity on specified accounts

        Reads `aws_conformity_accounts.csv` and sets up CloudFormation & Conformity accordingly.

        `enable_type` can be either `enable` or `enable_cc`. The former will create both the CFN template and the Conformity account. The latter will only create the Conformity account. This enables users to deploy the CFN through other means, e.g StackSet.

        Args:
            enable_type: `enable` or `enable_cc`
            input_file_path (str): Path to `aws_conformity_accounts.csv`

        Returns:
            None
        """
        # read CSV & ensure correct account numbers are provided
        csv_list = self._read_csv(input_file_path)

        # convert list to dict for easier processing
        csv_dict = self._list_to_dict(key_name='Id', list_obj=csv_list)

        if enable_type == 'enable':
            self.cfn.enable(self.cc.org_id, csv_dict)

        self.cc.enable(csv_dict)
        self.logger.entry('info', 'Done')

    def disable(self, input_file_path=DEFAULT_CSV_FILENAME):
        """Removes Conformity subscriptions

        Reads `aws_conformity_accounts.csv` and removes the associated Conformity subscriptions.

        Args:
            input_file_path (str): Path to `aws_conformity_accounts.csv`

        Returns:
            None

        """
        csv_list = self._read_csv(input_file_path)

        self.cc.disable(csv_list)
        self.logger.entry('info', 'Done')

    @staticmethod
    def _read_csv(input_file_path) -> list:
        """Description:
            Reads CSV file into a list of dicts

            When CSV files are opened in Excel, it removes leading 0's from integers. This method ensures the Account IDs are correct by pulling them from the ARN.

        Args:
            input_file_path (str): Path to `aws_conformity_accounts.csv`

        Example:
            Example usage:

            >>> from pprint import pprint
            >>> csv_list = self._read_csv(input_file_path)
            >>> pprint(csv_list)
             [{'Arn': 'arn:aws:organizations::1234567890123:account/o-f324ds23gs/098765432109',
              'ConformityAccountName': '',
              'ConformityCostPackage': '',
              'ConformityEnvironment': '',
              'ConformityRTM': '',
              'Email': 'example@example.com',
              'Id': '846381620374',
              'JoinedMethod': 'CREATED',
              'JoinedTimestamp': '2020-04-09 09:12:43.849000+10:00',
              'Name': 'example',
              'Status': 'ACTIVE'}]

        Returns:
            List of dicts
        """
        csv_list = csv_to_list(input_file_path)

        for entry in csv_list:
            arn = entry['Arn']
            account_id = arn.rsplit('/', 1)[1]
            entry['Id'] = account_id

        return csv_list

    @staticmethod
    def _list_to_dict(key_name, list_obj):
        """Description:
            Converts a list of dicts into a dict with nested dicts

            `key_name` is popped from each list entry and made the key of that same dictionary

        Args:
            key_name: Dictionary entry which becomes the key
            list_obj: List of dicts

        Example:
            Example usage:

            >>> from pprint import pprint
            >>> account_list = [{'Arn': 'arn:aws:organizations::1234567890123:account/o-f324ds23gs/098765432109',
              'ConformityAccountName': '',
              'ConformityCostPackage': '',
              'ConformityEnvironment': '',
              'ConformityRTM': '',
              'Email': 'example@example.com',
              'Id': '223344556677',
              'JoinedMethod': 'CREATED',
              'JoinedTimestamp': '2020-04-09 09:12:43.849000+10:00',
              'Name': 'example',
              'Status': 'ACTIVE'}]
            >>> account_dict = self._list_to_dict(key_name='Id', list_obj=account_list)
            >>> pprint(account_dict)
            {'223344556677': {'Arn': 'arn:aws:organizations::1234567890123:account/o-f324ds23gs/098765432109',
                  'ConformityAccountName': '',
                  'ConformityCostPackage': '',
                  'ConformityEnvironment': '',
                  'ConformityRTM': '',
                  'Email': 'example@example.com',
                  'JoinedMethod': 'CREATED',
                  'JoinedTimestamp': '2020-04-09 09:12:43.849000+10:00',
                  'Name': 'example',
                  'Status': 'ACTIVE'}}

        Returns:
            dict

        """
        output = dict()

        for entry in list_obj:
            account_id = entry.pop(key_name)
            output[account_id] = entry

        return output


def main():
    # argv1 (mandatory): Action to take
    # argv2 (optional): Debug level

    acceptable_args = ['enable', 'disable', 'csv', 'enable_cc']
    args = sys.argv

    if args == 1:
        sys.exit('Error: Please specify an argument')

    arg = sys.argv[1].lower()

    if arg not in acceptable_args:
        sys.exit('Error: Specified argument is not valid')

    try:
        log_level = sys.argv[2].upper()

    except IndexError:
        log_level = DEFAULT_LOG_LEVEL

    logger = Loggers(logger_name='CcAutoSetup', console_logger=True, log_level=log_level, log_file_path=LOG_FILE_PATH)
    auto_setup = CcAutoSetup(logger)

    if arg == 'csv':
        auto_setup.generate_account_csv()

    elif 'enable' in arg:
        auto_setup.enable(arg)

    elif arg == 'disable':
        auto_setup.disable()


if __name__ == '__main__':
    main()
