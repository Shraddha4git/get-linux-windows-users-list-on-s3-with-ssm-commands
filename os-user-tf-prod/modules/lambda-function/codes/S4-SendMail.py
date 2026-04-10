import boto3
import logging
import os
from datetime import datetime, timedelta

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

TOPIC_ARN = os.getenv("TOPIC_ARN")  # Fetch from environment variables

if not TOPIC_ARN:
    raise ValueError("SNS_TOPIC_ARN environment variable is missing. Set it in Lambda configuration.")

def send_sns_notification(topic_arn, message):
    try:
        sns = boto3.client('sns')
        response = sns.publish(
            TopicArn=topic_arn,
            Subject="OS Account Management Automation Tool",
            Message=message
        )
        logger.info(f"SNS notification sent successfully: {response}")
    except Exception as e:
        logger.error(f"Failed to send SNS notification: {e}")
        raise

def convert_to_ist(utc_time_str):
    """Convert UTC time string to IST (Indian Standard Time)."""
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%Y-%m-%d %H:%M:%S")

def lambda_handler(event, context):
    logger.info("Execution started.")
    print(event)

    # Extract and convert the Step Function start time to IST
    step_function_start_time_utc = event.get("StepFunctionStartTime", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    step_function_start_time_ist = convert_to_ist(step_function_start_time_utc)

    # Initialize variables for file paths
    CSVFilePathLinux = None
    CSVFilePathWindows = None
    linux_ssm_fail_ids = []
    windows_ssm_fail_ids = []

    # Extract details from ParallelStateOutput
    ParallelStateOutput = event.get("ParallelStateOutput", [])
    bucket_name = None
    for output in ParallelStateOutput:
        if output.get("CSVFilePathLinux"):
            CSVFilePathLinux = output.get("CSVFilePathLinux")
        if output.get("CSVFilePathWindows"):
            CSVFilePathWindows = output.get("CSVFilePathWindows")
        if output.get("BucketName") and not bucket_name:
            bucket_name = output.get("BucketName")
        if output.get("linux_ssm_fail_ids"):
            linux_ssm_fail_ids = output.get("linux_ssm_fail_ids")
        if output.get("windows_ssm_fail_ids"):
            windows_ssm_fail_ids = output.get("windows_ssm_fail_ids")

    # Log extracted paths
    print(f"CSVFilePathLinux: {CSVFilePathLinux}")
    print(f"CSVFilePathWindows: {CSVFilePathWindows}")
    print(f"linux_ssm_fail_ids: {linux_ssm_fail_ids}")
    print(f"windows_ssm_fail_ids: {windows_ssm_fail_ids}")
    

    # Check for errors
    L1_IsError = event.get("L1_IsError", False)
    ErrorReason = event.get("ErrorReason", "")
    additional_info = event.get("AdditionalMailInfo", None)
    message = ""

    # Construct the SNS message body
    if L1_IsError:  # If there is an error
        message += f"""
        Script Execution Report:
        The Script was not successful. Errors received:
        {ErrorReason} \n
        """
        if additional_info:
            message += f"- Additional Execution Info: {additional_info}\n"

    else:  # If there is no error
        message = f"""
        Script Execution Report:
        The Script for getting OS user details started at: {step_function_start_time_ist}.
        """
        if CSVFilePathLinux:  # Add only if the value is not null or blank
            message += f"- The OS user list for Linux is uploaded to the bucket: {bucket_name} with the file name: {CSVFilePathLinux}.\n"
        
        if CSVFilePathWindows:  # Add only if the value is not null or blank
            message += f"- The OS user list for Windows is uploaded to the bucket: {bucket_name} with the file name: {CSVFilePathWindows}.\n"
        
        if not CSVFilePathLinux:
            message += f"\n- The OS user list for Linux is empty (Linux instances are not available). Hence no CSV was uploaded to S3.\n"
        if not CSVFilePathWindows:
            message += f"\n- The OS user list for Windows is empty (Windows instances are not available). Hence no CSV was uploaded to S3.\n"

        if additional_info:
            message += f"\n- Additional Execution Info: {additional_info}.\n"

        if linux_ssm_fail_ids:
            message += f"\n- Script could not extract OS User information for below linux servers. Possible reason servers are not SSM Managed.\n{linux_ssm_fail_ids}\n"

        if windows_ssm_fail_ids:
            message += f"\n- Script could not extract OS User information for below windows servers. Possible reason servers are not SSM Managed.\n{windows_ssm_fail_ids}\n"

    # Log the constructed message
    logger.info(f"Constructed SNS message: {message}")

    # Publish the SNS notification
    send_sns_notification(TOPIC_ARN, message)

    logger.info("Execution finished.")
    return {"status": "SNS notification sent successfully"}

  