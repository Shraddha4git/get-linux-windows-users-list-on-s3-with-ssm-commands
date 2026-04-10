output "step_functions_role-arn" {
  value = aws_iam_role.cloudwatch_role.arn
}
output "lambda_os_user_role-arn" {
  value = aws_iam_role.lambda_os_user_role.arn
}
output "cloudwatch_role-arn" {
  value = aws_iam_role.cloudwatch_role.arn
}
