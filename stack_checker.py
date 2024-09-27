import os
import boto3
import argparse

class CloudFormationStackChecker:
    def __init__(self, stack_name):
        self.stack_name = stack_name

        self.cloudformation = boto3.client(
            'cloudformation',
            region_name=os.getenv('AWS_REGION')
        )

def main():
    parser = argparse.ArgumentParser(description='AWS CloudFormation Stack Checker')
    parser.add_argument('stack_name', type=str, help='The name of the CloudFormation stack')

    args = parser.parse_args()

    try:
        checker = CloudFormationStackChecker(stack_name=args.stack_name)
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
