import csv
import datetime
import boto3
import logging
import threading
import os

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

CONST_BUCKET_NAME = os.getenv("BUCKET_NAME", "prod-os-user-management")
CONST_CSV_SUFFIX = os.getenv("CSV_SUFFIX", "-linux-users-list")
CONST_SKIP_TAG_KEY = "OSUserScriptExclude"

REGIONS = ["ap-south-1", "ap-south-2"]
REGION_MAP = {
    "ap-south-1": "MUM(ap-south-1)",
    "ap-south-2": "HYD(ap-south-2)"
}

USER = "User(OS)"
SUDO_USER = "Sudo User(OS)"
UPDATED_AT = "Updated At (User Data)"

FIXED_INSTANCES = []

CONST_USR_CMD = "ls /home/"
CONST_SUDO_USR_CMD = (
    "bash -c \"sudo awk '/^[^#].*ALL=\\\\(ALL/ "
    "{sub(/ALL=\\\\(ALL.*/, \\\"\\\", \\$0); gsub(/,/, \\\"\\\\n\\\", \\$0); print \\$0}' /etc/sudoers\""
)

def put_users_to_server_list(server_list, users, sudousers):
    logger.info("Mapping users and sudo users to server list...")
    for user in users:
        for server in server_list:
            if user[0] == server["InstanceId"]:
                server[USER] = user[1]
                server[UPDATED_AT] = datetime.datetime.now().strftime("%Y-%m-%d")
                break
    for sudo_user in sudousers:
        for server in server_list:
            if sudo_user[0] == server["InstanceId"]:
                server[SUDO_USER] = sudo_user[1]
                server[UPDATED_AT] = datetime.datetime.now().strftime("%Y-%m-%d")
                break
    return server_list

def send_ssm_command(ssm, chunk, command):
    logger.info(f"Sending SSM command: '{command}' to instances: {chunk}")
    try:
        response = ssm.send_command(
            InstanceIds=[chunk],   # Changed to convert string to array, input chunk is in String
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': [command]}
        )
        logger.info(f"SSM Command Response: {response}")
        return response
    except Exception as e:
        logger.info(f"Failed to send SSM command: {e}")
        return None

def get_command_output(ssm, cmd_id, instance_id):
    try:
        logger.info(f"Waiting for command to complete on instance {instance_id}, Command ID: {cmd_id}")
        waiter = ssm.get_waiter('command_executed')
        waiter.wait(CommandId=cmd_id, InstanceId=instance_id, WaiterConfig={'Delay': 5, 'MaxAttempts': 12})
        response = ssm.get_command_invocation(CommandId=cmd_id, InstanceId=instance_id)
        logger.info(f"Command output for {instance_id}: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to get command output for instance {instance_id}: {e}")
        return None

def run_command(run_command_ids, region, command):
    logger.info("run_command() START")
    logger.info(f"Sending SSM command to {len(run_command_ids)} instance(s) in {region}...")
    results = []
    executed_instances = []
    failed_to_send_command_ids = []
    command_status = "Success"

    ssm = boto3.client('ssm', region_name=region)
    for instance_id in run_command_ids:
        try:
            resp = send_ssm_command(ssm, instance_id, command)
            if not resp:
                command_status = "Fail"
                failed_to_send_command_ids.append(instance_id)
                continue

            cmd_id = resp['Command']['CommandId']
            logger.info(f"{region} - Command sent, Command ID: {cmd_id}")

            output = get_command_output(ssm, cmd_id, instance_id)
            if output:
                result = output.get('StandardOutputContent', '').strip()
                logger.info(f"{region} - Standard Output Content for {instance_id}: {result}")
                if result:
                    results.append([instance_id, result])
                    executed_instances.append(instance_id)
                else:
                    logger.warning(f"{region} - No output content for {instance_id}")
            else:
                command_status = "Fail"
                failed_to_send_command_ids.append(instance_id)
        except Exception as e:
                logger.info(f"{region} - Failed to retrieve output for {instance_id}: {e}")
                command_status = "Fail"
                failed_to_send_command_ids.append(instance_id)

    logger.info(f"failed_to_send_command_ids : {failed_to_send_command_ids}")
    logger.info("run_command() END")
    return results, executed_instances, command_status, failed_to_send_command_ids

