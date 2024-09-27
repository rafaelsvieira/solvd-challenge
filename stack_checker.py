import os
import boto3
import logging
from botocore.exceptions import ClientError
import argparse
import json

class CloudFormationStackChecker:
    def __init__(self, stack_name, debug=False):
        self.stack_name = stack_name
        self.debug = debug

        self.logger = logging.getLogger(__name__)
        # Disable botocore logger
        logging.getLogger('botocore').setLevel(logging.CRITICAL)
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

        self.logger.debug("Initializing CloudFormationStackChecker...")

        if not self.check_aws_environment_variables():
            raise Exception("Missing required environment variables.")

        self.cloudformation = boto3.client(
            'cloudformation',
            region_name=os.getenv('AWS_REGION')
        )

        if not self.check_access():
            raise Exception("Access to CloudFormation is denied or invalid credentials.")

    def check_aws_environment_variables(self):
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_SESSION_TOKEN',
            'AWS_REGION'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            self.logger.error(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            return False

        self.logger.debug("All required environment variables are set.")
        return True

    def check_access(self):
        try:
            self.cloudformation.describe_stacks()
            self.logger.debug("Access to CloudFormation is verified.")
            return True
        except ClientError as e:
            self.logger.error(f"Access check failed: {str(e)}")
            return False

    def get_stack_status(self):
        try:
            self.logger.debug(f"Fetching stack status for {self.stack_name}...")
            stack_info = self.cloudformation.describe_stacks(StackName=self.stack_name)
            stack_status = stack_info['Stacks'][0]['StackStatus']
            self.logger.debug(f"Stack status for {self.stack_name}: {stack_status}")
            return stack_status
        except ClientError as e:
            self.logger.error(f"Error fetching stack status: {str(e)}")
            return {"error": str(e)}

    def get_failed_resource(self, stack_name):
        try:
            self.logger.debug(f"Fetching stack events for {stack_name}...")
            events = self.cloudformation.describe_stack_events(StackName=stack_name)['StackEvents']

            for event in events:
                if 'ROLLBACK' in event['ResourceStatus']:
                    self.logger.debug(f"Rollback triggered by resource: {event['LogicalResourceId']}")
                    return {
                        "ResourceName": event['LogicalResourceId'],
                        "ResourceType": event['ResourceType'],
                        "ErrorMessage": event.get('ResourceStatusReason', 'No error message')
                    }

            return None

        except ClientError as e:
            self.logger.error(f"Error fetching stack events: {str(e)}")
            return {"error": str(e)}

    def run(self):
        self.logger.debug(f"Checking stack {self.stack_name}...")
        stack_status = self.get_stack_status()

        output = {
            "StackName": self.stack_name,
            "StackStatus": stack_status
        }

        if "ROLLBACK" in stack_status:
            failed_resource = self.get_failed_resource(self.stack_name)

            if failed_resource:
                output["FailedResource"] = failed_resource

        print(json.dumps(output, indent=4))

def main():
    parser = argparse.ArgumentParser(description='AWS CloudFormation Stack Checker')
    parser.add_argument('stack_name', type=str, help='The name of the CloudFormation stack')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    try:
        checker = CloudFormationStackChecker(stack_name=args.stack_name, debug=args.debug)
        checker.run()
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
