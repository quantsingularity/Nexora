#!/usr/bin/env python3
"""
Deployment Validation Script for Nexora

This script performs comprehensive validation of Nexora deployments to ensure
they are functioning correctly. It validates deployed services, API endpoints,
database migrations, and configuration settings.

Usage:
    python deployment_validation.py --env [dev|staging|prod] [options]

Options:
    --env ENV               Target environment (dev, staging, prod)
    --config PATH           Path to config file (default: config/deployment_config.yaml)
    --output PATH           Path to output report (default: stdout)
    --format FORMAT         Output format (text, json, html) (default: text)
    --notify                Send notifications on validation failures
    --rollback              Automatically rollback failed deployments
    --timeout SECONDS       Timeout for validation checks (default: 300)
    --verbose               Enable verbose output
    --help                  Show this help message

Examples:
    python deployment_validation.py --env dev
    python deployment_validation.py --env prod --format json --output validation_report.json
    python deployment_validation.py --env staging --notify --rollback
"""

import argparse
import datetime
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml

# Try to import optional dependencies
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pymongo

    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import psycopg2

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import kubernetes

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

try:
    from kubernetes import client, config

    K8S_CLIENT_AVAILABLE = True
except ImportError:
    K8S_CLIENT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deployment_validation")


class DeploymentValidator:
    """Main class for validating deployments"""

    def __init__(
        self,
        config_path: str,
        env: str,
        timeout: int = 300,
        rollback: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the deployment validator with configuration

        Args:
            config_path: Path to the configuration file
            env: Target environment (dev, staging, prod)
            timeout: Timeout for validation checks in seconds
            rollback: Whether to automatically rollback failed deployments
            verbose: Enable verbose output
        """
        self.config_path = config_path
        self.env = env
        self.timeout = timeout
        self.rollback = rollback
        self.verbose = verbose
        self.config = self._load_config()
        self.results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "environment": env,
            "status": "UNKNOWN",
            "summary": {},
            "validations": {},
        }

        if verbose:
            logger.setLevel(logging.DEBUG)

        logger.info(f"Initializing deployment validation for {env} environment")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                # Create default config structure
                return {
                    "environments": {
                        self.env: {
                            "deployment": {
                                "name": f"nexora-{self.env}",
                                "version": "latest",
                                "namespace": "nexora",
                                "rollback_enabled": False,
                            },
                            "kubernetes": {
                                "enabled": False,
                                "context": None,
                                "namespace": "nexora",
                                "expected_deployments": [],
                                "expected_services": [],
                            },
                            "services": [],
                            "api_endpoints": [],
                            "databases": [],
                            "config_validations": [],
                        }
                    }
                }

            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            if not config or "environments" not in config:
                logger.error("Invalid configuration format")
                raise ValueError("Invalid configuration format")

            if self.env not in config["environments"]:
                logger.error(f"Environment '{self.env}' not found in configuration")
                raise ValueError(f"Environment '{self.env}' not found in configuration")

            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    def run_all_validations(self) -> Dict:
        """Run all deployment validations and return results"""
        logger.info("Starting deployment validations")

        # Get deployment info
        self._get_deployment_info()

        # Kubernetes validations
        self.validate_kubernetes()

        # Service validations
        self.validate_services()

        # API endpoint validations
        self.validate_api_endpoints()

        # Database validations
        self.validate_databases()

        # Configuration validations
        self.validate_configurations()

        # Determine overall status
        self._calculate_overall_status()

        # Handle rollback if needed
        if self.rollback and self.results["status"] in ["FAIL", "ERROR"]:
            self._perform_rollback()

        logger.info(
            f"Deployment validations completed with status: {self.results['status']}"
        )
        return self.results

    def _get_deployment_info(self) -> None:
        """Get information about the current deployment"""
        deployment_config = self.config["environments"][self.env].get("deployment", {})

        deployment_name = deployment_config.get("name", f"nexora-{self.env}")
        deployment_version = deployment_config.get("version", "latest")

        # Try to get actual version from various sources
        actual_version = self._get_actual_version()

        self.results["deployment_info"] = {
            "name": deployment_name,
            "environment": self.env,
            "expected_version": deployment_version,
            "actual_version": actual_version,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    def _get_actual_version(self) -> str:
        """Try to determine the actual deployed version"""
        # Try Kubernetes first if enabled
        k8s_config = self.config["environments"][self.env].get("kubernetes", {})
        if k8s_config.get("enabled", False) and K8S_CLIENT_AVAILABLE:
            try:
                # Load Kubernetes configuration
                if k8s_config.get("in_cluster", False):
                    config.load_incluster_config()
                else:
                    config.load_kube_config(
                        config_file=k8s_config.get("config_file"),
                        context=k8s_config.get("context"),
                    )

                # Get namespace
                namespace = k8s_config.get("namespace", "nexora")

                # Get deployments
                apps_v1 = client.AppsV1Api()
                deployments = apps_v1.list_namespaced_deployment(namespace).items

                # Look for main deployment
                deployment_config = self.config["environments"][self.env].get(
                    "deployment", {}
                )
                deployment_name = deployment_config.get("name", f"nexora-{self.env}")

                for deployment in deployments:
                    if deployment.metadata.name == deployment_name:
                        # Try to get version from labels or annotations
                        if (
                            deployment.metadata.labels
                            and "version" in deployment.metadata.labels
                        ):
                            return deployment.metadata.labels["version"]
                        if (
                            deployment.metadata.annotations
                            and "version" in deployment.metadata.annotations
                        ):
                            return deployment.metadata.annotations["version"]

                        # Try to parse version from image
                        if (
                            deployment.spec.template.spec.containers
                            and deployment.spec.template.spec.containers[0].image
                        ):
                            image = deployment.spec.template.spec.containers[0].image
                            # Try to extract version from image tag
                            if ":" in image:
                                return image.split(":")[-1]
            except Exception as e:
                logger.debug(f"Error getting version from Kubernetes: {str(e)}")

        # Try version endpoint if configured
        version_endpoint = self.config["environments"][self.env].get("version_endpoint")
        if version_endpoint and REQUESTS_AVAILABLE:
            try:
                response = requests.get(version_endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "version" in data:
                        return data["version"]
            except Exception as e:
                logger.debug(f"Error getting version from endpoint: {str(e)}")

        # Default to unknown
        return "unknown"

    def validate_kubernetes(self) -> None:
        """Validate Kubernetes resources"""
        logger.info("Validating Kubernetes resources")

        k8s_config = self.config["environments"][self.env].get("kubernetes", {})

        if not k8s_config.get("enabled", False):
            logger.debug("Kubernetes validation not enabled")
            return

        if not K8S_CLIENT_AVAILABLE:
            self.results["validations"]["kubernetes"] = {
                "status": "ERROR",
                "message": "kubernetes client library not available for Kubernetes validation",
            }
            return

        try:
            # Load Kubernetes configuration
            if k8s_config.get("in_cluster", False):
                config.load_incluster_config()
            else:
                config.load_kube_config(
                    config_file=k8s_config.get("config_file"),
                    context=k8s_config.get("context"),
                )

            # Initialize API clients
            core_v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            # Get namespace
            namespace = k8s_config.get("namespace", "nexora")

            k8s_validations = {}

            # Validate deployments
            if k8s_config.get("validate_deployments", True):
                deployments_status, deployments_details = (
                    self._validate_k8s_deployments(
                        apps_v1, namespace, k8s_config.get("expected_deployments", [])
                    )
                )
                k8s_validations["deployments"] = {
                    "status": deployments_status,
                    "namespace": namespace,
                    **deployments_details,
                }

            # Validate services
            if k8s_config.get("validate_services", True):
                services_status, services_details = self._validate_k8s_services(
                    core_v1, namespace, k8s_config.get("expected_services", [])
                )
                k8s_validations["services"] = {
                    "status": services_status,
                    "namespace": namespace,
                    **services_details,
                }

            # Validate pods
            if k8s_config.get("validate_pods", True):
                pods_status, pods_details = self._validate_k8s_pods(core_v1, namespace)
                k8s_validations["pods"] = {
                    "status": pods_status,
                    "namespace": namespace,
                    **pods_details,
                }

            # Validate ingress
            if k8s_config.get("validate_ingress", True):
                try:
                    networking_v1 = client.NetworkingV1Api()
                    ingress_status, ingress_details = self._validate_k8s_ingress(
                        networking_v1, namespace, k8s_config.get("expected_ingress", [])
                    )
                    k8s_validations["ingress"] = {
                        "status": ingress_status,
                        "namespace": namespace,
                        **ingress_details,
                    }
                except Exception as e:
                    k8s_validations["ingress"] = {
                        "status": "ERROR",
                        "message": f"Error validating ingress: {str(e)}",
                    }

            # Validate config maps
            if k8s_config.get("validate_configmaps", True):
                configmaps_status, configmaps_details = self._validate_k8s_configmaps(
                    core_v1, namespace, k8s_config.get("expected_configmaps", [])
                )
                k8s_validations["configmaps"] = {
                    "status": configmaps_status,
                    "namespace": namespace,
                    **configmaps_details,
                }

            # Validate secrets
            if k8s_config.get("validate_secrets", True):
                secrets_status, secrets_details = self._validate_k8s_secrets(
                    core_v1, namespace, k8s_config.get("expected_secrets", [])
                )
                k8s_validations["secrets"] = {
                    "status": secrets_status,
                    "namespace": namespace,
                    **secrets_details,
                }

            self.results["validations"]["kubernetes"] = k8s_validations

        except Exception as e:
            self.results["validations"]["kubernetes"] = {
                "status": "ERROR",
                "message": f"Error validating Kubernetes resources: {str(e)}",
            }

    def _validate_k8s_deployments(
        self, apps_v1, namespace: str, expected_deployments: List[str]
    ) -> Tuple[str, Dict]:
        """Validate Kubernetes deployments"""
        try:
            deployments = apps_v1.list_namespaced_deployment(namespace).items

            deployment_statuses = []
            missing_deployments = []
            not_ready_deployments = []

            # Check if all expected deployments exist
            found_deployments = set(d.metadata.name for d in deployments)
            for expected in expected_deployments:
                if expected not in found_deployments:
                    missing_deployments.append(expected)

            # Check if deployments are ready
            for deployment in deployments:
                deployment_name = deployment.metadata.name
                replicas = deployment.spec.replicas
                available_replicas = deployment.status.available_replicas or 0

                deployment_statuses.append(
                    {
                        "name": deployment_name,
                        "replicas": replicas,
                        "available": available_replicas,
                        "ready": available_replicas == replicas,
                        "expected": deployment_name in expected_deployments,
                    }
                )

                if available_replicas != replicas:
                    not_ready_deployments.append(
                        f"{deployment_name} ({available_replicas}/{replicas} ready)"
                    )

            if missing_deployments:
                return "FAIL", {
                    "message": f"Missing expected deployments: {', '.join(missing_deployments)}",
                    "deployments": deployment_statuses,
                    "missing": missing_deployments,
                    "not_ready": not_ready_deployments,
                }
            elif not_ready_deployments:
                return "FAIL", {
                    "message": f"Deployments not ready: {', '.join(not_ready_deployments)}",
                    "deployments": deployment_statuses,
                    "missing": missing_deployments,
                    "not_ready": not_ready_deployments,
                }
            else:
                return "PASS", {
                    "message": f"All deployments are ready",
                    "deployments": deployment_statuses,
                    "total_deployments": len(deployments),
                    "expected_deployments": len(expected_deployments),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating Kubernetes deployments: {str(e)}"
            }

    def _validate_k8s_services(
        self, core_v1, namespace: str, expected_services: List[str]
    ) -> Tuple[str, Dict]:
        """Validate Kubernetes services"""
        try:
            services = core_v1.list_namespaced_service(namespace).items

            service_statuses = []
            missing_services = []

            # Check if all expected services exist
            found_services = set(s.metadata.name for s in services)
            for expected in expected_services:
                if expected not in found_services:
                    missing_services.append(expected)

            # Get details for all services
            for service in services:
                service_name = service.metadata.name
                service_type = service.spec.type
                cluster_ip = service.spec.cluster_ip

                ports = []
                for port in service.spec.ports:
                    ports.append(
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol,
                        }
                    )

                # Check if endpoints exist for the service
                try:
                    endpoints = core_v1.read_namespaced_endpoints(
                        service_name, namespace
                    )
                    has_endpoints = bool(endpoints.subsets)
                except Exception:
                    has_endpoints = False

                service_statuses.append(
                    {
                        "name": service_name,
                        "type": service_type,
                        "cluster_ip": cluster_ip,
                        "ports": ports,
                        "has_endpoints": has_endpoints,
                        "expected": service_name in expected_services,
                    }
                )

            if missing_services:
                return "FAIL", {
                    "message": f"Missing expected services: {', '.join(missing_services)}",
                    "services": service_statuses,
                    "missing": missing_services,
                }
            else:
                return "PASS", {
                    "message": f"All expected services exist",
                    "services": service_statuses,
                    "total_services": len(services),
                    "expected_services": len(expected_services),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating Kubernetes services: {str(e)}"
            }

    def _validate_k8s_pods(self, core_v1, namespace: str) -> Tuple[str, Dict]:
        """Validate Kubernetes pods"""
        try:
            pods = core_v1.list_namespaced_pod(namespace).items

            pod_statuses = []
            not_running_pods = []

            for pod in pods:
                pod_name = pod.metadata.name
                pod_status = pod.status.phase

                # Get container statuses
                container_statuses = []
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        container_statuses.append(
                            {
                                "name": container.name,
                                "ready": container.ready,
                                "restart_count": container.restart_count,
                                "image": container.image,
                            }
                        )

                # Check if pod is ready
                is_ready = self._is_pod_ready(pod)

                pod_statuses.append(
                    {
                        "name": pod_name,
                        "status": pod_status,
                        "ready": is_ready,
                        "restarts": self._get_pod_restarts(pod),
                        "age": self._get_pod_age(pod),
                        "containers": container_statuses,
                    }
                )

                if pod_status != "Running" or not is_ready:
                    not_running_pods.append(f"{pod_name} ({pod_status})")

            if not_running_pods:
                return "FAIL", {
                    "message": f"{len(not_running_pods)} pod(s) not running: {', '.join(not_running_pods)}",
                    "pods": pod_statuses,
                    "total_pods": len(pods),
                    "running_pods": len(pods) - len(not_running_pods),
                    "not_running": not_running_pods,
                }
            else:
                return "PASS", {
                    "message": f"All {len(pods)} pods are running",
                    "pods": pod_statuses,
                    "total_pods": len(pods),
                    "running_pods": len(pods),
                }
        except Exception as e:
            return "ERROR", {"message": f"Error validating Kubernetes pods: {str(e)}"}

    def _is_pod_ready(self, pod) -> bool:
        """Check if a pod is ready"""
        if pod.status.phase != "Running":
            return False

        if not pod.status.container_statuses:
            return False

        for container_status in pod.status.container_statuses:
            if not container_status.ready:
                return False

        return True

    def _get_pod_restarts(self, pod) -> int:
        """Get total restarts for a pod"""
        restarts = 0
        if pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                restarts += container_status.restart_count
        return restarts

    def _get_pod_age(self, pod) -> str:
        """Get age of a pod"""
        if pod.metadata.creation_timestamp:
            age_seconds = (
                datetime.datetime.now(datetime.timezone.utc)
                - pod.metadata.creation_timestamp.replace(tzinfo=datetime.timezone.utc)
            ).total_seconds()

            if age_seconds < 60:
                return f"{int(age_seconds)}s"
            elif age_seconds < 3600:
                return f"{int(age_seconds / 60)}m"
            elif age_seconds < 86400:
                return f"{int(age_seconds / 3600)}h"
            else:
                return f"{int(age_seconds / 86400)}d"
        return "Unknown"

    def _validate_k8s_ingress(
        self, networking_v1, namespace: str, expected_ingress: List[str]
    ) -> Tuple[str, Dict]:
        """Validate Kubernetes ingress"""
        try:
            ingresses = networking_v1.list_namespaced_ingress(namespace).items

            ingress_statuses = []
            missing_ingress = []

            # Check if all expected ingress resources exist
            found_ingress = set(i.metadata.name for i in ingresses)
            for expected in expected_ingress:
                if expected not in found_ingress:
                    missing_ingress.append(expected)

            # Get details for all ingress resources
            for ingress in ingresses:
                ingress_name = ingress.metadata.name

                # Get rules
                rules = []
                if ingress.spec.rules:
                    for rule in ingress.spec.rules:
                        rule_info = {"host": rule.host}

                        # Get paths
                        if rule.http and rule.http.paths:
                            paths = []
                            for path in rule.http.paths:
                                path_info = {
                                    "path": path.path,
                                    "path_type": path.path_type,
                                }

                                # Get backend
                                if path.backend:
                                    if (
                                        hasattr(path.backend, "service")
                                        and path.backend.service
                                    ):
                                        path_info["backend"] = {
                                            "service_name": path.backend.service.name,
                                            "service_port": (
                                                path.backend.service.port.number
                                                if path.backend.service.port
                                                else None
                                            ),
                                        }

                                paths.append(path_info)

                            rule_info["paths"] = paths

                        rules.append(rule_info)

                # Get TLS
                tls = []
                if ingress.spec.tls:
                    for tls_item in ingress.spec.tls:
                        tls.append(
                            {
                                "hosts": tls_item.hosts,
                                "secret_name": tls_item.secret_name,
                            }
                        )

                ingress_statuses.append(
                    {
                        "name": ingress_name,
                        "rules": rules,
                        "tls": tls,
                        "expected": ingress_name in expected_ingress,
                    }
                )

            if missing_ingress:
                return "FAIL", {
                    "message": f"Missing expected ingress resources: {', '.join(missing_ingress)}",
                    "ingress": ingress_statuses,
                    "missing": missing_ingress,
                }
            else:
                return "PASS", {
                    "message": f"All expected ingress resources exist",
                    "ingress": ingress_statuses,
                    "total_ingress": len(ingresses),
                    "expected_ingress": len(expected_ingress),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating Kubernetes ingress: {str(e)}"
            }

    def _validate_k8s_configmaps(
        self, core_v1, namespace: str, expected_configmaps: List[str]
    ) -> Tuple[str, Dict]:
        """Validate Kubernetes ConfigMaps"""
        try:
            configmaps = core_v1.list_namespaced_config_map(namespace).items

            configmap_statuses = []
            missing_configmaps = []

            # Check if all expected ConfigMaps exist
            found_configmaps = set(cm.metadata.name for cm in configmaps)
            for expected in expected_configmaps:
                if expected not in found_configmaps:
                    missing_configmaps.append(expected)

            # Get details for all ConfigMaps
            for configmap in configmaps:
                configmap_name = configmap.metadata.name

                # Get data keys
                data_keys = []
                if configmap.data:
                    data_keys = list(configmap.data.keys())

                configmap_statuses.append(
                    {
                        "name": configmap_name,
                        "data_keys": data_keys,
                        "expected": configmap_name in expected_configmaps,
                    }
                )

            if missing_configmaps:
                return "FAIL", {
                    "message": f"Missing expected ConfigMaps: {', '.join(missing_configmaps)}",
                    "configmaps": configmap_statuses,
                    "missing": missing_configmaps,
                }
            else:
                return "PASS", {
                    "message": f"All expected ConfigMaps exist",
                    "configmaps": configmap_statuses,
                    "total_configmaps": len(configmaps),
                    "expected_configmaps": len(expected_configmaps),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating Kubernetes ConfigMaps: {str(e)}"
            }

    def _validate_k8s_secrets(
        self, core_v1, namespace: str, expected_secrets: List[str]
    ) -> Tuple[str, Dict]:
        """Validate Kubernetes Secrets"""
        try:
            secrets = core_v1.list_namespaced_secret(namespace).items

            secret_statuses = []
            missing_secrets = []

            # Check if all expected Secrets exist
            found_secrets = set(s.metadata.name for s in secrets)
            for expected in expected_secrets:
                if expected not in found_secrets:
                    missing_secrets.append(expected)

            # Get details for all Secrets
            for secret in secrets:
                secret_name = secret.metadata.name
                secret_type = secret.type

                # Get data keys (without revealing values)
                data_keys = []
                if secret.data:
                    data_keys = list(secret.data.keys())

                secret_statuses.append(
                    {
                        "name": secret_name,
                        "type": secret_type,
                        "data_keys": data_keys,
                        "expected": secret_name in expected_secrets,
                    }
                )

            if missing_secrets:
                return "FAIL", {
                    "message": f"Missing expected Secrets: {', '.join(missing_secrets)}",
                    "secrets": secret_statuses,
                    "missing": missing_secrets,
                }
            else:
                return "PASS", {
                    "message": f"All expected Secrets exist",
                    "secrets": secret_statuses,
                    "total_secrets": len(secrets),
                    "expected_secrets": len(expected_secrets),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating Kubernetes Secrets: {str(e)}"
            }

    def validate_services(self) -> None:
        """Validate services"""
        logger.info("Validating services")

        services_config = self.config["environments"][self.env].get("services", [])
        service_validations = {}

        for service in services_config:
            service_name = service.get("name", "unknown")
            service_type = service.get("type", "http")

            logger.debug(f"Validating service: {service_name} (type: {service_type})")

            if service_type == "http":
                # Validate HTTP service
                url = service.get("url")
                method = service.get("method", "GET")
                expected_status = service.get("expected_status", 200)
                timeout = service.get("timeout", 10)
                headers = service.get("headers", {})
                content_check = service.get("content_check")

                if not url:
                    service_validations[service_name] = {
                        "status": "ERROR",
                        "type": "http",
                        "message": "No URL specified",
                    }
                    continue

                status, details = self._validate_http_service(
                    url, method, expected_status, timeout, headers, content_check
                )
                service_validations[service_name] = {
                    "status": status,
                    "type": "http",
                    "url": url,
                    **details,
                }

            elif service_type == "tcp":
                # Validate TCP service
                host = service.get("host", "localhost")
                port = service.get("port")
                timeout = service.get("timeout", 5)

                if not port:
                    service_validations[service_name] = {
                        "status": "ERROR",
                        "type": "tcp",
                        "message": "No port specified",
                    }
                    continue

                status, details = self._validate_tcp_service(host, port, timeout)
                service_validations[service_name] = {
                    "status": status,
                    "type": "tcp",
                    "host": host,
                    "port": port,
                    **details,
                }

            elif service_type == "command":
                # Validate using command
                command = service.get("command")
                expected_exit_code = service.get("expected_exit_code", 0)
                timeout = service.get("timeout", 30)

                if not command:
                    service_validations[service_name] = {
                        "status": "ERROR",
                        "type": "command",
                        "message": "No command specified",
                    }
                    continue

                status, details = self._validate_command(
                    command, expected_exit_code, timeout
                )
                service_validations[service_name] = {
                    "status": status,
                    "type": "command",
                    "command": command,
                    **details,
                }

            else:
                service_validations[service_name] = {
                    "status": "ERROR",
                    "type": service_type,
                    "message": f"Unsupported service type: {service_type}",
                }

        self.results["validations"]["services"] = service_validations

    def _validate_http_service(
        self,
        url: str,
        method: str,
        expected_status: int,
        timeout: int,
        headers: Dict,
        content_check: Optional[str],
    ) -> Tuple[str, Dict]:
        """Validate HTTP service"""
        if not REQUESTS_AVAILABLE:
            return "ERROR", {
                "message": "requests library not available for HTTP validation"
            }

        try:
            start_time = time.time()
            response = requests.request(
                method=method, url=url, headers=headers, timeout=timeout
            )
            response_time = time.time() - start_time

            status_check = response.status_code == expected_status
            content_check_result = True

            # Check response content if specified
            if content_check and status_check:
                if content_check in response.text:
                    content_check_message = f"Response contains '{content_check}'"
                else:
                    content_check_result = False
                    content_check_message = (
                        f"Response does not contain '{content_check}'"
                    )
            else:
                content_check_message = "No content check specified"

            if status_check and content_check_result:
                return "PASS", {
                    "message": f"HTTP service validation passed",
                    "status_code": response.status_code,
                    "response_time": f"{response_time:.3f}s",
                    "content_check": content_check_message,
                }
            else:
                return "FAIL", {
                    "message": f"HTTP service validation failed",
                    "status_code": response.status_code,
                    "expected_status": expected_status,
                    "response_time": f"{response_time:.3f}s",
                    "content_check": content_check_message,
                }
        except requests.exceptions.Timeout:
            return "FAIL", {
                "message": f"HTTP request to {url} timed out after {timeout}s"
            }
        except requests.exceptions.ConnectionError:
            return "FAIL", {"message": f"Connection error when connecting to {url}"}
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating HTTP service {url}: {str(e)}"
            }

    def _validate_tcp_service(
        self, host: str, port: int, timeout: int
    ) -> Tuple[str, Dict]:
        """Validate TCP service"""
        try:
            start_time = time.time()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            connection_time = time.time() - start_time

            if result == 0:
                return "PASS", {
                    "message": f"TCP service is available at {host}:{port}",
                    "connection_time": f"{connection_time:.3f}s",
                }
            else:
                return "FAIL", {
                    "message": f"TCP service is not available at {host}:{port} (error code: {result})",
                    "error_code": result,
                }
        except socket.timeout:
            return "FAIL", {
                "message": f"Connection to {host}:{port} timed out after {timeout}s"
            }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating TCP service at {host}:{port}: {str(e)}"
            }

    def _validate_command(
        self, command: str, expected_exit_code: int, timeout: int
    ) -> Tuple[str, Dict]:
        """Validate using command"""
        try:
            start_time = time.time()
            process = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            execution_time = time.time() - start_time

            if process.returncode == expected_exit_code:
                return "PASS", {
                    "message": f"Command executed successfully with exit code {process.returncode}",
                    "exit_code": process.returncode,
                    "execution_time": f"{execution_time:.3f}s",
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                }
            else:
                return "FAIL", {
                    "message": f"Command failed with exit code {process.returncode}, expected {expected_exit_code}",
                    "exit_code": process.returncode,
                    "execution_time": f"{execution_time:.3f}s",
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                }
        except subprocess.TimeoutExpired:
            return "FAIL", {"message": f"Command timed out after {timeout}s"}
        except Exception as e:
            return "ERROR", {"message": f"Error running command: {str(e)}"}

    def validate_api_endpoints(self) -> None:
        """Validate API endpoints"""
        logger.info("Validating API endpoints")

        if not REQUESTS_AVAILABLE:
            self.results["validations"]["api_endpoints"] = {
                "status": "ERROR",
                "message": "requests library not available for API endpoint validation",
            }
            return

        endpoints_config = self.config["environments"][self.env].get(
            "api_endpoints", []
        )
        endpoint_validations = {}

        for endpoint in endpoints_config:
            endpoint_name = endpoint.get("name", "unknown")
            url = endpoint.get("url")
            method = endpoint.get("method", "GET")
            headers = endpoint.get("headers", {})
            data = endpoint.get("data")
            expected_status = endpoint.get("expected_status", 200)
            timeout = endpoint.get("timeout", 10)
            content_check = endpoint.get("content_check")
            schema_validation = endpoint.get("schema_validation")

            logger.debug(f"Validating API endpoint: {endpoint_name} ({url})")

            if not url:
                endpoint_validations[endpoint_name] = {
                    "status": "ERROR",
                    "message": "No URL specified",
                }
                continue

            status, details = self._validate_api_endpoint(
                url,
                method,
                headers,
                data,
                expected_status,
                timeout,
                content_check,
                schema_validation,
            )
            endpoint_validations[endpoint_name] = {
                "status": status,
                "url": url,
                "method": method,
                **details,
            }

        self.results["validations"]["api_endpoints"] = endpoint_validations

    def _validate_api_endpoint(
        self,
        url: str,
        method: str,
        headers: Dict,
        data: Any,
        expected_status: int,
        timeout: int,
        content_check: Optional[str],
        schema_validation: Optional[Dict],
    ) -> Tuple[str, Dict]:
        """Validate API endpoint"""
        try:
            start_time = time.time()

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                timeout=timeout,
            )

            response_time = time.time() - start_time

            # Check status code
            status_check = response.status_code == expected_status

            # Check response content if specified
            content_check_result = True
            if content_check and status_check:
                if content_check in response.text:
                    content_check_message = f"Response contains '{content_check}'"
                else:
                    content_check_result = False
                    content_check_message = (
                        f"Response does not contain '{content_check}'"
                    )
            else:
                content_check_message = "No content check specified"

            # Validate schema if specified
            schema_check_result = True
            schema_check_message = "No schema validation specified"
            if schema_validation and status_check:
                try:
                    # Try to parse response as JSON
                    response_json = response.json()

                    # Simple schema validation
                    schema_errors = []

                    # Check required fields
                    if "required_fields" in schema_validation:
                        for field in schema_validation["required_fields"]:
                            if field not in response_json:
                                schema_errors.append(
                                    f"Required field '{field}' missing"
                                )

                    # Check field types
                    if "field_types" in schema_validation:
                        for field, expected_type in schema_validation[
                            "field_types"
                        ].items():
                            if field in response_json:
                                # Check type
                                if expected_type == "string" and not isinstance(
                                    response_json[field], str
                                ):
                                    schema_errors.append(
                                        f"Field '{field}' should be a string"
                                    )
                                elif expected_type == "number" and not isinstance(
                                    response_json[field], (int, float)
                                ):
                                    schema_errors.append(
                                        f"Field '{field}' should be a number"
                                    )
                                elif expected_type == "boolean" and not isinstance(
                                    response_json[field], bool
                                ):
                                    schema_errors.append(
                                        f"Field '{field}' should be a boolean"
                                    )
                                elif expected_type == "array" and not isinstance(
                                    response_json[field], list
                                ):
                                    schema_errors.append(
                                        f"Field '{field}' should be an array"
                                    )
                                elif expected_type == "object" and not isinstance(
                                    response_json[field], dict
                                ):
                                    schema_errors.append(
                                        f"Field '{field}' should be an object"
                                    )

                    if schema_errors:
                        schema_check_result = False
                        schema_check_message = (
                            f"Schema validation failed: {', '.join(schema_errors)}"
                        )
                    else:
                        schema_check_message = "Schema validation passed"
                except ValueError:
                    schema_check_result = False
                    schema_check_message = "Response is not valid JSON"

            # Overall validation result
            if status_check and content_check_result and schema_check_result:
                return "PASS", {
                    "message": f"API endpoint validation passed",
                    "status_code": response.status_code,
                    "response_time": f"{response_time:.3f}s",
                    "content_check": content_check_message,
                    "schema_validation": schema_check_message,
                }
            else:
                return "FAIL", {
                    "message": f"API endpoint validation failed",
                    "status_code": response.status_code,
                    "expected_status": expected_status,
                    "response_time": f"{response_time:.3f}s",
                    "content_check": content_check_message,
                    "schema_validation": schema_check_message,
                }
        except requests.exceptions.Timeout:
            return "FAIL", {
                "message": f"API request to {url} timed out after {timeout}s"
            }
        except requests.exceptions.ConnectionError:
            return "FAIL", {"message": f"Connection error when connecting to {url}"}
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating API endpoint {url}: {str(e)}"
            }

    def validate_databases(self) -> None:
        """Validate databases"""
        logger.info("Validating databases")

        databases_config = self.config["environments"][self.env].get("databases", [])
        database_validations = {}

        for db in databases_config:
            db_name = db.get("name", "unknown")
            db_type = db.get("type", "unknown")

            logger.debug(f"Validating database: {db_name} (type: {db_type})")

            if db_type == "postgresql":
                if not POSTGRES_AVAILABLE:
                    database_validations[db_name] = {
                        "status": "ERROR",
                        "type": db_type,
                        "message": "psycopg2 not available for PostgreSQL validation",
                    }
                    continue

                host = db.get("host", "localhost")
                port = db.get("port", 5432)
                database = db.get("database", "postgres")
                user = db.get("user", "postgres")
                password = db.get("password", "")
                ssl_mode = db.get("ssl_mode", "prefer")
                timeout = db.get("timeout", 5)
                validation_query = db.get("validation_query", "SELECT 1")

                status, details = self._validate_postgresql(
                    host,
                    port,
                    database,
                    user,
                    password,
                    ssl_mode,
                    timeout,
                    validation_query,
                )
                database_validations[db_name] = {
                    "status": status,
                    "type": db_type,
                    "host": host,
                    "port": port,
                    "database": database,
                    **details,
                }

            elif db_type == "mongodb":
                if not MONGODB_AVAILABLE:
                    database_validations[db_name] = {
                        "status": "ERROR",
                        "type": db_type,
                        "message": "pymongo not available for MongoDB validation",
                    }
                    continue

                uri = db.get("uri")
                host = db.get("host", "localhost")
                port = db.get("port", 27017)
                database = db.get("database", "admin")
                user = db.get("user")
                password = db.get("password")
                timeout = db.get("timeout", 5)
                validation_collection = db.get("validation_collection")

                if uri:
                    status, details = self._validate_mongodb_uri(
                        uri, timeout, validation_collection
                    )
                else:
                    status, details = self._validate_mongodb(
                        host,
                        port,
                        database,
                        user,
                        password,
                        timeout,
                        validation_collection,
                    )

                database_validations[db_name] = {
                    "status": status,
                    "type": db_type,
                    **(
                        {"uri": uri}
                        if uri
                        else {"host": host, "port": port, "database": database}
                    ),
                    **details,
                }

            else:
                database_validations[db_name] = {
                    "status": "ERROR",
                    "type": db_type,
                    "message": f"Unsupported database type: {db_type}",
                }

        self.results["validations"]["databases"] = database_validations

    def _validate_postgresql(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        ssl_mode: str,
        timeout: int,
        validation_query: str,
    ) -> Tuple[str, Dict]:
        """Validate PostgreSQL database"""
        try:
            start_time = time.time()
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=database,
                user=user,
                password=password,
                sslmode=ssl_mode,
                connect_timeout=timeout,
            )

            cursor = conn.cursor()

            # Execute validation query
            cursor.execute(validation_query)
            result = cursor.fetchone()

            # Get database version
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            # Check for migrations table if it exists
            has_migrations_table = False
            try:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'migrations'
                    );
                """
                )
                has_migrations_table = cursor.fetchone()[0]

                # If migrations table exists, get latest migration
                latest_migration = None
                if has_migrations_table:
                    try:
                        cursor.execute(
                            "SELECT version FROM migrations ORDER BY id DESC LIMIT 1;"
                        )
                        latest_migration = cursor.fetchone()[0]
                    except:
                        pass
            except:
                pass

            cursor.close()
            conn.close()

            connection_time = time.time() - start_time

            return "PASS", {
                "message": "Successfully validated PostgreSQL database",
                "connection_time": f"{connection_time:.3f}s",
                "version": version,
                "has_migrations_table": has_migrations_table,
                **({"latest_migration": latest_migration} if latest_migration else {}),
            }
        except psycopg2.OperationalError as e:
            return "FAIL", {
                "message": f"Failed to connect to PostgreSQL database: {str(e)}"
            }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating PostgreSQL database: {str(e)}"
            }

    def _validate_mongodb_uri(
        self, uri: str, timeout: int, validation_collection: Optional[str]
    ) -> Tuple[str, Dict]:
        """Validate MongoDB database using URI"""
        try:
            start_time = time.time()
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=timeout * 1000)

            # Force connection
            server_info = client.server_info()

            # Check validation collection if specified
            collection_validation = None
            if validation_collection:
                db_name, coll_name = validation_collection.split(".", 1)
                db = client[db_name]
                coll = db[coll_name]

                # Check if collection exists and count documents
                collection_exists = coll_name in db.list_collection_names()
                if collection_exists:
                    doc_count = coll.count_documents({})
                    collection_validation = {
                        "exists": True,
                        "document_count": doc_count,
                    }
                else:
                    collection_validation = {"exists": False}

            connection_time = time.time() - start_time

            return "PASS", {
                "message": "Successfully validated MongoDB database",
                "connection_time": f"{connection_time:.3f}s",
                "version": server_info.get("version", "unknown"),
                **(
                    {"collection_validation": collection_validation}
                    if collection_validation
                    else {}
                ),
            }
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return "FAIL", {
                "message": f"Failed to connect to MongoDB database: {str(e)}"
            }
        except Exception as e:
            return "ERROR", {"message": f"Error validating MongoDB database: {str(e)}"}

    def _validate_mongodb(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        timeout: int,
        validation_collection: Optional[str],
    ) -> Tuple[str, Dict]:
        """Validate MongoDB database"""
        try:
            start_time = time.time()

            if user and password:
                client = pymongo.MongoClient(
                    host=host,
                    port=port,
                    username=user,
                    password=password,
                    authSource=database,
                    serverSelectionTimeoutMS=timeout * 1000,
                )
            else:
                client = pymongo.MongoClient(
                    host=host, port=port, serverSelectionTimeoutMS=timeout * 1000
                )

            # Force connection
            server_info = client.server_info()

            # Check validation collection if specified
            collection_validation = None
            if validation_collection:
                if "." in validation_collection:
                    db_name, coll_name = validation_collection.split(".", 1)
                else:
                    db_name, coll_name = database, validation_collection

                db = client[db_name]
                coll = db[coll_name]

                # Check if collection exists and count documents
                collection_exists = coll_name in db.list_collection_names()
                if collection_exists:
                    doc_count = coll.count_documents({})
                    collection_validation = {
                        "exists": True,
                        "document_count": doc_count,
                    }
                else:
                    collection_validation = {"exists": False}

            connection_time = time.time() - start_time

            return "PASS", {
                "message": "Successfully validated MongoDB database",
                "connection_time": f"{connection_time:.3f}s",
                "version": server_info.get("version", "unknown"),
                **(
                    {"collection_validation": collection_validation}
                    if collection_validation
                    else {}
                ),
            }
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return "FAIL", {
                "message": f"Failed to connect to MongoDB database: {str(e)}"
            }
        except Exception as e:
            return "ERROR", {"message": f"Error validating MongoDB database: {str(e)}"}

    def validate_configurations(self) -> None:
        """Validate configuration settings"""
        logger.info("Validating configurations")

        config_validations = self.config["environments"][self.env].get(
            "config_validations", []
        )
        configuration_results = {}

        for validation in config_validations:
            validation_name = validation.get("name", "unknown")
            validation_type = validation.get("type", "file")

            logger.debug(
                f"Validating configuration: {validation_name} (type: {validation_type})"
            )

            if validation_type == "file":
                # Validate configuration file
                file_path = validation.get("file_path")
                required_settings = validation.get("required_settings", [])

                if not file_path:
                    configuration_results[validation_name] = {
                        "status": "ERROR",
                        "type": validation_type,
                        "message": "No file path specified",
                    }
                    continue

                status, details = self._validate_config_file(
                    file_path, required_settings
                )
                configuration_results[validation_name] = {
                    "status": status,
                    "type": validation_type,
                    "file_path": file_path,
                    **details,
                }

            elif validation_type == "env":
                # Validate environment variables
                required_vars = validation.get("required_vars", [])

                status, details = self._validate_env_vars(required_vars)
                configuration_results[validation_name] = {
                    "status": status,
                    "type": validation_type,
                    **details,
                }

            elif validation_type == "command":
                # Validate using command
                command = validation.get("command")
                expected_exit_code = validation.get("expected_exit_code", 0)
                timeout = validation.get("timeout", 30)

                if not command:
                    configuration_results[validation_name] = {
                        "status": "ERROR",
                        "type": validation_type,
                        "message": "No command specified",
                    }
                    continue

                status, details = self._validate_command(
                    command, expected_exit_code, timeout
                )
                configuration_results[validation_name] = {
                    "status": status,
                    "type": validation_type,
                    "command": command,
                    **details,
                }

            else:
                configuration_results[validation_name] = {
                    "status": "ERROR",
                    "type": validation_type,
                    "message": f"Unsupported validation type: {validation_type}",
                }

        self.results["validations"]["configurations"] = configuration_results

    def _validate_config_file(
        self, file_path: str, required_settings: List[Dict]
    ) -> Tuple[str, Dict]:
        """Validate configuration file"""
        try:
            if not os.path.exists(file_path):
                return "FAIL", {"message": f"Configuration file not found: {file_path}"}

            # Determine file type from extension
            file_ext = os.path.splitext(file_path)[1].lower()

            # Load configuration file
            config_data = None
            if file_ext in [".yaml", ".yml"]:
                with open(file_path, "r") as f:
                    config_data = yaml.safe_load(f)
            elif file_ext == ".json":
                with open(file_path, "r") as f:
                    config_data = json.load(f)
            elif file_ext in [".ini", ".conf", ".cfg"]:
                # Simple parsing for INI-style files
                config_data = {}
                current_section = None
                with open(file_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith(";"):
                            continue
                        if line.startswith("[") and line.endswith("]"):
                            current_section = line[1:-1]
                            config_data[current_section] = {}
                        elif "=" in line:
                            key, value = line.split("=", 1)
                            if current_section:
                                config_data[current_section][
                                    key.strip()
                                ] = value.strip()
                            else:
                                config_data[key.strip()] = value.strip()
            else:
                # For other file types, just read as text
                with open(file_path, "r") as f:
                    content = f.read()
                config_data = {"content": content}

            # Check required settings
            missing_settings = []
            invalid_settings = []

            for setting in required_settings:
                path = setting.get("path", "")
                expected_value = setting.get("value")
                expected_type = setting.get("type")

                # Get actual value using path
                actual_value = self._get_value_by_path(config_data, path)

                if actual_value is None:
                    missing_settings.append(path)
                    continue

                # Check type if specified
                if expected_type:
                    type_valid = False
                    if expected_type == "string" and isinstance(actual_value, str):
                        type_valid = True
                    elif expected_type == "number" and isinstance(
                        actual_value, (int, float)
                    ):
                        type_valid = True
                    elif expected_type == "boolean" and isinstance(actual_value, bool):
                        type_valid = True
                    elif expected_type == "array" and isinstance(actual_value, list):
                        type_valid = True
                    elif expected_type == "object" and isinstance(actual_value, dict):
                        type_valid = True

                    if not type_valid:
                        invalid_settings.append(
                            f"{path} (expected type: {expected_type})"
                        )
                        continue

                # Check value if specified
                if expected_value is not None and actual_value != expected_value:
                    invalid_settings.append(
                        f"{path} (expected: {expected_value}, actual: {actual_value})"
                    )

            if missing_settings or invalid_settings:
                return "FAIL", {
                    "message": "Configuration validation failed",
                    "missing_settings": missing_settings,
                    "invalid_settings": invalid_settings,
                }
            else:
                return "PASS", {
                    "message": "Configuration validation passed",
                    "settings_checked": len(required_settings),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating configuration file: {str(e)}"
            }

    def _get_value_by_path(self, data: Any, path: str) -> Any:
        """Get value from nested data structure using dot notation path"""
        if not path:
            return data

        parts = path.split(".")
        current = data

        for part in parts:
            # Handle array indices
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str[:-1])

                if key:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return None

                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

        return current

    def _validate_env_vars(self, required_vars: List[Dict]) -> Tuple[str, Dict]:
        """Validate environment variables"""
        try:
            missing_vars = []
            invalid_vars = []

            for var in required_vars:
                name = var.get("name", "")
                expected_value = var.get("value")

                if not name:
                    continue

                # Check if variable exists
                if name not in os.environ:
                    missing_vars.append(name)
                    continue

                # Check value if specified
                if expected_value is not None and os.environ[name] != expected_value:
                    invalid_vars.append(f"{name} (expected: {expected_value})")

            if missing_vars or invalid_vars:
                return "FAIL", {
                    "message": "Environment variables validation failed",
                    "missing_vars": missing_vars,
                    "invalid_vars": invalid_vars,
                }
            else:
                return "PASS", {
                    "message": "Environment variables validation passed",
                    "vars_checked": len(required_vars),
                }
        except Exception as e:
            return "ERROR", {
                "message": f"Error validating environment variables: {str(e)}"
            }

    def _calculate_overall_status(self) -> None:
        """Calculate overall status based on validation results"""
        status_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "UNKNOWN": 0}

        # Count statuses from all validations
        for category, validations in self.results["validations"].items():
            if isinstance(validations, dict):
                for validation_name, validation_data in validations.items():
                    if (
                        isinstance(validation_data, dict)
                        and "status" in validation_data
                    ):
                        status = validation_data["status"]
                        status_counts[status] = status_counts.get(status, 0) + 1

        # Determine overall status
        if status_counts["ERROR"] > 0:
            self.results["status"] = "ERROR"
        elif status_counts["FAIL"] > 0:
            self.results["status"] = "FAIL"
        elif status_counts["UNKNOWN"] > 0:
            self.results["status"] = "WARN"
        else:
            self.results["status"] = "PASS"

        # Add summary
        self.results["summary"] = {
            "total_validations": sum(status_counts.values()),
            "status_counts": status_counts,
        }

    def _perform_rollback(self) -> None:
        """Perform rollback if validation failed"""
        logger.info("Performing rollback due to validation failures")

        deployment_config = self.config["environments"][self.env].get("deployment", {})
        rollback_command = deployment_config.get("rollback_command")

        if not rollback_command:
            logger.warning("No rollback command specified in configuration")
            self.results["rollback"] = {
                "status": "WARN",
                "message": "No rollback command specified in configuration",
            }
            return

        try:
            logger.info(f"Executing rollback command: {rollback_command}")
            process = subprocess.run(
                rollback_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout for rollback
            )

            if process.returncode == 0:
                logger.info("Rollback completed successfully")
                self.results["rollback"] = {
                    "status": "PASS",
                    "message": "Rollback completed successfully",
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                }
            else:
                logger.error(f"Rollback failed with exit code {process.returncode}")
                self.results["rollback"] = {
                    "status": "FAIL",
                    "message": f"Rollback failed with exit code {process.returncode}",
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                }
        except subprocess.TimeoutExpired:
            logger.error("Rollback command timed out")
            self.results["rollback"] = {
                "status": "FAIL",
                "message": "Rollback command timed out after 300 seconds",
            }
        except Exception as e:
            logger.error(f"Error performing rollback: {str(e)}")
            self.results["rollback"] = {
                "status": "ERROR",
                "message": f"Error performing rollback: {str(e)}",
            }

    def generate_report(
        self, format: str = "text", output_path: Optional[str] = None
    ) -> str:
        """Generate a report of the validation results"""
        if format == "json":
            report = json.dumps(self.results, indent=2)
        elif format == "html":
            report = self._generate_html_report()
        else:  # text
            report = self._generate_text_report()

        if output_path:
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")

        return report

    def _generate_text_report(self) -> str:
        """Generate a text report"""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append(f"NEXORA DEPLOYMENT VALIDATION REPORT - {self.env.upper()}")
        lines.append(f"Date: {self.results['timestamp']}")
        lines.append(f"Status: {self.results['status']}")
        lines.append("=" * 80)

        # Deployment info
        if "deployment_info" in self.results:
            info = self.results["deployment_info"]
            lines.append("\nDEPLOYMENT INFORMATION:")
            lines.append(f"Name: {info.get('name', 'unknown')}")
            lines.append(f"Environment: {info.get('environment', 'unknown')}")
            lines.append(f"Expected Version: {info.get('expected_version', 'unknown')}")
            lines.append(f"Actual Version: {info.get('actual_version', 'unknown')}")
            lines.append(f"Timestamp: {info.get('timestamp', 'unknown')}")

        # Summary
        summary = self.results["summary"]
        lines.append("\nSUMMARY:")
        lines.append(f"Total validations: {summary['total_validations']}")
        for status, count in summary["status_counts"].items():
            lines.append(f"  {status}: {count}")

        # Detailed results
        for category, validations in self.results["validations"].items():
            if not validations:
                continue

            lines.append("\n" + "=" * 80)
            lines.append(f"{category.upper()} VALIDATIONS:")
            lines.append("-" * 80)

            if isinstance(validations, dict):
                for validation_name, validation_data in validations.items():
                    if (
                        isinstance(validation_data, dict)
                        and "status" in validation_data
                    ):
                        status = validation_data["status"]
                        message = validation_data.get("message", "No message")

                        lines.append(f"{validation_name}: {status}")
                        lines.append(f"  {message}")

                        # Add additional details
                        for key, value in validation_data.items():
                            if key not in ["status", "message"] and not isinstance(
                                value, (dict, list)
                            ):
                                lines.append(f"  {key}: {value}")

                        lines.append("")
            else:
                lines.append(f"{validations}")
                lines.append("")

        # Rollback info if present
        if "rollback" in self.results:
            rollback = self.results["rollback"]
            lines.append("\n" + "=" * 80)
            lines.append("ROLLBACK INFORMATION:")
            lines.append("-" * 80)
            lines.append(f"Status: {rollback.get('status', 'UNKNOWN')}")
            lines.append(f"Message: {rollback.get('message', 'No message')}")

            if "stdout" in rollback and rollback["stdout"]:
                lines.append("\nStandard Output:")
                lines.append(rollback["stdout"])

            if "stderr" in rollback and rollback["stderr"]:
                lines.append("\nStandard Error:")
                lines.append(rollback["stderr"])

        return "\n".join(lines)

    def _generate_html_report(self) -> str:
        """Generate an HTML report"""
        html = []

        # Header
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append(
            "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        )
        html.append("  <title>Nexora Deployment Validation Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("    h1, h2, h3 { color: #333; }")
        html.append("    .report-header { margin-bottom: 20px; }")
        html.append("    .status { font-weight: bold; }")
        html.append("    .status-PASS { color: green; }")
        html.append("    .status-FAIL { color: red; }")
        html.append("    .status-ERROR { color: darkred; }")
        html.append("    .status-WARN, .status-UNKNOWN { color: orange; }")
        html.append("    .status-INFO { color: blue; }")
        html.append(
            "    .validation { margin-bottom: 10px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }"
        )
        html.append(
            "    .validation-header { display: flex; justify-content: space-between; }"
        )
        html.append("    .validation-details { margin-top: 10px; }")
        html.append("    .validation-message { margin: 5px 0; }")
        html.append("    .summary { margin: 20px 0; }")
        html.append("    table { border-collapse: collapse; width: 100%; }")
        html.append(
            "    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
        )
        html.append("    th { background-color: #f2f2f2; }")
        html.append("    .category { margin-top: 30px; }")
        html.append(
            "    .toggle-btn { cursor: pointer; background: none; border: none; font-size: 16px; }"
        )
        html.append("    .deployment-info { margin: 20px 0; }")
        html.append("    .rollback-info { margin: 20px 0; }")
        html.append(
            "    pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }"
        )
        html.append("  </style>")
        html.append("  <script>")
        html.append("    function toggleDetails(id) {")
        html.append("      const details = document.getElementById(id);")
        html.append("      const btn = document.getElementById(id + '-btn');")
        html.append("      if (details.style.display === 'none') {")
        html.append("        details.style.display = 'block';")
        html.append("        btn.textContent = '▼';")
        html.append("      } else {")
        html.append("        details.style.display = 'none';")
        html.append("        btn.textContent = '►';")
        html.append("      }")
        html.append("    }")
        html.append("  </script>")
        html.append("</head>")
        html.append("<body>")

        # Report header
        html.append("  <div class='report-header'>")
        html.append(
            f"    <h1>Nexora Deployment Validation Report - {self.env.upper()}</h1>"
        )
        html.append(f"    <p><strong>Date:</strong> {self.results['timestamp']}</p>")
        html.append(
            f"    <p><strong>Status:</strong> <span class='status status-{self.results['status']}'>{self.results['status']}</span></p>"
        )
        html.append("  </div>")

        # Deployment info
        if "deployment_info" in self.results:
            info = self.results["deployment_info"]
            html.append("  <div class='deployment-info'>")
            html.append("    <h2>Deployment Information</h2>")
            html.append("    <table>")
            html.append(
                f"      <tr><th>Name</th><td>{info.get('name', 'unknown')}</td></tr>"
            )
            html.append(
                f"      <tr><th>Environment</th><td>{info.get('environment', 'unknown')}</td></tr>"
            )
            html.append(
                f"      <tr><th>Expected Version</th><td>{info.get('expected_version', 'unknown')}</td></tr>"
            )
            html.append(
                f"      <tr><th>Actual Version</th><td>{info.get('actual_version', 'unknown')}</td></tr>"
            )
            html.append(
                f"      <tr><th>Timestamp</th><td>{info.get('timestamp', 'unknown')}</td></tr>"
            )
            html.append("    </table>")
            html.append("  </div>")

        # Summary
        summary = self.results["summary"]
        html.append("  <div class='summary'>")
        html.append("    <h2>Summary</h2>")
        html.append("    <table>")
        html.append(
            "      <tr><th>Total Validations</th><td>"
            + str(summary["total_validations"])
            + "</td></tr>"
        )
        for status, count in summary["status_counts"].items():
            html.append(f"      <tr><th>{status}</th><td>{count}</td></tr>")
        html.append("    </table>")
        html.append("  </div>")

        # Detailed results
        validation_id = 0
        for category, validations in self.results["validations"].items():
            if not validations:
                continue

            html.append(f"  <div class='category'>")
            html.append(f"    <h2>{category.title()} Validations</h2>")

            if isinstance(validations, dict):
                for validation_name, validation_data in validations.items():
                    if (
                        isinstance(validation_data, dict)
                        and "status" in validation_data
                    ):
                        validation_id += 1
                        status = validation_data["status"]
                        message = validation_data.get("message", "No message")

                        html.append(f"    <div class='validation'>")
                        html.append(f"      <div class='validation-header'>")
                        html.append(f"        <h3>{validation_name}</h3>")
                        html.append(
                            f"        <span class='status status-{status}'>{status}</span>"
                        )
                        html.append(f"      </div>")
                        html.append(
                            f"      <div class='validation-message'>{message}</div>"
                        )

                        # Add toggle button for details
                        html.append(
                            f"      <button id='validation-{validation_id}-btn' class='toggle-btn' onclick=\"toggleDetails('validation-{validation_id}-details')\">▼</button>"
                        )

                        # Add additional details
                        html.append(
                            f"      <div id='validation-{validation_id}-details' class='validation-details'>"
                        )
                        for key, value in validation_data.items():
                            if key not in ["status", "message"]:
                                if isinstance(value, (dict, list)):
                                    html.append(
                                        f"        <div><strong>{key}:</strong> <pre>{json.dumps(value, indent=2)}</pre></div>"
                                    )
                                else:
                                    html.append(
                                        f"        <div><strong>{key}:</strong> {value}</div>"
                                    )
                        html.append("      </div>")
                        html.append("    </div>")
            else:
                html.append(f"    <div class='validation'>{validations}</div>")

            html.append("  </div>")

        # Rollback info if present
        if "rollback" in self.results:
            rollback = self.results["rollback"]
            html.append("  <div class='rollback-info'>")
            html.append("    <h2>Rollback Information</h2>")
            html.append("    <table>")
            html.append(
                f"      <tr><th>Status</th><td><span class='status status-{rollback.get('status', 'UNKNOWN')}'>{rollback.get('status', 'UNKNOWN')}</span></td></tr>"
            )
            html.append(
                f"      <tr><th>Message</th><td>{rollback.get('message', 'No message')}</td></tr>"
            )
            html.append("    </table>")

            if "stdout" in rollback and rollback["stdout"]:
                html.append("    <h3>Standard Output</h3>")
                html.append(f"    <pre>{rollback['stdout']}</pre>")

            if "stderr" in rollback and rollback["stderr"]:
                html.append("    <h3>Standard Error</h3>")
                html.append(f"    <pre>{rollback['stderr']}</pre>")

            html.append("  </div>")

        # Footer
        html.append("  <div class='footer'>")
        html.append("    <p>Generated by Nexora Deployment Validation Script</p>")
        html.append("  </div>")

        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Deployment Validation Script for Nexora",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1],
    )

    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        required=True,
        help="Target environment (dev, staging, prod)",
    )
    parser.add_argument(
        "--config",
        default="config/deployment_config.yaml",
        help="Path to config file (default: config/deployment_config.yaml)",
    )
    parser.add_argument("--output", help="Path to output report (default: stdout)")
    parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format (text, json, html) (default: text)",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send notifications on validation failures",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Automatically rollback failed deployments",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for validation checks in seconds (default: 300)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    try:
        # Initialize deployment validator
        validator = DeploymentValidator(
            config_path=args.config,
            env=args.env,
            timeout=args.timeout,
            rollback=args.rollback,
            verbose=args.verbose,
        )

        # Run validations
        results = validator.run_all_validations()

        # Generate report
        report = validator.generate_report(format=args.format, output_path=args.output)

        # Print report if not saving to file
        if not args.output:
            print(report)

        # Send notifications if enabled and validations failed
        if args.notify and results["status"] in ["FAIL", "ERROR"]:
            # Notification logic would go here
            # This could be email, Slack, etc.
            logger.info("Notifications would be sent (not implemented)")

        # Return exit code based on status
        if results["status"] == "PASS":
            return 0
        elif results["status"] == "WARN":
            return 1
        else:  # FAIL or ERROR
            return 2

    except Exception as e:
        logger.error(f"Error running deployment validation: {str(e)}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
