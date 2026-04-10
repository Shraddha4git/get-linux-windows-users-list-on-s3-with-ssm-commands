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

CONST_SKIP_TAG_KEY = "OSUserScriptExclude"
CONST_EXCLUDE_ENV_LIST = ["prod", "preprod"]


def lambda_handler(event, context):
    print(f"Input event: {event}")
    regions = event.get("Regions", None)
    environment = event.get("Environment", None)
    instances_to_skip = event.get("SkipInstances", [])

    # New inputs to skip starting instances if present
    specific_instances_linux = event.get("ExecuteSpecificInstanceLinux", [])
    specific_instances_windows = event.get("ExecuteSpecificInstanceWindows", [])

    event["L1_IsError"] = False
    event["ErrorReason"] = ""
    event["started_instances"] = {}
    event["isInstancesStarted"] = False
    event["NoInstanceToProceed"] = False
    event["AdditionalMailInfo"] = ""
    
    if not regions:
        logger.error("Region key is not present in the input")
        event["L1_IsError"] = True
        event["ErrorReason"] = "Region key is not present in the Step Function Input."
        return event
    
    for region in regions:
        if region not in REGIONS:
            logger.error(f"Region value ({region}) is either not correct or not accepted. Accepted values are {REGIONS}.")
            event["L1_IsError"] = True
            event["ErrorReason"] = f"Step Function Input: Region value ({region}) is either not correct or not accepted. Accepted values are {REGIONS}."
            return event

    if not environment:
        logger.error("Environment key is not present in the input.")
        event["L1_IsError"] = True
        event["ErrorReason"] = "Environment key is not present in the Step Function Input."
        return event

    #Skip startup if specific instance sets are provided
    if specific_instances_linux or specific_instances_windows:
        logger.info("Execution is targeted for specific instance(s) only. Skipping start-instance logic.")
        event["NoInstanceToProceed"] = False
        event["AdditionalMailInfo"] += "Execution is targeted for specific instances (ExecuteSpecificInstanceLinux or ExecuteSpecificInstanceWindows). Instance startup skipped.\n"
        return event
        
    logger.info(f"Environment: {environment}")

    if environment.lower() in CONST_EXCLUDE_ENV_LIST:
        # For excluded environment no need to start the instances
        logger.info(f"Environment '{environment}' is in Exclude environment list. No instances need to be started. Skipping to the next step.")
        return event

    # Process instances in each region
    started_instances = {}
    isInstancesStarted = False
    isInstanceExistsInAnyRegion = False 
    
    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        instances_to_be_started = []
        isInstanceExistsInRegion = False 

        try:
            # Use paginator for handling large datasets
            paginator = ec2.get_paginator('describe_instances')
            page_iterator = paginator.paginate()

            for page in page_iterator:  # Iterate through each page of results
                for res in page['Reservations']:
                    for instance in res['Instances']:
                        instance_id = instance['InstanceId']
                        state = instance['State']['Name']

                        '''# Filter instances based on Environment tag from input
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        if tags.get('Environment') != environment:
                            continue  # Skip instances not matching the Environment tag'''

                        # Extract and process instance tags
                        tags = {tag.get('Key', '').strip(): tag.get('Value', '').strip() for tag in instance.get('Tags', [])}
                        logger.debug(f"Extracted Tags for Instance {instance_id}: {tags}")

                        # Check Environment tag case-insensitively
                        if tags.get('Environment', '').lower() != environment.lower():
                            continue  # Skip instances with mismatched Environment tag
                        
                        # Check OSUserScriptExclude tag case-insensitively
                        if tags.get(CONST_SKIP_TAG_KEY, '').lower() == "true":
                            continue  # Skip instances with OSUserScriptExclude tag

                        if state == "terminated":
                            continue  # Skip terminated instances
                        
                        if instance_id in instances_to_skip:
                            continue  # Skip fixed instances (not targetted by the script)

                        # Add stopped instances to the list
                        if state == "stopped":
                            instances_to_be_started.append(instance_id)

                            # Start instance
                            ec2.start_instances(InstanceIds=[instance_id])
                            isInstancesStarted = True
                            isInstanceExistsInRegion = True
                        else:
                            # For all other states
                            isInstanceExistsInRegion = True

        except botocore.exceptions.ClientError as e:
            logger.error(f"Error in Region {region}: {e.response['Error']['Code']}, {e.response['Error']['Message']}")
            # Set L1_IsError to True in case of any error during describe_instances
            event["L1_IsError"] = True
            event["ErrorReason"] += f"Error in Region {region}: {e.response['Error']['Code']}, {e.response['Error']['Message']}\n"


        # Handle no instances available
        if not isInstanceExistsInRegion:
            logger.info(f"No instances are available in region {region} for environment {environment}.")
            event["AdditionalMailInfo"] += f"No instances are available in region {region} for environment {environment}.\n"
            continue  # Continue to the next region
        else:
            isInstanceExistsInAnyRegion = True

        # Collect started instances per region
        started_instances[region] = instances_to_be_started

    # Final update for event output
    if not isInstanceExistsInAnyRegion:
        # If no instances were started across all regions, log a info message
        logger.info("No instances were started in any region. Check the ErrorReason for details.")
        event["NoInstanceToProceed"] = True
        event["AdditionalMailInfo"] += "No instances are available in any region.\n"

    # Add results to the event object
    event["started_instances"] = started_instances
    event["isInstancesStarted"] = isInstancesStarted
    logger.info(f"Final event: {event}")
    # Return the updated event
    return event
