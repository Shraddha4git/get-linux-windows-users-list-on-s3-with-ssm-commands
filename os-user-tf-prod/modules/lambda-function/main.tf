resource "aws_lambda_function" "S1-StartInstances-lambda" {
  function_name = "S1-StartInstances"
  description = "OsUserManagement: Starts EC2s with Environment=UAT.Excludes instances via 1. SkipInstances list in StepFunction input or 2.permanent exclusion using OSUserScriptExclude=true tag"
  role          = var.lambda_os_user_role-arn
  runtime       = "python3.13"
  handler       = "S1-StartInstances.lambda_handler"
  filename      = "./modules/lambda-function/codes/S1-StartInstances.zip"
  timeout       = 300
    tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_lambda_function" "S2-LinuxUsers-lambda" {
  function_name = "S2-LinuxUsers"
  description = "OsUserManagement: Retrieves Linux user data via SSM from running EC2s with Environment tags across regions. Filters out Windows/excluded instances. Generates and uploads a CSV of system/sudo users to S3. Supports audits and automations with user tracking."
  role          = var.lambda_os_user_role-arn
  runtime       = "python3.13"
  handler       = "S2-LinuxUsers.lambda_handler"
  filename      = "./modules/lambda-function/codes/S2-LinuxUsers.zip"
  timeout       = 900
  environment {
    variables = {
      BUCKET_NAME = var.BUCKET_NAME
    }
  }
    tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_lambda_function" "S2-WindowsUsers-lambda" {
  function_name = "S2-WindowsUsers"
  description = "OsUserManagement: Retrieves Windows user data via SSM from EC2s tagged by Environment. Filters Linux/excluded instances,fetches standard/admin users,logs outcomes,uploads a CSV to S3—supporting."
  role          = var.lambda_os_user_role-arn
  runtime       = "python3.13"
  handler       = "S2-WindowsUsers.lambda_handler"
  filename      = "./modules/lambda-function/codes/S2-WindowsUsers.zip"
  timeout       = 900
  environment {
    variables = {
      BUCKET_NAME = var.BUCKET_NAME
    }
  }
      tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_lambda_function" "S3-StopInstances-lambda" {
  function_name = "S3-StopInstances"
  description = "OsUserManagement: Stops EC2s started earlier in the workflow using event input.Stops them via EC2 API, logs transitions, handles failures,updates the event with stopped/failed instances"
  role          = var.lambda_os_user_role-arn
  runtime       = "python3.13"
  handler       = "S3-StopInstances.lambda_handler"
  filename      = "./modules/lambda-function/codes/S3-StopInstances.zip"
  timeout       = 300
      tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_lambda_function" "S4-SendMail-lambda" {
  function_name = "S4-SendMail"
  description = "OsUserManagement: Sends execution reports via SNS after workflow completion. Extracts S3 paths, errors, and user data; formats and sends summaries with CSV status for Linux/Windows users. Logs failures, reporting missing data for troubleshooting."
  role          = var.lambda_os_user_role-arn
  runtime       = "python3.13"
  handler       = "S4-SendMail.lambda_handler"
  filename      = "./modules/lambda-function/codes/S4-SendMail.zip"
  timeout       = 300
  environment {
    variables = {
      BUCKET_NAME = var.BUCKET_NAME
      TOPIC_ARN = var.TOPIC_ARN
    }
  }
      tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}
