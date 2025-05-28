# Deployments Directory

## Overview

The deployments directory contains configuration files and resources necessary for deploying the Nexora system to various environments. This directory serves as a central repository for deployment configurations across different infrastructure platforms, ensuring consistent and reproducible deployments of the application.

## Directory Structure

```
deployments/
├── helm/
│   └── readmission-chart/
│       └── values.yaml
├── k8s/
│   ├── feature_server.yaml
│   └── model_serving.yaml
└── terraform/
    └── hospital_readmission.tf
```

## Contents Description

### Subdirectories

#### helm/

This subdirectory contains Helm charts for deploying Nexora components to Kubernetes clusters:

- **readmission-chart/values.yaml**: Configuration values for the hospital readmission prediction service Helm chart. This file defines parameters such as replica counts, resource requests/limits, environment variables, and other configuration options specific to the readmission prediction service deployment.

#### k8s/

This subdirectory contains raw Kubernetes manifests for deploying Nexora components:

- **feature_server.yaml**: Kubernetes manifest for deploying the feature server component, which likely serves pre-computed features for the machine learning models. This file defines the Kubernetes resources (Deployments, Services, ConfigMaps, etc.) required for running the feature server.

- **model_serving.yaml**: Kubernetes manifest for deploying the model serving component, which hosts the trained machine learning models and exposes them via an API. This file defines the Kubernetes resources required for running the model serving infrastructure.

#### terraform/

This subdirectory contains Terraform configurations for provisioning cloud infrastructure:

- **hospital_readmission.tf**: Terraform configuration for provisioning infrastructure resources required by the hospital readmission prediction system. This likely includes compute resources, storage, networking, and possibly managed services like databases or message queues.

## Usage

The deployment configurations in this directory are used to deploy the Nexora system to various environments:

1. **Helm Deployments**:
   ```bash
   helm install readmission-service ./helm/readmission-chart -f ./helm/readmission-chart/values.yaml
   ```

2. **Kubernetes Deployments**:
   ```bash
   kubectl apply -f ./k8s/feature_server.yaml
   kubectl apply -f ./k8s/model_serving.yaml
   ```

3. **Terraform Deployments**:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

## Best Practices

1. **Environment Separation**: Maintain separate configuration files for different environments (development, staging, production).
2. **Secret Management**: Never store sensitive information like passwords or API keys in these files. Use Kubernetes Secrets, HashiCorp Vault, or cloud provider secret management services instead.
3. **Version Control**: Always commit deployment configuration changes to version control with clear commit messages.
4. **Validation**: Test deployment changes in a development environment before applying to production.
5. **Documentation**: Document any environment-specific configurations and prerequisites.
6. **Automation**: Use CI/CD pipelines to automate the deployment process using these configuration files.

## Related Components

- The deployment configurations in this directory are related to the components in the `infrastructure/` directory, which provides the underlying infrastructure setup.
- The deployed services use code from the `src/` directory, particularly components in `src/serving/` for model serving and API endpoints.
- The configurations may reference container images built from the application code in the repository.