def get_region_code(region):
    return REGION_MAP.get(region, region)

def describe_instances(region, ec2, environment, specific_instances_linux):
    logger.info(f"Describing instances in {region}...")
    servers = []
    run_command_ids = []

    try:
        if specific_instances_linux:
            logger.info(f"Describing specific instances: {specific_instances_linux}")
            resp = ec2.describe_instances(InstanceIds=specific_instances_linux)
        else:
            resp = ec2.describe_instances(
                Filters=[{'Name':'tag:Environment', 'Values':[environment]}]
                )
        
        logger.info(f"{region} - Describe Instances Response: {resp}")
        for res in resp['Reservations']:
            for inst in res['Instances']:
                if inst.get('Platform', '').lower() == 'windows':
                    logger.info(f"{region} - Skipping Windows instance: {inst['InstanceId']}")
                    continue

                tags = {t['Key']: t['Value'] for t in inst.get("Tags", [])}

                # Check OSUserScriptExclude tag case-insensitively
                if tags.get(CONST_SKIP_TAG_KEY, '').lower() == "true":
                    continue  # Skip instances with OSUserScriptExclude tag
                
                inst_data = {
                    'Region': get_region_code(region),
                    'Environment': tags.get("Environment"),
                    'Role': tags.get("Role"),
                    'Name': tags.get("Name"),
                    'InstanceId': inst["InstanceId"],
                    'Instance state': inst["State"]["Name"],
                    'Instance type': inst["InstanceType"],
                    'Private IP': inst.get("PrivateIpAddress"),
                    USER: None,
                    SUDO_USER: None,
                    UPDATED_AT: None
                }

                if any(inst["InstanceId"] == f["InstanceId"] for f in FIXED_INSTANCES):
                    for f in FIXED_INSTANCES:
                        if inst["InstanceId"] == f["InstanceId"]:
                            inst_data.update({USER: f[USER], SUDO_USER: f[SUDO_USER], UPDATED_AT: f[UPDATED_AT]})
                            break
                elif inst["State"]["Name"] == "running":
                    run_command_ids.append(inst["InstanceId"])
                elif inst["State"]["Name"] == "terminated":
                    continue
                elif inst["State"]["Name"] == "stopped":
                    continue
                else:
                    logger.info(f"{region} - Instance {inst['InstanceId']} is not running.")

                servers.append(inst_data)
    except Exception as e:
        logger.error(f"{region} - Failed to describe instances: {e}")

    return servers, run_command_ids

def process_region(region, output_list, executed_set, command_status_set, environment, region_failed_ids, specific_instances_linux):
    logger.info("process_region() START")
    ec2 = boto3.client('ec2', region_name=region)
    servers, run_command_ids = describe_instances(region, ec2, environment, specific_instances_linux)


    if run_command_ids:
        logger.info(f"{region} - Running commands on instances: {run_command_ids}")
        users, executed_users, command_status, failed_to_send_command_ids = run_command(run_command_ids, region, CONST_USR_CMD)
        sudousers = []
        executed_set.update(executed_users)

        # Server ids after removing the failed server ids received in above step. This will not attempt send command again on failed servers for sudo user retrival
        instance_ids_success = list(set(run_command_ids) - set(failed_to_send_command_ids))
        sudousers, executed_sudo_users, _, _ = run_command(instance_ids_success, region, CONST_SUDO_USR_CMD)
        executed_set.update(executed_sudo_users)

        servers = put_users_to_server_list(servers, users, sudousers)
        command_status_set.add(command_status)
        region_failed_ids.extend(failed_to_send_command_ids)

    output_list.extend(servers)
    logger.info(f"region_failed_ids : {region_failed_ids}")
    logger.info("process_region() END")
    

