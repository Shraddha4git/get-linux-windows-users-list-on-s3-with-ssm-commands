
module "s3" {
  source = "./modules/s3"
}

module "iam" {
  source     = "./modules/iam"
}
#this is not required for now, once all setup is done then we can add emails of members who need the notification
module "sns" {
  source = "./modules/sns"
}

module "lambda-function" {
  source = "./modules/lambda-function"
  BUCKET_NAME = module.s3.BUCKET_NAME
  lambda_os_user_role-arn = module.iam.lambda_os_user_role-arn
  TOPIC_ARN = module.sns.TOPIC_ARN
}

module "step-function" {
  source = "./modules/step-function"
  step_functions_role-arn = module.iam.step_functions_role-arn
}

module "cloudwatch-event" {
  source = "./modules/cloudwatch-event"
  cloudwatch_role-arn = module.iam.cloudwatch_role-arn
  depends_on = [ module.iam ]
}
