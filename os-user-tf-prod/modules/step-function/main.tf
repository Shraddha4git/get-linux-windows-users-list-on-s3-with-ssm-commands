variable "step_functions_role-arn" {
}
resource "aws_sfn_state_machine" "os-user-ec2-event-state-machine" {
  name     = "OsUserManagement"
  role_arn = var.step_functions_role-arn
  definition = file("${path.module}/step-function.json")
  tags = {
    Purpose = "OsUsermanagement"
    CreatedBy = "Shraddha"
    Environment = "PROD"
    Product = "ALLPRODUCT"
    Owner = "Shraddha"
  }

  logging_configuration {
    include_execution_data = true
    level                  = "ALL"
    log_destination = "arn:aws:logs:ap-south-1:477323665679:log-group:/aws/vendedlogs/states/OsUserManagement-Logs:*"
  }

  tracing_configuration {
    enabled = true
  }
}