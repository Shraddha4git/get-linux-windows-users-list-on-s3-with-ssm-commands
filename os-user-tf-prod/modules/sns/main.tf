resource "aws_sns_topic" "os_user_management_topic" {
  name = "os-user-management-sns-topic"
    tags = {
    Environment = "PROD"
    Purpose = "OsUserManagement"
    Owner = "Shraddha"
    CreatedBy = "Shraddha"
    Product = "ALLPRODUCT"
  }
}

resource "aws_sns_topic_subscription" "email_subscription-1" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "shraddha.suryawanshi@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-2" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "anil11.ejagar@nttdata.com"
}

resource "aws_sns_topic_subscription" "email_subscription-3" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "smathai@cloudhedge.io"
}

resource "aws_sns_topic_subscription" "email_subscription-4" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "mayur.chandekar@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-5" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "ikufumi13.goda@atomtech.in"
}


resource "aws_sns_topic_subscription" "email_subscription-6" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "sanjeev16.singh@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-7" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "rabindranath.moharana@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-8" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "osden.rodrigues@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-9" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "mayur.prajapati@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-10" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "saibalaji.kotturu@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-11" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "bharat.bansode@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-12" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "umesh.pal@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-13" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "aditya.adhatrao@atomtech.in"
}

resource "aws_sns_topic_subscription" "email_subscription-14" {
  topic_arn = aws_sns_topic.os_user_management_topic.arn
  protocol  = "email"
  endpoint  = "sanjay.vishwakarma@atomtech.in"
}

output "TOPIC_ARN" {
  value = aws_sns_topic.os_user_management_topic.arn
}