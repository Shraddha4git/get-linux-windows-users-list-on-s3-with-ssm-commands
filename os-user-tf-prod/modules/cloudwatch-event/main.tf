variable "cloudwatch_role-arn" { 
}

resource "aws_cloudwatch_event_rule" "monthly_trigger_prod_regular_trigger" {
  name                = "OS-User-Management-StepFunction-Monthly-Trigger-prod-regular"
  description         = "Triggers Step Function on the first friday of every month at 10:30 PM IST"
  schedule_expression = "cron(0 17 ? * 6#1 *)" # first Friday of every month at 10:30 PM IST , 10:30 PM IST = 5:00 PM UTC
    tags = {
    Purpose     = "OsUsermanagement"
    CreatedBy   = "Shraddha"
    Environment = "PROD"
    Product     = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_cloudwatch_event_target" "step_function_target_prod_regular" {
  rule      = aws_cloudwatch_event_rule.monthly_trigger_prod_regular_trigger.name
  target_id = "OS-User-Management-StepFunctionTarget"
  arn       = "arn:aws:states:ap-south-1:477323665679:stateMachine:OsUserManagement" # Replace with actual Step Function ARN
  role_arn  = var.cloudwatch_role-arn
  input = jsonencode({
    Environment = "PROD",
    Regions     = ["ap-south-1"]
  })
}

resource "aws_cloudwatch_event_rule" "monthly_trigger_prod_selective_instances" {
  name                = "OS-User-Management-StepFunction-Monthly-prod-selective-instance"
  description         = "Triggers Step Function on the first friday of every month at 6:00 PM IST, for selective instances which were skipped from Regular trigger"
  schedule_expression = "cron(30 12 ? * 6#1 *)" #first Friday of every month at 6:00 PM IST = 12:30 PM UTC
    tags = {
    Purpose     = "OsUsermanagement"
    CreatedBy   = "Shraddha"
    Environment = "PROD"
    Product     = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_cloudwatch_event_target" "step_function_target_selective_prod" {
  rule      = aws_cloudwatch_event_rule.monthly_trigger_prod_selective_instances.name
  target_id = "OS-User-Management-StepFunctionTarget"
  arn       = "arn:aws:states:ap-south-1:477323665679:stateMachine:OsUserManagement" # Replace with actual Step Function ARN
  role_arn  = var.cloudwatch_role-arn
  input = jsonencode({
    Environment                  = "PROD"
    Regions                     = ["ap-south-1"]
    ExecuteSpecificInstanceLinux  = ["i-079512247b353e1f6", "i-0fcab21904de8907b", "i-0f04282707ca849e8", "i-0f2efb0adc0467c35", "i-0a129ae395542ae8f", "i-0d3eab2e4e958b517", "i-030f3b16d84476c31", "i-01cf73538a02d1257", "i-02ec878d1cc259397", "i-07df03d6ea4c055a9"]
    ExecuteSpecificInstanceWindows = []
  })
}

resource "aws_cloudwatch_event_rule" "monthly_trigger_preprod" {
  name                = "OS-User-Management-StepFunction-Monthly-Trigger-preprod"
  description         = "Triggers Step Function on the the first Monday (2#1) of every month, at 15:00 UTC, which is 8:30 PM IST"
  schedule_expression = "cron(0 15 ? * 2#1 *)" #trigger on the first Monday (2#1) of every month, at 15:00 UTC, which is 8:30 PM IST

    tags = {
    Purpose     = "OsUsermanagement"
    CreatedBy   = "Shraddha"
    Environment = "PROD"
    Product     = "ALLPRODUCT"
    Owner = "Shraddha"
  }
}

resource "aws_cloudwatch_event_target" "step_function_target-preprod" {
  rule      = aws_cloudwatch_event_rule.monthly_trigger_preprod.name
  target_id = "OS-User-Management-StepFunctionTarget-preprod"
  arn       = "arn:aws:states:ap-south-1:477323665679:stateMachine:OsUserManagement" # Replace with actual Step Function ARN
  role_arn  = var.cloudwatch_role-arn
  input = jsonencode({
    Environment = "PREPROD",
    Regions     = ["ap-south-1"]
  })
}