# Infrastructure Documentation

This document provides comprehensive information about the infrastructure setup and management for the Hospital Readmission Risk Prediction System.

## Table of Contents

1. [Infrastructure Overview](#infrastructure-overview)
2. [Cloud Infrastructure](#cloud-infrastructure)
3. [Kubernetes Setup](#kubernetes-setup)
4. [Database Infrastructure](#database-infrastructure)
5. [Networking](#networking)
6. [Security](#security)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Disaster Recovery](#disaster-recovery)
9. [Infrastructure as Code](#infrastructure-as-code)

## Infrastructure Overview

The Hospital Readmission Risk Prediction System is designed to be deployed on a modern cloud-native infrastructure that ensures scalability, reliability, and security. The infrastructure is managed using Infrastructure as Code (IaC) principles with Terraform.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Cloud Provider (AWS/Azure/GCP)                 │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     Virtual Network / VPC                        │    │
│  │                                                                 │    │
│  │  ┌───────────────┐   ┌────────────────┐   ┌────────────────┐    │    │
│  │  │ Public Subnet │   │ Private Subnet │   │ Database Subnet│    │    │
│  │  │               │   │                │   │                │    │    │
│  │  │  ┌─────────┐  │   │  ┌──────────┐  │   │  ┌──────────┐  │    │    │
│  │  │  │ Load    │  │   │  │Kubernetes│  │   │  │ Database │  │    │    │
│  │  │  │ Balancer│  │   │  │ Cluster  │  │   │  │ Cluster  │  │    │    │
│  │  │  └────┬────┘  │   │  └─────┬────┘  │   │  └──────────┘  │    │    │
│  │  │       │       │   │        │       │   │                │    │    │
│  │  └───────┼───────┘   └────────┼───────┘   └────────────────┘    │    │
│  │          │                    │                                 │    │
│  └──────────┼────────────────────┼─────────────────────────────────┘    │
│             │                    │                                      │
│  ┌──────────▼────────────────────▼─────────────────────────────────┐    │
│  │                    Internet Gateway                              │    │
│  └────────────────────────────────────────────────────────────────┬┘    │
│                                                                   │      │
└───────────────────────────────────────────────────────────────────┼──────┘
                                                                    │
                                                                    ▼
                                                               Internet
```

### Key Components

1. **Compute Infrastructure**:
   - Kubernetes cluster for container orchestration
   - Autoscaling node groups
   - GPU nodes for model training and inference

2. **Storage Infrastructure**:
   - Database cluster for patient data and model metadata
   - Object storage for model artifacts
   - Persistent volumes for application data

3. **Networking Infrastructure**:
   - Virtual private cloud (VPC)
   - Subnets (public, private, database)
   - Load balancers
   - Network security groups

4. **Security Infrastructure**:
   - Identity and access management
   - Encryption (at rest and in transit)
   - Security monitoring and compliance

5. **Monitoring Infrastructure**:
   - Metrics collection and visualization
   - Log aggregation
   - Alerting and notification

## Cloud Infrastructure

The system can be deployed on major cloud providers (AWS, Azure, GCP) with provider-specific configurations.

### AWS Infrastructure

#### Core Services

| Service | Purpose |
|---------|---------|
| EKS | Kubernetes cluster for container orchestration |
| RDS | PostgreSQL database for application data |
| S3 | Object storage for model artifacts |
| ECR | Container registry for application images |
| CloudWatch | Monitoring and logging |
| IAM | Identity and access management |
| VPC | Networking and security |
| Route53 | DNS management |
| ACM | TLS certificate management |

#### AWS Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                  AWS                                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                              VPC                                 │    │
│  │                                                                 │    │
│  │  ┌───────────────┐   ┌────────────────┐   ┌────────────────┐    │    │
│  │  │ Public Subnet │   │ Private Subnet │   │ Database Subnet│    │    │
│  │  │               │   │                │   │                │    │    │
│  │  │  ┌─────────┐  │   │  ┌──────────┐  │   │  ┌──────────┐  │    │    │
│  │  │  │ ALB     │  │   │  │ EKS      │  │   │  │ RDS      │  │    │    │
│  │  │  │         │  │   │  │ Cluster  │  │   │  │ Cluster  │  │    │    │
│  │  │  └────┬────┘  │   │  └─────┬────┘  │   │  └──────────┘  │    │    │
│  │  │       │       │   │        │       │   │                │    │    │
│  │  └───────┼───────┘   └────────┼───────┘   └────────────────┘    │    │
│  │          │                    │                                 │    │
│  └──────────┼────────────────────┼─────────────────────────────────┘    │
│             │                    │                                      │
│  ┌──────────▼──┐  ┌──────────────▼─┐  ┌────────────┐  ┌─────────────┐   │
│  │ Route53     │  │ Internet       │  │ S3 Buckets │  │ CloudWatch  │   │
│  │             │  │ Gateway        │  │            │  │             │   │
│  └─────────────┘  └────────────────┘  └────────────┘  └─────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Azure Infrastructure

#### Core Services

| Service | Purpose |
|---------|---------|
| AKS | Kubernetes cluster for container orchestration |
| Azure SQL | PostgreSQL database for application data |
| Blob Storage | Object storage for model artifacts |
| Container Registry | Container registry for application images |
| Monitor | Monitoring and logging |
| Active Directory | Identity and access management |
| Virtual Network | Networking and security |
| DNS | DNS management |
| Key Vault | Secret management |

### GCP Infrastructure

#### Core Services

| Service | Purpose |
|---------|---------|
| GKE | Kubernetes cluster for container orchestration |
| Cloud SQL | PostgreSQL database for application data |
| Cloud Storage | Object storage for model artifacts |
| Container Registry | Container registry for application images |
| Cloud Monitoring | Monitoring and logging |
| IAM | Identity and access management |
| VPC | Networking and security |
| Cloud DNS | DNS management |
| Secret Manager | Secret management |

## Kubernetes Setup

The system is deployed on Kubernetes for container orchestration, providing scalability, resilience, and portability.

### Cluster Configuration

#### Production Cluster Specifications

| Component | Specification |
|-----------|---------------|
| Control Plane | Managed by cloud provider |
| Node Pools | 3 node pools (general, compute, GPU) |
| General Nodes | 4+ nodes, 8 vCPU, 32GB RAM |
| Compute Nodes | 2+ nodes, 16 vCPU, 64GB RAM |
| GPU Nodes | 2+ nodes, 8 vCPU, 32GB RAM, NVIDIA A100 |
| Autoscaling | Enabled, min 2 nodes, max 10 nodes per pool |
| Kubernetes Version | 1.25+ |

#### Namespace Structure

| Namespace | Purpose |
|-----------|---------|
| readmission-system | Core application components |
| readmission-monitoring | Monitoring and logging |
| readmission-database | Database proxies and tools |
| cert-manager | TLS certificate management |
| ingress-nginx | Ingress controller |

### Resource Management

#### Resource Requests and Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: readmission-api
  namespace: readmission-system
spec:
  containers:
  - name: api
    image: ghcr.io/health-ai/readmission-api:2.3.0
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
  - name: model-server
    image: ghcr.io/health-ai/readmission-model:2.3.0
    resources:
      requests:
        memory: "4Gi"
        cpu: "1000m"
        nvidia.com/gpu: 1
      limits:
        memory: "8Gi"
        cpu: "2000m"
        nvidia.com/gpu: 1
```

#### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: readmission-api
  namespace: readmission-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: readmission-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deployment Configuration

#### Deployment Strategy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: readmission-api
  namespace: readmission-system
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: readmission-api
  template:
    metadata:
      labels:
        app: readmission-api
    spec:
      containers:
      - name: api
        image: ghcr.io/health-ai/readmission-api:2.3.0
        # ...
```

## Database Infrastructure

The system uses a PostgreSQL database for storing patient data, model metadata, and application state.

### Database Architecture

#### High-Availability Setup

```
┌─────────────────────────────────────────────────────────────┐
│                   Database Cluster                           │
│                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐  │
│  │  Primary    │      │  Replica 1  │      │  Replica 2  │  │
│  │  Node       │◄────►│             │◄────►│             │  │
│  │             │      │             │      │             │  │
│  └─────────────┘      └─────────────┘      └─────────────┘  │
│         ▲                                                   │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          │
┌─────────┼───────────────────────────────────────────────────┐
│         │           Connection Pooling                       │
│  ┌──────▼──────┐    ┌─────────────┐     ┌─────────────┐     │
│  │  PgBouncer  │    │  PgBouncer  │     │  PgBouncer  │     │
│  │  Primary    │    │  Replica    │     │  Replica    │     │
│  └─────────────┘    └─────────────┘     └─────────────┘     │
│         ▲                 ▲                   ▲             │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
┌─────────┼─────────────────┼───────────────────┼─────────────┐
│         │                 │                   │             │
│  ┌──────▼──────┐    ┌─────▼───────┐     ┌─────▼───────┐     │
│  │ Application │    │ Application │     │ Application │     │
│  │ Pods        │    │ Pods        │     │ Pods        │     │
│  └─────────────┘    └─────────────┘     └─────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Database Specifications

#### Production Database

| Component | Specification |
|-----------|---------------|
| Database Type | PostgreSQL 14+ |
| Instance Size | 8 vCPU, 32GB RAM |
| Storage | 1TB SSD with auto-scaling |
| Read Replicas | 2 |
| Backup | Automated daily backups, 30-day retention |
| Point-in-Time Recovery | Enabled, 7-day window |
| Encryption | Enabled for data at rest |
| Connection Pooling | PgBouncer |

#### Database Schema

The database uses a schema optimized for clinical data and model metadata:

```sql
-- Patient data schema
CREATE TABLE patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    demographics JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Admission data schema
CREATE TABLE admissions (
    admission_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50) REFERENCES patients(patient_id),
    admission_date TIMESTAMP WITH TIME ZONE NOT NULL,
    discharge_date TIMESTAMP WITH TIME ZONE,
    primary_diagnosis VARCHAR(20),
    diagnoses JSONB,
    procedures JSONB,
    medications JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prediction data schema
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(50) REFERENCES patients(patient_id),
    admission_id VARCHAR(50) REFERENCES admissions(admission_id),
    readmission_risk FLOAT NOT NULL,
    confidence_interval FLOAT[2],
    risk_factors JSONB,
    model_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model metadata schema
CREATE TABLE model_versions (
    model_version VARCHAR(20) PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    training_date TIMESTAMP WITH TIME ZONE NOT NULL,
    performance_metrics JSONB NOT NULL,
    fairness_metrics JSONB,
    active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Database Maintenance

#### Routine Maintenance

| Task | Frequency | Description |
|------|-----------|-------------|
| Vacuum | Weekly | Reclaim storage and update statistics |
| Reindex | Monthly | Rebuild indexes to improve performance |
| Version Upgrade | Yearly | Upgrade to newer PostgreSQL version |

#### Monitoring Queries

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('readmission'));

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Check index usage
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Networking

The system uses a secure networking architecture to protect patient data and ensure reliable communication.

### Network Architecture

#### VPC Configuration

| Component | CIDR Block | Purpose |
|-----------|------------|---------|
| VPC | 10.0.0.0/16 | Main network |
| Public Subnet 1 | 10.0.1.0/24 | Load balancers, NAT gateways |
| Public Subnet 2 | 10.0.2.0/24 | Load balancers, NAT gateways |
| Private Subnet 1 | 10.0.10.0/24 | Kubernetes nodes |
| Private Subnet 2 | 10.0.11.0/24 | Kubernetes nodes |
| Database Subnet 1 | 10.0.20.0/24 | Database instances |
| Database Subnet 2 | 10.0.21.0/24 | Database instances |

### Ingress Configuration

#### Ingress Controller

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: readmission-ingress
  namespace: readmission-system
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
spec:
  tls:
  - hosts:
    - api.readmission-risk.org
    - ui.readmission-risk.org
    secretName: readmission-tls
  rules:
  - host: api.readmission-risk.org
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: readmission-api
            port:
              number: 8000
  - host: ui.readmission-risk.org
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: readmission-ui
            port:
              number: 80
```

### Network Policies

#### Default Deny Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: readmission-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

#### API Server Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-server-policy
  namespace: readmission-system
spec:
  podSelector:
    matchLabels:
      app: readmission-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: readmission-model
    ports:
    - protocol: TCP
      port: 8001
  - to:
    - namespaceSelector:
        matchLabels:
          name: readmission-database
    ports:
    - protocol: TCP
      port: 5432
```

## Security

The system implements comprehensive security measures to protect patient data and ensure regulatory compliance.

### Identity and Access Management

#### Role-Based Access Control

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: readmission-system
  name: readmission-api-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: readmission-api-rolebinding
  namespace: readmission-system
subjects:
- kind: ServiceAccount
  name: readmission-api
  namespace: readmission-system
roleRef:
  kind: Role
  name: readmission-api-role
  apiGroup: rbac.authorization.k8s.io
```

### Encryption

#### Data Encryption

| Data Type | Encryption Method |
|-----------|-------------------|
| Data at Rest | AES-256 |
| Data in Transit | TLS 1.3 |
| Database | Transparent Data Encryption |
| Secrets | KMS-managed encryption |

#### TLS Configuration

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: readmission-tls
  namespace: readmission-system
spec:
  secretName: readmission-tls
  duration: 2160h # 90 days
  renewBefore: 360h # 15 days
  subject:
    organizations:
      - Health AI
  isCA: false
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
    - server auth
    - client auth
  dnsNames:
    - api.readmission-risk.org
    - ui.readmission-risk.org
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
```

### Security Scanning

#### Container Scanning

| Tool | Purpose | Frequency |
|------|---------|-----------|
| Trivy | Vulnerability scanning | On every build |
| Clair | Container image scanning | Daily |
| Anchore | Policy compliance | Weekly |

#### Code Scanning

| Tool | Purpose | Frequency |
|------|---------|-----------|
| SonarQube | Code quality and security | On every PR |
| Bandit | Python security linting | On every build |
| OWASP Dependency Check | Dependency vulnerabilities | Daily |

### Compliance Controls

#### HIPAA Controls

| Control | Implementation |
|---------|----------------|
| Access Control | RBAC, MFA, least privilege |
| Audit Controls | Comprehensive audit logging |
| Integrity | Checksums, signatures, immutable infrastructure |
| Person/Entity Authentication | OAuth2, OIDC, MFA |
| Transmission Security | TLS, VPN, network policies |

## Monitoring and Logging

The system implements comprehensive monitoring and logging to ensure reliability and facilitate troubleshooting.

### Metrics Monitoring

#### Prometheus Configuration

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: readmission-api
  namespace: readmission-monitoring
spec:
  selector:
    matchLabels:
      app: readmission-api
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
  namespaceSelector:
    matchNames:
    - readmission-system
```

#### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| readmission_api_requests_total | Total number of API requests | N/A |
| readmission_api_request_duration_seconds | API request duration | p95 > 1s |
| readmission_model_prediction_duration_seconds | Model prediction time | p95 > 2s |
| readmission_model_prediction_errors_total | Model prediction errors | > 1% error rate |
| readmission_database_query_duration_seconds | Database query duration | p95 > 500ms |

### Log Management

#### Logging Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Pods                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ API Server  │  │ Model Server│  │ UI Server   │          │
│  │ Logs        │  │ Logs        │  │ Logs        │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼───────────────┼───────────────┼──────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Fluent Bit DaemonSet                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Fluent Bit  │  │ Fluent Bit  │  │ Fluent Bit  │          │
│  │ Pod 1       │  │ Pod 2       │  │ Pod 3       │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼───────────────┼───────────────┼──────────────────┘
          │               │               │
          └───────────────┼───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Elasticsearch Cluster                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Elasticsearch│  │Elasticsearch│  │Elasticsearch│          │
│  │ Node 1      │  │ Node 2      │  │ Node 3      │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼───────────────┼───────────────┼──────────────────┘
          │               │               │
          └───────────────┼───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kibana Dashboard                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │                                                     │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### Log Format

```json
{
  "timestamp": "2025-04-25T10:30:45.123Z",
  "level": "INFO",
  "service": "readmission-api",
  "trace_id": "abcdef123456",
  "span_id": "fedcba654321",
  "user_id": "doctor-smith",
  "patient_id": "12345",
  "message": "Prediction request processed successfully",
  "details": {
    "prediction": 0.72,
    "model_version": "2.3.0",
    "duration_ms": 150
  }
}
```

### Alerting

#### Alert Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: readmission-alerts
  namespace: readmission-monitoring
spec:
  groups:
  - name: readmission
    rules:
    - alert: HighErrorRate
      expr: sum(rate(readmission_api_request_errors_total[5m])) / sum(rate(readmission_api_requests_total[5m])) > 0.01
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate on API requests"
        description: "Error rate is above 1% for more than 5 minutes"
    - alert: SlowAPIResponse
      expr: histogram_quantile(0.95, sum(rate(readmission_api_request_duration_seconds_bucket[5m])) by (le)) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Slow API response time"
        description: "95th percentile of API response time is above 1 second for more than 5 minutes"
```

## Disaster Recovery

The system implements comprehensive disaster recovery procedures to ensure business continuity.

### Backup Strategy

#### Backup Components

| Component | Backup Method | Frequency | Retention |
|-----------|---------------|-----------|-----------|
| Database | Automated snapshots | Daily | 30 days |
| Database | Transaction logs | Continuous | 7 days |
| Model Artifacts | S3 replication | Continuous | Indefinite |
| Configuration | Git repository | On change | Indefinite |
| Kubernetes State | Velero backups | Daily | 14 days |

### Recovery Procedures

#### Database Recovery

```bash
# Restore from latest snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier readmission-db-restored \
  --db-snapshot-identifier readmission-db-snapshot-20250424

# Point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier readmission-db \
  --target-db-instance-identifier readmission-db-restored \
  --restore-time 2025-04-24T23:45:00Z
```

#### Kubernetes Recovery

```bash
# Restore entire cluster
velero restore create --from-backup readmission-backup-20250424

# Restore specific namespace
velero restore create --from-backup readmission-backup-20250424 --include-namespaces readmission-system
```

### Disaster Recovery Testing

| Test Type | Frequency | Description |
|-----------|-----------|-------------|
| Database Recovery | Quarterly | Restore database to test environment |
| Full System Recovery | Bi-annually | Restore entire system to DR environment |
| Failover Testing | Quarterly | Test automatic failover capabilities |

## Infrastructure as Code

The system infrastructure is managed using Terraform for consistent, version-controlled deployments.

### Terraform Structure

```
infrastructure/
├── terraform/
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   ├── staging/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   └── prod/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── terraform.tfvars
│   ├── modules/
│   │   ├── network/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── kubernetes/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── database/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── storage/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── security/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── providers.tf
```

### Example Terraform Configuration

#### Network Module

```hcl
# modules/network/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
    Project     = "readmission-risk"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.environment}-public-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = "readmission-risk"
  }
}

resource "aws_subnet" "private" {
  count                   = length(var.private_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]

  tags = {
    Name        = "${var.environment}-private-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = "readmission-risk"
  }
}

resource "aws_subnet" "database" {
  count                   = length(var.database_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.database_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]

  tags = {
    Name        = "${var.environment}-database-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = "readmission-risk"
  }
}

# Additional resources: internet gateway, NAT gateway, route tables, etc.
```

#### Kubernetes Module

```hcl
# modules/kubernetes/main.tf
resource "aws_eks_cluster" "main" {
  name     = "${var.environment}-readmission-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
    security_group_ids      = [aws_security_group.eks_cluster.id]
  }

  encryption_config {
    resources = ["secrets"]
    provider {
      key_arn = var.kms_key_arn
    }
  }

  tags = {
    Environment = var.environment
    Project     = "readmission-risk"
  }
}

resource "aws_eks_node_group" "general" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.environment}-general"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.subnet_ids

  scaling_config {
    desired_size = var.general_node_desired_size
    min_size     = var.general_node_min_size
    max_size     = var.general_node_max_size
  }

  instance_types = var.general_node_instance_types

  tags = {
    Environment = var.environment
    Project     = "readmission-risk"
    NodeGroup   = "general"
  }
}

resource "aws_eks_node_group" "gpu" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.environment}-gpu"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.subnet_ids

  scaling_config {
    desired_size = var.gpu_node_desired_size
    min_size     = var.gpu_node_min_size
    max_size     = var.gpu_node_max_size
  }

  instance_types = var.gpu_node_instance_types

  tags = {
    Environment = var.environment
    Project     = "readmission-risk"
    NodeGroup   = "gpu"
  }
}

# Additional resources: IAM roles, security groups, etc.
```

### Deployment Workflow

```bash
# Initialize Terraform
cd infrastructure/terraform/environments/prod
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Destroy infrastructure (for cleanup)
terraform destroy
```
