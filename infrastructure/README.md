# Nexora Infrastructure

Production-grade infrastructure for the Nexora platform, managing AWS cloud resources
(Terraform), configuration management (Ansible), container orchestration (Kubernetes/Helm),
and local development (Docker Compose).

---

## Repository Structure

```
infrastructure/
├── terraform/               # AWS infrastructure (IaC)
│   ├── main.tf              # Root module - wires all child modules
│   ├── variables.tf         # All input variable declarations
│   ├── outputs.tf           # Root outputs
│   ├── modules/
│   │   ├── network/         # VPC, subnets, NAT, VPN, flow logs, VPC endpoints
│   │   ├── compute/         # EC2 ASG, ALB, launch template, IAM
│   │   ├── database/        # RDS (MySQL/PostgreSQL), parameter groups, read replica
│   │   ├── security/        # Security groups, WAF, GuardDuty, CloudTrail, Config
│   │   ├── storage/         # S3 buckets with lifecycle, encryption, versioning
│   │   ├── monitoring/      # CloudWatch dashboards, alarms, SNS, X-Ray
│   │   ├── secrets/         # AWS Secrets Manager - app + DB credentials
│   │   └── backup/          # AWS Backup - daily/weekly/monthly plans
│   └── environments/
│       ├── dev/             # Dev-specific tfvars
│       ├── staging/         # Staging-specific tfvars
│       └── prod/            # Prod-specific tfvars
│
├── kubernetes/              # Helm chart (also usable with Kustomize post-render)
│   ├── Chart.yaml           # Helm chart manifest
│   ├── values.schema.json   # Helm values validation schema
│   ├── templates/           # Helm-rendered Kubernetes manifests
│   ├── base/                # Raw manifests (also used by Kustomize)
│   └── environments/
│       ├── dev/values.yaml
│       ├── staging/values.yaml
│       └── prod/values.yaml
│
├── ansible/                 # Server configuration management
│   ├── ansible.cfg
│   ├── inventory/
│   ├── playbooks/
│   └── roles/
│       ├── common/          # Base OS hardening, packages, firewall, fail2ban
│       ├── webserver/       # Nginx with security headers and rate limiting
│       └── database/        # MariaDB with secure root setup
│
├── docker/                  # Dockerfiles and service configs
│   ├── frontend/Dockerfile  # Multi-stage React (Parcel) → nginx; builds ../../web-frontend
│   └── nginx/               # Reverse proxy gateway
│                             # (the backend image builds directly from ../../code/Dockerfile,
│                             #  see the `backend` service context in docker-compose.yml)
│
├── docker-compose.yml           # Production-ready compose
├── docker-compose.override.yml  # Local dev overrides (auto-applied)
├── docker-compose.prod.yml      # Production resource constraints
└── .env.example                 # Environment variable template
```

---

## Docker / Local Development

The stack is three containers: `nginx` (gateway), `frontend` (the React SPA
in `web-frontend/`), and `backend` (the Python/FastAPI clinical prediction
API in `code/`). The backend is self-contained - it persists accounts and
patient data to SQLite and stores models/artifacts on local volumes, so
there's no separate database or cache service to run.

### Prerequisites

- Docker ≥ 24 and Docker Compose v2
- Copy `.env.example` → `.env` and fill in values

### Start all services

```bash
# First time - copy and configure env
cp .env.example .env

# Start dev stack (auto-applies docker-compose.override.yml)
docker compose up -d

# Tail logs
docker compose logs -f backend

# Stop everything
docker compose down
```

### Local service URLs

| Service          | URL                        |
| ---------------- | -------------------------- |
| App (via nginx)  | http://localhost:8080      |
| Backend direct   | http://localhost:8000      |
| Backend API docs | http://localhost:8000/docs |
| Frontend direct  | http://localhost:3000      |

### Production deployment

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Build images

```bash
docker compose build
# Or with a specific version tag:
APP_VERSION=1.2.3 docker compose build
```

---

## Kubernetes / Helm

### Prerequisites

- `helm` ≥ 3.12
- `kubectl` configured for target cluster

### Deploy with Helm

```bash
# Dev
helm upgrade --install nexora ./kubernetes \
  -f kubernetes/environments/dev/values.yaml \
  --namespace nexora --create-namespace

# Production
helm upgrade --install nexora ./kubernetes \
  -f kubernetes/environments/prod/values.yaml \
  --namespace nexora --create-namespace \
  --atomic --timeout 5m
```

### Render then apply with Kustomize

```bash
helm template nexora ./kubernetes \
  -f kubernetes/environments/dev/values.yaml \
  --output-dir kubernetes/rendered/dev

kubectl apply -k kubernetes/rendered/dev
```

---

## Terraform

### Prerequisites

- Terraform ≥ 1.5
- AWS credentials configured (`aws configure` or env vars)
- An S3 bucket + DynamoDB table for remote state (see `backend-s3.tf.example`)

### Usage

