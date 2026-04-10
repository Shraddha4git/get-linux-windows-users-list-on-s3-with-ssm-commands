resource "aws_iam_role" "lambda_os_user_role" {
  name = "LambdaOsUserManagementRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com" # Allows Lambda to assume this role
        },
        Action: "sts:AssumeRole"
      },
      {
        Effect = "Allow",
        Principal = {
          Service = "states.amazonaws.com" # Allows Step Functions to assume this role
        },
        Action: "sts:AssumeRole"
      }
    ]
  })
    tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

# Attach AWS-managed policies
resource "aws_iam_role_policy_attachment" "lambda_ec2_readonly" {
  role       = aws_iam_role.lambda_os_user_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_full_access" {
  role       = aws_iam_role.lambda_os_user_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_readonly" {
  role       = aws_iam_role.lambda_os_user_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_os_user_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

#Custom policy for missing actions (EC2 Start/Stop, SSM Commands, SNS)
resource "aws_iam_policy" "lambda_os_user_custom_policy" {
  name = "LambdaCustomExecutionPolicy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ssm:SendCommand",
          "ssm:GetCommandInvocation",
          "sns:Publish"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_custom_policy_attachment" {
  role       = aws_iam_role.lambda_os_user_role.name
  policy_arn = aws_iam_policy.lambda_os_user_custom_policy.arn
}

#Step Function Role and Policy Restrict of lambda functions.
resource "aws_iam_role" "step_functions_role" {
  name = "StepFunctionsOsUserManagementRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "states.amazonaws.com" # Step Functions must be explicitly allowed
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
    tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}
resource "aws_iam_policy" "step_functions_lambda_invoke_policy" {
  name = "StepFunctionsLambdaInvokeCustomPolicy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "step-fucntion_policy_attachment" {
  role       = aws_iam_role.step_functions_role.name
  policy_arn = aws_iam_policy.step_functions_lambda_invoke_policy.arn
}

#Cloudwatch Events Role and Policy
resource "aws_iam_role" "cloudwatch_role" {
  name = "CloudWatchStepFunctionOSUserRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "events.amazonaws.com" # Allow CloudWatch to trigger Step Functions
        },
        Action = "sts:AssumeRole"
      },
      {
        Effect = "Allow",
        Principal = {
          Service = "states.amazonaws.com" # Allow Step Functions to assume this role
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Purpose     = "OsUsermanagement"
    CreatedBy   = "Shraddha"
    Environment = "PROD"
    Product     = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}


resource "aws_iam_policy" "cloudwatch_step_function_policy" {
  name = "CloudWatchStepFunctionInvokeCustomPolicy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "states:StartExecution"
        ],
        Resource = "arn:aws:states:ap-south-1:477323665679:stateMachine:OsUserManagement" # Replace with actual ARN
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_policy_attachment" {
  role       = aws_iam_role.cloudwatch_role.name
  policy_arn = aws_iam_policy.cloudwatch_step_function_policy.arn
}

resource "aws_iam_policy" "cloudwatch_lambda_invoke_policy" {
  name = "CloudWatchLambdaInvokeCustomPolicy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction"
        ],
        Resource = [
          "arn:aws:lambda:ap-south-1:477323665679:function:S1-StartInstances",
          "arn:aws:lambda:ap-south-1:477323665679:function:S2-LinuxUsers",
          "arn:aws:lambda:ap-south-1:477323665679:function:S2-WindowsUsers",
          "arn:aws:lambda:ap-south-1:477323665679:function:S3-StopInstances",
          "arn:aws:lambda:ap-south-1:477323665679:function:S4-SendMail"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_lambda_policy_attachment" {
  role       = aws_iam_role.cloudwatch_role.name
  policy_arn = aws_iam_policy.cloudwatch_lambda_invoke_policy.arn
}

resource "aws_iam_policy" "step-function-cloudwatch_logs_policy" {
  name        = "StepFunction_CloudWatch_Logs_Policy"
  description = "Allows creation and management of CloudWatch log groups and streams"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowCloudWatchLogsAccess",
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_cloudwatch_logs_policy" {
  role       = aws_iam_role.cloudwatch_role.name
  policy_arn = aws_iam_policy.cloudwatch_lambda_invoke_policy.arn
}