def lambda_handler(event, context):
    logger.info("Lambda execution started.")
    threads = []
    results = []
    linux_ssm_fail_ids = []
    executed_instance_ids_set = set()
    command_status_set = set()

    # Initialize response object
    response = {
        "L2_Linux_IsError": False,  # Default to no error
        "CSVFilePathLinux": None,
        "linux_ssm_fail_ids": [],
        "Command_Linux_Status": "Fail"
    }

    # Extract Environment and validate
    environment = event.get("Environment", None)
    logger.info(f"Environment: {environment}")
    if not environment:
        logger.error("Environment key is not present in the input")
        response["L2_Linux_IsError"] = True
        response["error_message"] = "Environment key is missing in the input."
        return response

    specific_instances_linux = event.get("ExecuteSpecificInstanceLinux", [])
    specific_instances_windows = event.get("ExecuteSpecificInstanceWindows", [])
    # Skip further process if lambda is invoked for specific instances and intance is not specified in input
    if specific_instances_windows and not specific_instances_linux:
        logger.info("Lambda is invoked for specific instances and instance ID is not specified in input")
        return response

    # Extract and validate Regions
    regions = event.get("Regions", None)
    if not regions:
        logger.error("Regions key is missing.")
        response["L2_Linux_IsError"] = True
        response["error_message"] = "Regions key is missing in the input."
        return response

    for region in regions:
        if region not in REGIONS:
            logger.error(f"Region value ({region}) is not correct. Accepted values are {REGIONS}")
            response["L2_Linux_IsError"] = True
            response["error_message"] = f"Invalid region: {region}."
            return response

    # Extract values from input
    instance_started_fixed = event.get("instance_started_fixed", [])

    # Process each region concurrently
    for region in regions:
        region_result = []
        region_failed_ids = []
        region_executed = set()
        region_command_status = set()
        t = threading.Thread(target=process_region, args=(region, region_result, region_executed, region_command_status, environment, region_failed_ids, specific_instances_linux))
        threads.append((t, region_result, region_executed, region_command_status, region_failed_ids))
        t.start()

    for t, region_result, region_executed, region_command_status, region_failed_ids in threads:
        t.join()
        results.extend(region_result)
        executed_instance_ids_set.update(region_executed)
        command_status_set.update(region_command_status)
        linux_ssm_fail_ids.extend(region_failed_ids)

    # Record executed instances
    executed_linux_instance_ids = list(executed_instance_ids_set)
    logger.info(f"Commands executed on {len(executed_linux_instance_ids)} instance(s).")

    # Generate CSV file if results exist
    if results:
        logger.info(f"Generating CSV for {len(results)} instance(s)...")
        keys = results[0].keys()
        filepath = '/tmp/data.csv'
        with open(filepath, 'w', newline='', encoding='UTF-16') as f:
            writer = csv.writer(f, dialect='excel-tab', quoting=csv.QUOTE_ALL)
            writer.writerow(keys)
            writer.writerows([[r[k] for k in keys] for r in results])

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
        filename = now.strftime("%Y-%m-%d_%H:%M") + CONST_CSV_SUFFIX + f"_{environment}.csv" 
        boto3.resource('s3').meta.client.upload_file(filepath, CONST_BUCKET_NAME, filename)
        logger.info(f"CSV file uploaded to S3 as: {filename}")
        response["CSVFilePathLinux"] = filename
    else:
        logger.info("No instances processed. CSV will not be created.")

        # remove duplicates from list
    linux_ssm_fail_ids = list(set(linux_ssm_fail_ids))

    # Determine command status
    response["Command_Linux_Status"] = "Fail" if "Fail" in command_status_set else "Success"   
    response["linux_ssm_fail_ids"] = linux_ssm_fail_ids
    response["BucketName"] = CONST_BUCKET_NAME

    # Return the final response
    return response

