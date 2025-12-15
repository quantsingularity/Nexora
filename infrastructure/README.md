# Nexora Infrastructure

**Complete Infrastructure as Code (IaC) for the Nexora Healthcare AI Platform**

This directory contains all infrastructure provisioning, configuration, and deployment automation for Nexora. The infrastructure follows security best practices, compliance requirements, and industry standards for healthcare applications.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Terraform Setup](#terraform-setup)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Ansible Configuration](#ansible-configuration)
- [CI/CD Workflows](#cicd-workflows)
- [Security & Secrets Management](#security--secrets-management)
- [Validation & Testing](#validation--testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

Install the following tools before proceeding:

```bash
# Terraform (v1.6.0 or later)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version

# kubectl (v1.28 or later)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client

# Helm (v3.12 or later) - optional but recommended
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version

# kustomize (v5.0 or later)
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
kustomize version

# Ansible (v2.15 or later)
pip3 install ansible ansible-lint
ansible --version

# Validation tools
pip3 install yamllint
# tflint
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
# tfsec
brew install tfsec  # or download from https://github.com/aquasecurity/tfsec/releases
# kubeval
wget https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz
tar xf kubeval-linux-amd64.tar.gz
sudo mv kubeval /usr/local/bin/
```

### Cloud Provider Access

- **AWS Account** with appropriate IAM permissions
- AWS CLI configured: `aws configure`
- S3 bucket for Terraform state (optional, local backend available)

### Kubernetes Cluster

- Existing Kubernetes cluster (EKS, GKE, AKS, or local minikube/kind)
- kubectl configured with cluster access: `kubectl cluster-info`

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to infrastructure directory
cd infrastructure

# Copy example configuration files
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
cp terraform/backend-local.tf.example terraform/backend-local.tf
cp kubernetes/base/app-secrets.example.yaml kubernetes/base/app-secrets.yaml
cp kubernetes/environments/dev/values.example.yaml kubernetes/environments/dev/values.yaml
cp ansible/inventory/hosts.example.yml ansible/inventory/hosts.yml
```

### 2. Configure Secrets

Edit the copied files and replace all `CHANGEME` values with actual configuration.

**IMPORTANT**: Never commit files containing real secrets to version control.

### 3. Validate Infrastructure

```bash
# Run all validations
make validate  # or see Validation & Testing section below
```

### 4. Deploy

```bash
# Terraform
cd terraform
terraform init
terraform plan
terraform apply

# Kubernetes
cd ../kubernetes
kubectl apply -k environments/dev/

# Ansible (if configuring VMs)
cd ../ansible
ansible-playbook -i inventory/hosts.yml playbooks/main.yml
```

## Directory Structure

```
infrastructure/
├── README.md                           # This file
├── .gitignore                          # Prevent secret leakage
├── AUDIT_ISSUES_CHECKLIST.md          # Security audit checklist
│
├── terraform/                          # Infrastructure provisioning
│   ├── main.tf                        # Main Terraform configuration
│   ├── variables.tf                   # Variable definitions
│   ├── outputs.tf                     # Output definitions
│   ├── terraform.tfvars.example       # Example variables (COPY THIS)
│   ├── backend-local.tf.example       # Local backend config
│   ├── backend-s3.tf.example          # S3 backend config
│   ├── .tflint.hcl                    # TFLint configuration
│   ├── .tfsec.yml                     # tfsec configuration
│   ├── modules/                       # Terraform modules
│   │   ├── network/                   # VPC, subnets, routing
│   │   ├── compute/                   # EC2, ASG, ALB
│   │   ├── database/                  # RDS configuration
│   │   ├── storage/                   # S3, EBS volumes
│   │   ├── security/                  # Security groups, WAF, GuardDuty
│   │   ├── monitoring/                # CloudWatch, SNS alerts
│   │   ├── secrets/                   # Secrets Manager integration
│   │   └── backup/                    # AWS Backup configuration
│   └── environments/                  # Per-environment configs
│       ├── dev/terraform.tfvars
│       ├── staging/terraform.tfvars
│       └── prod/terraform.tfvars
│
├── kubernetes/                         # Container orchestration
│   ├── base/                          # Base Kubernetes manifests
│   │   ├── kustomization.yaml         # Kustomize config
│   │   ├── namespace.yaml             # Namespace definition
│   │   ├── rbac.yaml                  # RBAC manifests
│   │   ├── app-configmap.yaml         # Application config
│   │   ├── app-secrets.yaml           # Secrets (DO NOT COMMIT)
│   │   ├── app-secrets.example.yaml   # Secret template
│   │   ├── backend-deployment.yaml    # Backend deployment
│   │   ├── backend-service.yaml       # Backend service
│   │   ├── frontend-deployment.yaml   # Frontend deployment
│   │   ├── frontend-service.yaml      # Frontend service
│   │   ├── database-statefulset.yaml  # Database stateful set
│   │   ├── database-service.yaml      # Database service
│   │   ├── redis-deployment.yaml      # Redis cache
│   │   ├── redis-service.yaml         # Redis service
│   │   ├── redis-pvc.yaml             # Redis persistent volume
│   │   └── ingress.yaml               # Ingress controller config
│   └── environments/                  # Environment overlays
│       ├── dev/values.example.yaml    # Dev config template
│       ├── staging/values.yaml
│       └── prod/values.yaml
│
├── ansible/                            # Configuration management
│   ├── ansible.cfg                    # Ansible configuration
│   ├── inventory/                     # Inventory files
│   │   ├── hosts.yml                  # Actual hosts (DO NOT COMMIT)
│   │   └── hosts.example.yml          # Example inventory
│   ├── playbooks/                     # Ansible playbooks
│   │   └── main.yml                   # Main playbook
│   ├── roles/                         # Ansible roles
│   │   ├── common/                    # Common tasks
│   │   ├── webserver/                 # Web server config
│   │   └── database/                  # Database config
│   └── group_vars/                    # Group variables
│       └── all/
│           └── vault.example.yml      # Vault template
│
└── cicd/                               # CI/CD workflows
    └── github-actions/                # GitHub Actions workflows
        ├── ci-cd.yml                  # Main CI/CD pipeline
        ├── deploy-infrastructure.yml  # Infrastructure deployment
        └── validate-infrastructure.yml # Validation workflow

```

## Terraform Setup

### Local Development (Recommended for Testing)

```bash
cd terraform

# 1. Copy backend configuration for local development
cp backend-local.tf.example backend-local.tf

# 2. Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values

# 3. Set sensitive variables via environment
export TF_VAR_db_password="YourSecurePassword123!"

# 4. Initialize Terraform (local backend)
terraform init

# 5. Validate configuration
terraform fmt -recursive
terraform validate

# 6. Plan infrastructure changes
terraform plan -out=plan.out

# 7. Review plan and apply
terraform show plan.out
terraform apply plan.out
```

### Production (S3 Backend)

```bash
cd terraform

# 1. Create S3 bucket and DynamoDB table for state management
aws s3 mb s3://your-terraform-state-bucket --region us-west-2
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-2

# 2. Copy and configure S3 backend
cp backend-s3.tf.example backend-s3.tf
nano backend-s3.tf  # Update bucket name and region

# 3. Remove local backend if present
rm -f backend-local.tf

# 4. Initialize with S3 backend
terraform init -reconfigure

# 5. Continue with plan and apply as above
```

### Terraform Validation Commands

```bash
# Format check (no changes)
terraform fmt -check -recursive

# Format and fix
terraform fmt -recursive

# Validate syntax
terraform init -backend=false
terraform validate

# Run TFLint
cd terraform
tflint --init
tflint --format compact

# Run tfsec security scan
tfsec . --format=default --soft-fail
```

## Kubernetes Deployment

### Setup Kubernetes Manifests

```bash
cd kubernetes

# 1. Copy secret template
cp base/app-secrets.example.yaml base/app-secrets.yaml

# 2. Edit secrets (base64 encode values)
echo -n "your-secret-value" | base64  # Get base64 encoded value
nano base/app-secrets.yaml  # Paste encoded values

# 3. Copy environment values
cp environments/dev/values.example.yaml environments/dev/values.yaml
nano environments/dev/values.yaml  # Edit configuration

# 4. Validate YAML syntax
yamllint base/
yamllint environments/dev/

# 5. Validate Kubernetes manifests
kubectl apply -k base/ --dry-run=client

# 6. Apply to cluster (dev environment)
kubectl apply -k environments/dev/

# 7. Verify deployment
kubectl get all -n nexora-dev
kubectl get pods -n nexora-dev
kubectl logs -f deployment/nexora-backend -n nexora-dev
```

### Using Kustomize

```bash
# Build and view rendered manifests
kustomize build kubernetes/base/

# Build specific environment
kustomize build kubernetes/environments/dev/

# Apply with kustomize
kubectl apply -k kubernetes/environments/dev/

# Delete deployment
kubectl delete -k kubernetes/environments/dev/
```

### Kubernetes Validation Commands

```bash
# YAML syntax
yamllint -f parsable kubernetes/

# Kubernetes schema validation (note: templates with {{ }} will fail)
find kubernetes/base -name "*.yaml" -exec kubeval --ignore-missing-schemas {} \;

# Dry-run apply
kubectl apply -k kubernetes/base/ --dry-run=client -o yaml

# Check resource quotas
kubectl describe resourcequotas -n nexora-dev
```

## Ansible Configuration

### Setup Ansible Inventory

```bash
cd ansible

# 1. Copy inventory template
cp inventory/hosts.example.yml inventory/hosts.yml
nano inventory/hosts.yml  # Add your server IPs

# 2. Create vault for secrets
ansible-vault create group_vars/all/vault.yml
# Add secrets in YAML format:
# vault_db_password: "SecurePassword123!"
# vault_db_root_password: "RootPassword123!"

# 3. Store vault password (add to .gitignore)
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass

# 4. Test connection
ansible all -m ping -i inventory/hosts.yml

# 5. Run playbook (check mode)
ansible-playbook -i inventory/hosts.yml playbooks/main.yml --check

# 6. Run playbook
ansible-playbook -i inventory/hosts.yml playbooks/main.yml

# 7. Run specific role
ansible-playbook -i inventory/hosts.yml playbooks/main.yml --tags database
```

### Ansible Validation Commands

```bash
# YAML syntax
yamllint ansible/

# Ansible-lint
ansible-lint playbooks/main.yml

# Syntax check
ansible-playbook playbooks/main.yml --syntax-check -i inventory/hosts.example.yml

# Dry-run
ansible-playbook -i inventory/hosts.yml playbooks/main.yml --check --diff

# List tasks
ansible-playbook -i inventory/hosts.yml playbooks/main.yml --list-tasks

# List hosts
ansible all -i inventory/hosts.yml --list-hosts
```

## CI/CD Workflows

### GitHub Actions Setup

1. **Configure Repository Secrets** (Settings → Secrets and variables → Actions):

```
AWS_ACCESS_KEY_ID: Your AWS access key
AWS_SECRET_ACCESS_KEY: Your AWS secret key
AWS_ROLE_ARN: IAM role ARN for deployment
TF_STATE_BUCKET: S3 bucket for Terraform state
TF_STATE_LOCK_TABLE: DynamoDB table name
KUBECONFIG: Base64-encoded kubeconfig file
SLACK_WEBHOOK_URL: (Optional) Slack webhook for notifications
```

2. **Available Workflows**:

- `ci-cd.yml`: Main CI/CD pipeline (test, build, deploy)
- `deploy-infrastructure.yml`: Terraform infrastructure deployment
- `validate-infrastructure.yml`: Validation checks (runs on PR)

3. **Trigger Workflows**:

```bash
# Automatic triggers
git push origin main  # Triggers CI/CD
git push origin develop  # Triggers validation

# Manual trigger (workflow_dispatch)
# Go to Actions tab → Select workflow → Run workflow
```

### Local CI Testing

Test GitHub Actions locally using `act`:

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test workflow locally
cd infrastructure
act -W cicd/github-actions/validate-infrastructure.yml

# Test specific job
act -W cicd/github-actions/validate-infrastructure.yml -j terraform-validate
```

## Security & Secrets Management

### Best Practices

1. **Never commit secrets to git**:
   - Use `.gitignore` to exclude secret files
   - Use `.example` templates for documentation

2. **Use secret management tools**:
   - AWS Secrets Manager (Terraform module included)
   - Kubernetes Secrets with encryption at rest
   - Ansible Vault for configuration management
   - External Secrets Operator for Kubernetes

3. **Environment variables for sensitive data**:

```bash
# Terraform
export TF_VAR_db_password="SecurePassword"
export TF_VAR_db_username="admin"

# Kubernetes (create secrets imperatively)
kubectl create secret generic nexora-secrets \
  --from-literal=db-password="SecurePassword" \
  --namespace=nexora-dev

# Ansible
export ANSIBLE_VAULT_PASSWORD_FILE=.vault_pass
```

### Rotating Secrets

```bash
# Terraform: Update in Secrets Manager
aws secretsmanager update-secret \
  --secret-id nexora/dev/db-password \
  --secret-string "NewPassword"

# Kubernetes: Update and restart pods
kubectl create secret generic nexora-secrets \
  --from-literal=db-password="NewPassword" \
  --namespace=nexora-dev --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/nexora-backend -n nexora-dev

# Ansible: Update vault
ansible-vault edit group_vars/all/vault.yml
```

## Validation & Testing

### Comprehensive Validation Script

```bash
#!/bin/bash
# Run all validation checks

set -e

echo "=== Terraform Validation ==="
cd terraform
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
tflint --init && tflint
tfsec . --soft-fail

echo "=== Kubernetes Validation ==="
cd ../kubernetes
yamllint base/
yamllint environments/
kubectl apply -k base/ --dry-run=client

echo "=== Ansible Validation ==="
cd ../ansible
yamllint .
ansible-lint playbooks/main.yml
ansible-playbook playbooks/main.yml --syntax-check -i inventory/hosts.example.yml

echo "=== All validations passed! ==="
```

Save as `validate-all.sh`, make executable: `chmod +x validate-all.sh`

### Pre-commit Hooks

Install pre-commit hooks to validate before commits:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml (see example in repo)
pre-commit install

# Run manually
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

**Terraform: Backend initialization fails**

```bash
# Solution: Use local backend for development
cp backend-local.tf.example backend-local.tf
rm -f backend-s3.tf
terraform init -reconfigure
```

**Kubernetes: Template syntax errors**

```bash
# Solution: Ensure no spaces in template delimiters
# Wrong: { { .Values.name } }
# Correct: {{ .Values.name }}
```

**Ansible: Variable not defined**

```bash
# Solution: Define in inventory or group_vars
# Add to inventory/hosts.yml under vars section
```

**CI/CD: Workflow syntax error**

```bash
# Validate workflow YAML
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci-cd.yml'))"
```

### Getting Help

- Check `AUDIT_ISSUES_CHECKLIST.md` for known issues
- Review validation logs in `validation_logs/` directory
- Consult official documentation:
  - [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
  - [Kubernetes Documentation](https://kubernetes.io/docs/)
  - [Ansible Documentation](https://docs.ansible.com/)

### Health Checks

```bash
# Terraform
terraform state list
terraform output

# Kubernetes
kubectl get all -n nexora-dev
kubectl describe pod <pod-name> -n nexora-dev
kubectl logs -f deployment/nexora-backend -n nexora-dev

# Ansible
ansible all -m ping -i inventory/hosts.yml
```

## Compliance & Security Features

- **Encryption**: At-rest and in-transit encryption for all data
- **Audit Logging**: CloudTrail, VPC Flow Logs, Kubernetes audit logs
- **Access Control**: RBAC for Kubernetes, IAM for AWS, privilege escalation for Ansible
- **Network Segmentation**: VPC, subnets, security groups, network policies
- **Monitoring**: CloudWatch, Prometheus, Grafana integration points
- **Backup & DR**: Automated backups with retention policies
- **Compliance**: SOC2, HIPAA, PCI-DSS compliance features enabled

## Contributing

Before submitting infrastructure changes:

1. Run all validation checks
2. Update documentation if adding new components
3. Test in dev environment first
4. Create PR with detailed change description

## License

See main repository LICENSE file.

---