```bash
cd terraform

# 1. Configure backend (copy and edit one of the examples)
cp backend-s3.tf.example backend.tf   # or backend-local.tf.example

# 2. Initialize
terraform init

# 3. Plan for a specific environment
terraform plan -var-file=environments/dev/terraform.tfvars

# 4. Apply
terraform apply -var-file=environments/dev/terraform.tfvars

# 5. Sensitive vars via env (NEVER hardcode passwords)
export TF_VAR_db_password="your-secure-password-here"
export TF_VAR_jwt_secret="your-jwt-secret-here"
```

### Security note

Never commit `terraform.tfvars` files containing real passwords. Use:

- `TF_VAR_*` environment variables, or
- AWS Secrets Manager integration, or
- A secrets management tool like Vault

---

## Ansible

### Prerequisites

- `ansible` ≥ 2.14
- Python 3 with `boto3`, `PyMySQL`
- SSH access to target hosts

### Setup

```bash
cd ansible

# Copy and populate the inventory
cp inventory/hosts.example.yml inventory/hosts.yml

# Copy and encrypt vault secrets
cp group_vars/all/vault.example.yml group_vars/all/vault.yml
ansible-vault encrypt group_vars/all/vault.yml

# Configure vault password (choose one approach):
# Option A: file
echo "your-vault-password" > .vault_pass && chmod 600 .vault_pass
# Then uncomment vault_password_file in ansible.cfg

# Option B: environment variable
export ANSIBLE_VAULT_PASSWORD_FILE=.vault_pass

# Option C: prompt
# ansible-playbook playbooks/main.yml --ask-vault-pass
```

### Run playbooks

```bash
# Full provision
ansible-playbook playbooks/main.yml

# Dry run (check mode)
ansible-playbook playbooks/main.yml --check

# Specific host group
ansible-playbook playbooks/main.yml --limit webservers

# Specific tags
ansible-playbook playbooks/main.yml --tags "nginx,security"
```

---

## Security Considerations

- **Secrets**: Never commit `.env`, `vault.yml`, or `terraform.tfvars` with real values
- **TLS**: All production traffic enforced via HTTPS (HTTP→HTTPS redirect)
- **Encryption**: All RDS, EBS, and S3 storage encrypted with KMS
- **Network**: Database subnets are isolated (`internal: true` in Docker, private subnets in AWS)
- **IMDSv2**: EC2 instances enforce IMDSv2 only (no v1 SSRF vulnerability)
- **Non-root containers**: All Docker images run as non-root users
- **Security headers**: X-Frame-Options, CSP, X-Content-Type-Options on all nginx configs

---

## Bug Fixes Applied (v1.0.0 -> v1.1.0)

