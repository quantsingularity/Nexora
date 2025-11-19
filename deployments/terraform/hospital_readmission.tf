module "ml_serving" {
  source  = "terraform-aws-modules/eks/aws"

  cluster_name = "readmission-cluster"
  node_groups = {
    model_serving = {
      desired_capacity = 5
      instance_types  = ["g4dn.xlarge"]
      gpu_required    = true
    }
  }

  enable_istio = true
  prometheus_enabled = true
}

resource "aws_s3_bucket" "feature_store" {
  bucket = "clinical-feature-store"
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
