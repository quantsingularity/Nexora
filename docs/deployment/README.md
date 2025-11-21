# Deployment Guide

This guide provides comprehensive instructions for deploying the Hospital Readmission Risk Prediction System in various environments, from development to production.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Local Deployment](#local-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration Management](#configuration-management)
7. [Database Setup](#database-setup)
8. [Security Considerations](#security-considerations)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Backup and Recovery](#backup-and-recovery)
11. [Troubleshooting](#troubleshooting)

## Deployment Overview

The Hospital Readmission Risk Prediction System can be deployed in several environments:

1. **Local Development**: For development and testing
2. **Staging Environment**: For integration testing and validation
3. **Production Environment**: For clinical use

The system uses containerization (Docker) and orchestration (Kubernetes) to ensure consistent deployment across environments.

## Prerequisites

### Hardware Requirements

| Environment | CPU       | RAM    | Storage | GPU         |
| ----------- | --------- | ------ | ------- | ----------- |
| Development | 4+ cores  | 16+ GB | 100+ GB | Optional    |
| Staging     | 8+ cores  | 32+ GB | 500+ GB | NVIDIA T4+  |
| Production  | 16+ cores | 64+ GB | 1+ TB   | NVIDIA A100 |

### Software Requirements

- Docker 20.10+
- Kubernetes 1.22+
- Helm 3.8+
- FHIR-compliant database
- NVIDIA GPU drivers (for GPU acceleration)
- CUDA 11.7+
- Python 3.10+

### Network Requirements

- Outbound internet access for package installation
- Internal network access to FHIR/EHR systems
- Load balancer for production deployments
- TLS certificates for secure communication

## Local Deployment

### Using Docker Compose

1. Clone the repository:

   ```bash
   git clone https://github.com/abrar2030/Nexora.git
   cd Nexora
   ```

2. Create a `.env` file:

   ```
   FHIR_SERVER_URL=https://fhir.example.org/R4
   FHIR_CLIENT_ID=client_id
   FHIR_CLIENT_SECRET=client_secret
   MODEL_REGISTRY_URL=https://mlflow.example.org
   DATABASE_URL=postgresql://user:password@localhost:5432/readmission
   ```

3. Start the services:

   ```bash
   docker-compose up -d
   ```

4. Verify deployment:
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/v1/health
   ```

### Using Make Commands

The project includes Make commands for common deployment tasks:

```bash
# Set up development environment
make setup

# Start development server
make dev-server

# Start clinician UI
make clinician-ui

# Run synthetic data generation
make synthetic-data

# Deploy with specific configuration
make deploy CONFIG=local
```

## Kubernetes Deployment

### Using Helm

1. Add the Helm repository:

   ```bash
   helm repo add readmission-risk https://charts.readmission-risk.org
   helm repo update
   ```

2. Create a values file (`values.yaml`):

   ```yaml
   global:
     environment: production
     registry: ghcr.io/health-ai

   fhir:
     serverUrl: https://fhir.example.org/R4
     clientId: client_id
     clientSecret: client_secret

   database:
     host: postgres.database.svc.cluster.local
     port: 5432
     name: readmission
     user: readmission_user

   modelServing:
     replicas: 3
     gpu:
       enabled: true
       count: 1

   clinicianUi:
     replicas: 2
     ingress:
       enabled: true
       host: readmission.example.org
   ```

3. Install the Helm chart:

   ```bash
   helm install readmission readmission-risk/readmission \
     --namespace readmission-system \
     --create-namespace \
     --values values.yaml
   ```

4. Verify the deployment:
   ```bash
   kubectl get pods -n readmission-system
   kubectl get services -n readmission-system
   ```

### Manual Kubernetes Deployment

For more control over the deployment, you can use the Kubernetes manifests directly:

1. Navigate to the deployment directory:

   ```bash
   cd deployments/kubernetes
   ```

2. Apply the manifests:
   ```bash
   kubectl apply -f namespace.yaml
   kubectl apply -f configmap.yaml
   kubectl apply -f secrets.yaml
   kubectl apply -f database.yaml
   kubectl apply -f model-serving.yaml
   kubectl apply -f clinician-ui.yaml
   kubectl apply -f ingress.yaml
   ```

## Cloud Deployment

### AWS Deployment

1. Set up infrastructure using Terraform:

   ```bash
   cd infrastructure/terraform/aws
   terraform init
   terraform apply
   ```

2. Configure AWS CLI:

   ```bash
   aws configure
   ```

3. Update kubeconfig:

   ```bash
   aws eks update-kubeconfig --name readmission-cluster --region us-west-2
   ```

4. Deploy using Helm:
   ```bash
   helm install readmission ./deployments/helm \
     --namespace readmission-system \
     --create-namespace \
     --values values-aws.yaml
   ```

### Azure Deployment

1. Set up infrastructure using Terraform:

   ```bash
   cd infrastructure/terraform/azure
   terraform init
   terraform apply
   ```

2. Configure Azure CLI:

   ```bash
   az login
   ```

3. Get AKS credentials:

   ```bash
   az aks get-credentials --resource-group readmission-rg --name readmission-aks
   ```

4. Deploy using Helm:
   ```bash
   helm install readmission ./deployments/helm \
     --namespace readmission-system \
     --create-namespace \
     --values values-azure.yaml
   ```

### GCP Deployment

1. Set up infrastructure using Terraform:

   ```bash
   cd infrastructure/terraform/gcp
   terraform init
   terraform apply
   ```

2. Configure gcloud CLI:

   ```bash
   gcloud auth login
   ```

3. Get GKE credentials:

   ```bash
   gcloud container clusters get-credentials readmission-cluster --zone us-central1-a
   ```

4. Deploy using Helm:
   ```bash
   helm install readmission ./deployments/helm \
     --namespace readmission-system \
     --create-namespace \
     --values values-gcp.yaml
   ```

## Configuration Management

### Configuration Files

The system uses a hierarchical configuration approach:

1. **Default Configuration**: `config/config.default.yaml`
2. **Environment Configuration**: `config/config.{env}.yaml`
3. **Local Configuration**: `config/config.local.yaml`
4. **Secret Configuration**: Stored in Kubernetes secrets or environment variables

Example configuration structure:

```yaml
environment: production

data:
  fhir:
    base_url: https://fhir.example.org/R4
    page_count: 1000
  deidentification:
    date_shift: 365
    phi_patterns:
      - name: mrn
        regex: \b\d{3}-\d{2}-\d{4}\b
        replacement: "[MEDICAL_RECORD]"

model:
  serving:
    batch_size: 32
    timeout_seconds: 30
  fairness_constraints:
    max_disparity: 0.1
    protected_attributes: [race, gender, age_group]

monitoring:
  enabled: true
  log_level: INFO
  metrics_interval_seconds: 60
```

### Environment Variables

Critical configuration can be provided via environment variables:

```
READMISSION_ENV=production
READMISSION_FHIR_BASE_URL=https://fhir.example.org/R4
READMISSION_FHIR_CLIENT_ID=client_id
READMISSION_FHIR_CLIENT_SECRET=client_secret
READMISSION_DATABASE_URL=postgresql://user:password@localhost:5432/readmission
```

### Secrets Management

Sensitive information should be stored in Kubernetes secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: readmission-secrets
  namespace: readmission-system
type: Opaque
data:
  fhir-client-id: Y2xpZW50X2lk
  fhir-client-secret: Y2xpZW50X3NlY3JldA==
  database-password: cGFzc3dvcmQ=
```

## Database Setup

### PostgreSQL Setup

1. Create the database:

   ```sql
   CREATE DATABASE readmission;
   CREATE USER readmission_user WITH ENCRYPTED PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE readmission TO readmission_user;
   ```

2. Initialize the schema:
   ```bash
   psql -U readmission_user -d readmission -f scripts/schema.sql
   ```

### FHIR Database Integration

1. Configure FHIR server connection:

   ```yaml
   fhir:
     server_url: https://fhir.example.org/R4
     client_id: client_id
     client_secret: client_secret
     version: R4
   ```

2. Test the connection:
   ```bash
   python -m src.utils.fhir_connector --test
   ```

## Security Considerations

### Network Security

1. **API Security**:
   - Use TLS for all communications
   - Implement API rate limiting
   - Use JWT for authentication

2. **Kubernetes Network Policies**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: readmission-network-policy
     namespace: readmission-system
   spec:
     podSelector:
       matchLabels:
         app: readmission
     ingress:
       - from:
           - namespaceSelector:
               matchLabels:
                 name: ingress-nginx
         ports:
           - protocol: TCP
             port: 8000
   ```

### Data Security

1. **PHI Protection**:
   - Enable PHI audit logging
   - Implement data de-identification
   - Use encrypted storage

2. **Access Control**:
   - Implement role-based access control
   - Use least privilege principle
   - Audit all data access

### Compliance

1. **HIPAA Compliance**:
   - Enable HIPAA audit logging
   - Implement BAA with cloud providers
   - Regular security assessments

2. **FDA Considerations**:
   - Document model validation
   - Maintain version control
   - Track model lineage

## Monitoring and Logging

### Prometheus Monitoring

1. Deploy Prometheus:

   ```bash
   helm install prometheus prometheus-community/prometheus \
     --namespace monitoring \
     --create-namespace
   ```

2. Configure scraping:
   ```yaml
   prometheus:
     scrape_configs:
       - job_name: "readmission-metrics"
         kubernetes_sd_configs:
           - role: pod
         relabel_configs:
           - source_labels: [__meta_kubernetes_pod_label_app]
             action: keep
             regex: readmission
   ```

### Grafana Dashboards

1. Deploy Grafana:

   ```bash
   helm install grafana grafana/grafana \
     --namespace monitoring \
     --set adminPassword=admin
   ```

2. Import dashboards:

   ```bash
   kubectl apply -f monitoring/dashboards/
   ```

3. Access Grafana:
   ```bash
   kubectl port-forward svc/grafana 3000:3000 -n monitoring
   ```

### Logging with ELK Stack

1. Deploy ELK stack:

   ```bash
   helm install elk elastic/eck-operator \
     --namespace logging \
     --create-namespace
   ```

2. Configure log shipping:

   ```yaml
   filebeat:
     inputs:
       - type: container
         paths:
           - /var/log/containers/*readmission*.log
   ```

3. Access Kibana:
   ```bash
   kubectl port-forward svc/kibana-kb-http 5601:5601 -n logging
   ```

## Backup and Recovery

### Database Backup

1. Set up automated backups:

   ```bash
   kubectl apply -f deployments/kubernetes/backup-cronjob.yaml
   ```

2. Backup script:
   ```bash
   #!/bin/bash
   TIMESTAMP=$(date +%Y%m%d%H%M%S)
   pg_dump -U readmission_user -d readmission | gzip > /backups/readmission-$TIMESTAMP.sql.gz
   ```

### Model Artifacts Backup

1. Back up model registry:

   ```bash
   aws s3 sync /mnt/models s3://readmission-models-backup/
   ```

2. Version control for model artifacts:
   ```bash
   dvc push
   ```

### Disaster Recovery

1. Create a disaster recovery plan:
   - Document recovery procedures
   - Regular recovery testing
   - Offsite backup storage

2. Recovery testing script:

   ```bash
   #!/bin/bash
   # Test database restore
   gunzip -c /backups/readmission-latest.sql.gz | psql -U readmission_user -d readmission_test

   # Test model loading
   python -m src.utils.model_loader --test --model-path /backups/models/latest
   ```

## Troubleshooting

### Common Deployment Issues

#### Pod Startup Failures

**Problem**: Pods fail to start or crash loop

**Solution**:

1. Check pod logs:
   ```bash
   kubectl logs -n readmission-system pod/readmission-api-xyz
   ```
2. Check pod events:
   ```bash
   kubectl describe pod -n readmission-system readmission-api-xyz
   ```
3. Check resource constraints:
   ```bash
   kubectl top pod -n readmission-system
   ```

#### Database Connection Issues

**Problem**: Services cannot connect to database

**Solution**:

1. Check database service:
   ```bash
   kubectl get svc -n readmission-system postgres
   ```
2. Test connection from a pod:
   ```bash
   kubectl exec -it -n readmission-system deploy/readmission-api -- \
     psql -h postgres -U readmission_user -d readmission -c "SELECT 1"
   ```
3. Check secrets:
   ```bash
   kubectl get secret -n readmission-system readmission-db-credentials -o yaml
   ```

#### API Connectivity Issues

**Problem**: Cannot access API endpoints

**Solution**:

1. Check ingress configuration:
   ```bash
   kubectl get ingress -n readmission-system
   ```
2. Test service internally:
   ```bash
   kubectl exec -it -n readmission-system deploy/readmission-api -- \
     curl http://localhost:8000/api/v1/health
   ```
3. Check TLS certificates:
   ```bash
   kubectl get secret -n readmission-system tls-cert -o yaml
   ```

### Deployment Rollback

If a deployment fails, you can roll back to a previous version:

```bash
# Helm rollback
helm rollback readmission 1 -n readmission-system

# Kubernetes rollback
kubectl rollout undo deployment/readmission-api -n readmission-system
```

### Support Resources

For additional help:

1. Check the project's GitHub issues
2. Join the Slack support channel
3. Contact the development team at support@readmission-risk-system.org