| Area       | Fix                                                                                  |
| ---------- | ------------------------------------------------------------------------------------ |
| Terraform  | Removed duplicate `app_name` arg in network module                                   |
| Terraform  | Fixed backup module KMS arg (`kms_key_id` → `kms_key_arn`)                           |
| Terraform  | Fixed backup schedule/retention variable name mismatches                             |
| Terraform  | Fixed `ebs_volume_ids`/`s3_bucket_arn` → `ebs_volume_arns`/`s3_bucket_arns`          |
| Terraform  | Added missing `ssl_certificate_arn` and `enable_vpc_endpoints` root variables        |
| Terraform  | Removed duplicate target group attachment (ASG + standalone)                         |
| Terraform  | Updated deprecated TLS policy to `ELBSecurityPolicy-TLS13-1-2-2021-06`               |
| Terraform  | Removed `timestamp()` from static snapshot identifier (perpetual drift)              |
| Terraform  | Fixed `log_retention_days * 2` producing invalid CloudWatch retention value          |
| Terraform  | Added `depends_on` to S3 bucket policy (public access block must apply first)        |
| Terraform  | Added `required_providers` block to compute module for `random` provider             |
| Kubernetes | Fixed all `{ { } }` Helm delimiter spacing across every template                     |
| Kubernetes | Fixed `backend-deployment.yaml` values key (`backend.` → `code.`)                    |
| Kubernetes | Fixed `backend-service.yaml` selector to match renamed deployment                    |
| Kubernetes | Fixed ingress `.Values.backend.servicePort` → `.Values.code.servicePort`             |
| Kubernetes | Fixed MySQL liveness/readiness probes (env vars don't expand in exec list form)      |
| Kubernetes | Updated Redis image `6.2` → `7-alpine` in all environment values                     |
| Kubernetes | Added missing `Chart.yaml` and `templates/` directory                                |
| Kubernetes | Added `values.schema.json` for Helm input validation                                 |
| Ansible    | Made `vault_password_file` conditional - hard ref broke all runs                     |
| Ansible    | Added `login_unix_socket` to all MySQL tasks (fresh install has no TCP auth)         |
| Ansible    | Fixed self-referencing `app_name` variable in `webserver/vars/main.yml`              |
| Ansible    | Added security headers, `server_tokens off`, rate limiting to nginx template         |
| Ansible    | Added nginx config validation (`nginx -t`) before reload                             |
| Ansible    | Added `Reload Nginx` handler alongside restart                                       |
| Ansible    | Fixed `yum update_only: yes` - now properly runs full update                         |
| Ansible    | Added fail2ban, chrony, sysctl hardening to common role                              |
| Ansible    | Added anonymous user removal, test DB removal, remote root lockout                   |
| Docker     | Added multi-stage `Dockerfile` for backend (Node.js, non-root, dumb-init)            |
| Docker     | Added multi-stage `Dockerfile` for frontend (React → nginx)                          |
| Docker     | Added nginx reverse proxy `Dockerfile` with rate limiting                            |
| Docker     | Added `docker-compose.yml`, `docker-compose.override.yml`, `docker-compose.prod.yml` |
| Docker     | Added MySQL custom config, init SQL, Redis config                                    |
| Docker     | Added `.env.example`, `.dockerignore`                                                |

## Bug Fixes Applied (v1.1.0 -> v1.2.0)

Everything above this table was built (and previously fixed) against a
generic **Node.js + MySQL + Redis** application template. The real Nexora
app is **Python/FastAPI + React**, persists to **SQLite** (not MySQL), and
has no cache layer - so none of that infrastructure actually matched the
application in this repository. This pass re-aligned it:

| Area       | Fix                                                                                                                                                                                                       |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Docker     | Backend now builds the real `code/Dockerfile` (Python/FastAPI) instead of a fictional Node.js image                                                                                                       |
| Docker     | Removed MySQL and Redis services/configs entirely - unused by the real app                                                                                                                                |
| Docker     | Fixed frontend build output path (`/app/build` → `/app/dist`, matching Parcel's real default)                                                                                                             |
| Docker     | Fixed frontend build-arg name (`REACT_APP_API_URL` → `REACT_APP_API_BASE_URL`, matching the actual frontend code)                                                                                         |
| Docker     | Removed a runtime env-injection entrypoint that could never work (Parcel inlines env vars at build time, not runtime)                                                                                     |
| Docker     | Fixed gateway nginx: wrong backend port (3000 → 8000) and a missing trailing slash on `proxy_pass` that forwarded `/api/*` to the backend unchanged, 404ing every request                                 |
| Docker     | Reduced prod backend to 1 replica - the app writes to SQLite on a shared volume, so multiple replicas risk "database is locked"                                                                           |
| Kubernetes | Fixed broken Helm delimiters: `{ { .Values.x } }` (with stray spaces) isn't valid template syntax - found and fixed in 50 places across every template                                                    |
| Kubernetes | Renamed `.Values.code.*` → `.Values.backend.*` throughout (chart, both `base/` and `templates/`, all environment values files, `values.schema.json`)                                                      |
| Kubernetes | Removed MySQL StatefulSet and Redis Deployment - unused by the real app; updated `kustomization.yaml`, configmap, and secrets accordingly                                                                 |
| Kubernetes | Fixed backend container port (3000 → 8000) and env vars (removed `DATABASE_URL`/`NODE_ENV`, added the real `AUDIT_DB_PATH`/`APP_DB_PATH`/`JWT_SECRET_KEY`/etc.)                                           |
| Kubernetes | Fixed ingress: added `rewrite-target` + capture-group path so `/api/*` is stripped before reaching the backend (same class of bug as the Docker nginx fix)                                                |
| Kubernetes | Removed a frontend runtime env var that had no effect on the static build (same issue as the Docker entrypoint fix)                                                                                       |
| Kubernetes | Verified all 35 distinct `.Values.*` paths referenced across every template resolve correctly against all four values files                                                                               |
| Terraform  | Fixed `module.backup.backup_iam_role_arn` - the module's real output is named `backup_role_arn`; this would fail `terraform plan`                                                                         |
| Terraform  | Fixed a missing required argument: the `database` module block omitted `app_name = var.app_name` (every other module passes it)                                                                           |
| Terraform  | Fixed a security-group egress rule that fell back to port 3000 (Node.js) instead of 8000 (the real backend)                                                                                               |
| Terraform  | Flagged (via comment) that `modules/compute/user_data.sh` provisions the instance but never actually deploys the application containers                                                                   |
| Ansible    | Fixed the same missing-trailing-slash `proxy_pass` bug a third time, in `roles/webserver/templates/nginx.conf.j2`                                                                                         |
| Ansible    | Fixed `app_port: 3000` → `8000` in `roles/webserver/vars/main.yml`                                                                                                                                        |
| Ansible    | Fixed an OS-family mismatch: `ansible.cfg` and `hosts.example.yml` assumed an Ubuntu user (`ubuntu`), but every task uses the `yum` module (Amazon Linux/RedHat family only) - standardized on `ec2-user` |
| Ansible    | Removed `nodejs`/`npm` from the webserver role's packages - not needed for nginx reverse-proxying + static file serving                                                                                   |

Full details in the repository root `CHANGES.md`.
