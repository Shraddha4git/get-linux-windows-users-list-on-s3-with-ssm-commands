import boto3
import botocore
import logging

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Target region
REGIONS = ["ap-south-1", "ap-south-2"]
REGION_MAP = {
"ap-south-1": "MUM(ap-south-1)",
"ap-south-2": "HYD(ap-south-2)"
}

def lambda_handler(event, context):
    logger.info(f"Input event: {event}")
    started_instances = event.get("started_instances", None)

    stopped_instances = []  # Instances successfully stopped
    stop_failed_instances = []  # Instances that failed to stop

    if started_instances:
        for key in started_instances:
            region = key
            ec2 = boto3.client('ec2', region_name=region)

            instances_to_stop = started_instances[key]
            try:
                logger.info(f"Attempting to stop instances: {instances_to_stop} in region: {region}")
                response = ec2.stop_instances(InstanceIds=instances_to_stop)
                logger.info(f"Response from stop_instances: {response}")
                # Iterate over each instance in the response
                for instance in response['StoppingInstances']:
                    instance_id = instance['InstanceId']
                    current_state = instance['CurrentState']['Name']

                    if current_state in ['stopping', 'stopped']:
                        # Successfully transitioning to stopping or stopped
                        stopped_instances.append(instance_id)
                    else:
                        # Failed to transition to stopping or stopped
                        stop_failed_instances.append(instance_id)

            except botocore.exceptions.ClientError as e:
                logger.error(f"Error stopping instances in region {region}: {e}")
                # Add only those instances not processed in the response
                stop_failed_instances.extend(
                    instance for instance in instances_to_stop if instance not in stopped_instances
                )
    
    else:
        logger.info("No servers were STARTED, hence stop instance action is skipped")
    
    event["FailedToStop"] = stop_failed_instances
    return event
    
