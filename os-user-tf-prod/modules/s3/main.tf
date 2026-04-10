# Create S3 bucket
resource "aws_s3_bucket" "os-user-list-s3-bucket" {
  bucket = "prod-os-user-management"
   tags = {
    Environment = "PROD"
    Purpose = "OS-User-List"
    Owner = "Shraddha"
    CreatedBy = "Shraddha"
    Product = "ALLPRODUCT"
  }
}

# Lifecycle Rule to delete objects older than 60 days
resource "aws_s3_bucket_lifecycle_configuration" "lifecycle" {
  bucket = aws_s3_bucket.os-user-list-s3-bucket.id

  rule {
    id     = "delete-old-objects"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects
    }
    expiration {
      days = 60
    }

  }
}