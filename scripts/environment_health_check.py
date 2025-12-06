"""
Environment Health Check Script for Nexora

This script performs comprehensive health checks on Nexora environments
(development, staging, production) to verify their operational status.
It checks system resources, service status, database connections, and API endpoints.

Usage:
    python environment_health_check.py --env [dev|staging|prod] [options]

Options:
    --env ENV               Target environment (dev, staging, prod)
    --config PATH           Path to config file (default: config/env_config.yaml)
    --output PATH           Path to output report (default: stdout)
    --format FORMAT         Output format (text, json, html) (default: text)
    --notify                Send notifications on failures
    --threshold PERCENT     Alert threshold for resource usage (default: 80)
    --verbose               Enable verbose output
    --help                  Show this help message

Examples:
    python environment_health_check.py --env dev
    python environment_health_check.py --env prod --format json --output health_report.json
    python environment_health_check.py --env staging --notify --threshold 75
"""

import argparse
import datetime
import json
import logging
import os
import platform
import socket
import subprocess
import sys
import time
from typing import Any, Dict, Optional, Tuple
import yaml
from core.logging import get_logger

logger = get_logger(__name__)
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
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
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
try:
    import kubernetes

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("environment_health_check")


class HealthCheck:
    """Main class for performing environment health checks"""

    def __init__(
        self, config_path: str, env: str, threshold: int = 80, verbose: bool = False
    ) -> Any:
        """
        Initialize the health check with configuration

        Args:
            config_path: Path to the configuration file
            env: Target environment (dev, staging, prod)
            threshold: Alert threshold for resource usage (percentage)
            verbose: Enable verbose output
        """
        self.config_path = config_path
        self.env = env
        self.threshold = threshold
        self.verbose = verbose
        self.config = self._load_config()
        self.results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "environment": env,
            "status": "UNKNOWN",
            "summary": {},
            "checks": {},
        }
        if verbose:
            logger.setLevel(logging.DEBUG)
        logger.info(f"Initializing health check for {env} environment")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                return {
                    "environments": {
                        self.env: {
                            "system": {
                                "min_memory_mb": 1024,
                                "min_disk_gb": 10,
                                "max_cpu_load": 90,
                            },
                            "services": [],
                            "databases": [],
                            "api_endpoints": [],
                            "kubernetes": {"enabled": False},
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

    def run_all_checks(self) -> Dict:
        """Run all health checks and return results"""
        logger.info("Starting health checks")
        self.check_system_resources()
        self.check_services()
        self.check_databases()
        self.check_api_endpoints()
        self.check_kubernetes()
        self._calculate_overall_status()
        logger.info(f"Health checks completed with status: {self.results['status']}")
        return self.results

    def check_system_resources(self) -> None:
        """Check system resources (CPU, memory, disk)"""
        logger.info("Checking system resources")
        system_checks = {}
        system_config = self.config["environments"][self.env].get("system", {})
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = (
                "PASS"
                if cpu_percent < system_config.get("max_cpu_load", 90)
                else "FAIL"
            )
            system_checks["cpu"] = {
                "status": cpu_status,
                "value": f"{cpu_percent}%",
                "threshold": f"{system_config.get('max_cpu_load', 90)}%",
                "message": f"CPU usage is {cpu_percent}%",
            }
        else:
            system_checks["cpu"] = {
                "status": "UNKNOWN",
                "message": "psutil not available for CPU check",
            }
        if PSUTIL_AVAILABLE:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_status = "PASS" if memory_percent < self.threshold else "FAIL"
            min_memory_mb = system_config.get("min_memory_mb", 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            memory_available_status = (
                "PASS" if memory_available_mb > min_memory_mb else "FAIL"
            )
            system_checks["memory_percent"] = {
                "status": memory_status,
                "value": f"{memory_percent}%",
                "threshold": f"{self.threshold}%",
                "message": f"Memory usage is {memory_percent}%",
            }
            system_checks["memory_available"] = {
                "status": memory_available_status,
                "value": f"{memory_available_mb:.2f} MB",
                "threshold": f"{min_memory_mb} MB",
                "message": f"Available memory is {memory_available_mb:.2f} MB",
            }
        else:
            system_checks["memory"] = {
                "status": "UNKNOWN",
                "message": "psutil not available for memory check",
            }
        if PSUTIL_AVAILABLE:
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_status = "PASS" if disk_percent < self.threshold else "FAIL"
            min_disk_gb = system_config.get("min_disk_gb", 10)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            disk_free_status = "PASS" if disk_free_gb > min_disk_gb else "FAIL"
            system_checks["disk_percent"] = {
                "status": disk_status,
                "value": f"{disk_percent}%",
                "threshold": f"{self.threshold}%",
                "message": f"Disk usage is {disk_percent}%",
            }
            system_checks["disk_free"] = {
                "status": disk_free_status,
                "value": f"{disk_free_gb:.2f} GB",
                "threshold": f"{min_disk_gb} GB",
                "message": f"Free disk space is {disk_free_gb:.2f} GB",
            }
        else:
            system_checks["disk"] = {
                "status": "UNKNOWN",
                "message": "psutil not available for disk check",
            }
        if hasattr(os, "getloadavg") and callable(getattr(os, "getloadavg")):
            try:
                load1, load5, load15 = os.getloadavg()
                cpu_count = os.cpu_count() or 1
                normalized_load = load5 / cpu_count * 100
                load_status = "PASS" if normalized_load < self.threshold else "FAIL"
                system_checks["load_average"] = {
                    "status": load_status,
                    "value": f"{load1:.2f}, {load5:.2f}, {load15:.2f}",
                    "normalized": f"{normalized_load:.2f}%",
                    "threshold": f"{self.threshold}%",
                    "message": f"System load average (1, 5, 15 min): {load1:.2f}, {load5:.2f}, {load15:.2f}",
                }
            except Exception as e:
                system_checks["load_average"] = {
                    "status": "ERROR",
                    "message": f"Error checking load average: {str(e)}",
                }
        system_checks["info"] = {
            "status": "INFO",
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "time": datetime.datetime.now().isoformat(),
        }
        self.results["checks"]["system"] = system_checks

    def check_services(self) -> None:
        """Check status of configured services"""
        logger.info("Checking services")
        services_config = self.config["environments"][self.env].get("services", [])
        service_checks = {}
        for service in services_config:
            service_name = service.get("name", "unknown")
            service_type = service.get("type", "process")
            logger.debug(f"Checking service: {service_name} (type: {service_type})")
            if service_type == "process":
                process_name = service.get("process_name")
                pid = service.get("pid")
                if process_name:
                    status, details = self._check_process_by_name(process_name)
                elif pid:
                    status, details = self._check_process_by_pid(pid)
                else:
                    status = "ERROR"
                    details = {"message": "No process_name or pid specified"}
                service_checks[service_name] = {
                    "status": status,
                    "type": "process",
                    **details,
                }
            elif service_type == "port":
                host = service.get("host", "localhost")
                port = service.get("port")
                if not port:
                    service_checks[service_name] = {
                        "status": "ERROR",
                        "type": "port",
                        "message": "No port specified",
                    }
                    continue
                status, details = self._check_port(host, port)
                service_checks[service_name] = {
                    "status": status,
                    "type": "port",
                    "host": host,
                    "port": port,
                    **details,
                }
            elif service_type == "http":
                url = service.get("url")
                method = service.get("method", "GET")
                expected_status = service.get("expected_status", 200)
                timeout = service.get("timeout", 10)
                headers = service.get("headers", {})
                if not url:
                    service_checks[service_name] = {
                        "status": "ERROR",
                        "type": "http",
                        "message": "No URL specified",
                    }
                    continue
                status, details = self._check_http_endpoint(
                    url, method, expected_status, timeout, headers
                )
                service_checks[service_name] = {
                    "status": status,
                    "type": "http",
                    "url": url,
                    **details,
                }
            elif service_type == "command":
                command = service.get("command")
                expected_exit_code = service.get("expected_exit_code", 0)
                timeout = service.get("timeout", 30)
                if not command:
                    service_checks[service_name] = {
                        "status": "ERROR",
                        "type": "command",
                        "message": "No command specified",
                    }
                    continue
                status, details = self._run_command(
                    command, expected_exit_code, timeout
                )
                service_checks[service_name] = {
                    "status": status,
                    "type": "command",
                    "command": command,
                    **details,
                }
            else:
                service_checks[service_name] = {
                    "status": "ERROR",
                    "type": service_type,
                    "message": f"Unsupported service type: {service_type}",
                }
        self.results["checks"]["services"] = service_checks

    def check_databases(self) -> None:
        """Check database connections"""
        logger.info("Checking databases")
        databases_config = self.config["environments"][self.env].get("databases", [])
        database_checks = {}
        for db in databases_config:
            db_name = db.get("name", "unknown")
            db_type = db.get("type", "unknown")
            logger.debug(f"Checking database: {db_name} (type: {db_type})")
            if db_type == "postgresql":
                if not POSTGRES_AVAILABLE:
                    database_checks[db_name] = {
                        "status": "ERROR",
                        "type": db_type,
                        "message": "psycopg2 not available for PostgreSQL check",
                    }
                    continue
                host = db.get("host", "localhost")
                port = db.get("port", 5432)
                database = db.get("database", "postgres")
                user = db.get("user", "postgres")
                password = db.get("password", "")
                ssl_mode = db.get("ssl_mode", "prefer")
                timeout = db.get("timeout", 5)
                status, details = self._check_postgresql(
                    host, port, database, user, password, ssl_mode, timeout
                )
                database_checks[db_name] = {
                    "status": status,
                    "type": db_type,
                    "host": host,
                    "port": port,
                    "database": database,
                    **details,
                }
            elif db_type == "mongodb":
                if not MONGODB_AVAILABLE:
                    database_checks[db_name] = {
                        "status": "ERROR",
                        "type": db_type,
                        "message": "pymongo not available for MongoDB check",
                    }
                    continue
                uri = db.get("uri")
                host = db.get("host", "localhost")
                port = db.get("port", 27017)
                database = db.get("database", "admin")
                user = db.get("user")
                password = db.get("password")
                timeout = db.get("timeout", 5)
                if uri:
                    status, details = self._check_mongodb_uri(uri, timeout)
                else:
                    status, details = self._check_mongodb(
                        host, port, database, user, password, timeout
                    )
                database_checks[db_name] = {
                    "status": status,
                    "type": db_type,
                    **(
                        {"uri": uri}
                        if uri
                        else {"host": host, "port": port, "database": database}
                    ),
                    **details,
                }
            elif db_type == "redis":
                if not REDIS_AVAILABLE:
                    database_checks[db_name] = {
                        "status": "ERROR",
                        "type": db_type,
                        "message": "redis-py not available for Redis check",
                    }
                    continue
                host = db.get("host", "localhost")
                port = db.get("port", 6379)
                db_index = db.get("db", 0)
                password = db.get("password")
                timeout = db.get("timeout", 5)
                status, details = self._check_redis(
                    host, port, db_index, password, timeout
                )
                database_checks[db_name] = {
                    "status": status,
                    "type": db_type,
                    "host": host,
                    "port": port,
                    "db": db_index,
                    **details,
                }
            else:
                database_checks[db_name] = {
                    "status": "ERROR",
                    "type": db_type,
                    "message": f"Unsupported database type: {db_type}",
                }
        self.results["checks"]["databases"] = database_checks

    def check_api_endpoints(self) -> None:
        """Check API endpoints"""
        logger.info("Checking API endpoints")
        if not REQUESTS_AVAILABLE:
            self.results["checks"]["api_endpoints"] = {
                "status": "ERROR",
                "message": "requests library not available for API endpoint checks",
            }
            return
        endpoints_config = self.config["environments"][self.env].get(
            "api_endpoints", []
        )
        endpoint_checks = {}
        for endpoint in endpoints_config:
            endpoint_name = endpoint.get("name", "unknown")
            url = endpoint.get("url")
            method = endpoint.get("method", "GET")
            headers = endpoint.get("headers", {})
            data = endpoint.get("data")
            expected_status = endpoint.get("expected_status", 200)
            timeout = endpoint.get("timeout", 10)
            content_check = endpoint.get("content_check")
            logger.debug(f"Checking API endpoint: {endpoint_name} ({url})")
            if not url:
                endpoint_checks[endpoint_name] = {
                    "status": "ERROR",
                    "message": "No URL specified",
                }
                continue
            status, details = self._check_api_endpoint(
                url, method, headers, data, expected_status, timeout, content_check
            )
            endpoint_checks[endpoint_name] = {
                "status": status,
                "url": url,
                "method": method,
                **details,
            }
        self.results["checks"]["api_endpoints"] = endpoint_checks

    def check_kubernetes(self) -> None:
        """Check Kubernetes resources if configured"""
        logger.info("Checking Kubernetes resources")
        k8s_config = self.config["environments"][self.env].get("kubernetes", {})
        if not k8s_config.get("enabled", False):
            logger.debug("Kubernetes checks not enabled")
            return
        if not K8S_AVAILABLE:
            self.results["checks"]["kubernetes"] = {
                "status": "ERROR",
                "message": "kubernetes library not available for Kubernetes checks",
            }
            return
        try:
            if k8s_config.get("in_cluster", False):
                kubernetes.config.load_incluster_config()
            else:
                kubernetes.config.load_kube_config(
                    config_file=k8s_config.get("config_file")
                )
            core_v1 = kubernetes.client.CoreV1Api()
            apps_v1 = kubernetes.client.AppsV1Api()
            namespace = k8s_config.get("namespace", "default")
            k8s_checks = {}
            if k8s_config.get("check_nodes", True):
                nodes_status, nodes_details = self._check_k8s_nodes(core_v1)
                k8s_checks["nodes"] = {"status": nodes_status, **nodes_details}
            if k8s_config.get("check_pods", True):
                pods_status, pods_details = self._check_k8s_pods(core_v1, namespace)
                k8s_checks["pods"] = {
                    "status": pods_status,
                    "namespace": namespace,
                    **pods_details,
                }
            if k8s_config.get("check_deployments", True):
                deployments_status, deployments_details = self._check_k8s_deployments(
                    apps_v1, namespace
                )
                k8s_checks["deployments"] = {
                    "status": deployments_status,
                    "namespace": namespace,
                    **deployments_details,
                }
            if k8s_config.get("check_services", True):
                services_status, services_details = self._check_k8s_services(
                    core_v1, namespace
                )
                k8s_checks["services"] = {
                    "status": services_status,
                    "namespace": namespace,
                    **services_details,
                }
            self.results["checks"]["kubernetes"] = k8s_checks
        except Exception as e:
            self.results["checks"]["kubernetes"] = {
                "status": "ERROR",
                "message": f"Error checking Kubernetes resources: {str(e)}",
            }

    def _check_process_by_name(self, process_name: str) -> Tuple[str, Dict]:
        """Check if a process is running by name"""
        if not PSUTIL_AVAILABLE:
            return ("ERROR", {"message": "psutil not available for process check"})
        try:
            processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                if process_name.lower() in proc.info["name"].lower() or (
                    proc.info["cmdline"]
                    and any(
                        (
                            process_name.lower() in cmd.lower()
                            for cmd in proc.info["cmdline"]
                        )
                    )
                ):
                    processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": (
                                " ".join(proc.info["cmdline"])
                                if proc.info["cmdline"]
                                else ""
                            ),
                        }
                    )
            if processes:
                return (
                    "PASS",
                    {
                        "message": f"Process '{process_name}' is running",
                        "processes": processes,
                    },
                )
            else:
                return ("FAIL", {"message": f"Process '{process_name}' is not running"})
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking process '{process_name}': {str(e)}"},
            )

    def _check_process_by_pid(self, pid: int) -> Tuple[str, Dict]:
        """Check if a process is running by PID"""
        if not PSUTIL_AVAILABLE:
            return ("ERROR", {"message": "psutil not available for process check"})
        try:
            process = psutil.Process(pid)
            return (
                "PASS",
                {
                    "message": f"Process with PID {pid} is running",
                    "name": process.name(),
                    "cmdline": " ".join(process.cmdline()) if process.cmdline() else "",
                },
            )
        except psutil.NoSuchProcess:
            return ("FAIL", {"message": f"Process with PID {pid} is not running"})
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking process with PID {pid}: {str(e)}"},
            )

    def _check_port(self, host: str, port: int) -> Tuple[str, Dict]:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return ("PASS", {"message": f"Port {port} on {host} is open"})
            else:
                return (
                    "FAIL",
                    {
                        "message": f"Port {port} on {host} is closed (error code: {result})"
                    },
                )
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking port {port} on {host}: {str(e)}"},
            )

    def _check_http_endpoint(
        self, url: str, method: str, expected_status: int, timeout: int, headers: Dict
    ) -> Tuple[str, Dict]:
        """Check HTTP endpoint"""
        if not REQUESTS_AVAILABLE:
            return (
                "ERROR",
                {"message": "requests library not available for HTTP check"},
            )
        try:
            start_time = time.time()
            response = requests.request(
                method=method, url=url, headers=headers, timeout=timeout
            )
            response_time = time.time() - start_time
            if response.status_code == expected_status:
                return (
                    "PASS",
                    {
                        "message": f"HTTP endpoint returned status {response.status_code}",
                        "status_code": response.status_code,
                        "response_time": f"{response_time:.3f}s",
                    },
                )
            else:
                return (
                    "FAIL",
                    {
                        "message": f"HTTP endpoint returned status {response.status_code}, expected {expected_status}",
                        "status_code": response.status_code,
                        "response_time": f"{response_time:.3f}s",
                    },
                )
        except requests.exceptions.Timeout:
            return (
                "FAIL",
                {"message": f"HTTP request to {url} timed out after {timeout}s"},
            )
        except requests.exceptions.ConnectionError:
            return ("FAIL", {"message": f"Connection error when connecting to {url}"})
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking HTTP endpoint {url}: {str(e)}"},
            )

    def _run_command(
        self, command: str, expected_exit_code: int, timeout: int
    ) -> Tuple[str, Dict]:
        """Run command and check exit code"""
        try:
            start_time = time.time()
            process = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            execution_time = time.time() - start_time
            if process.returncode == expected_exit_code:
                return (
                    "PASS",
                    {
                        "message": f"Command executed successfully with exit code {process.returncode}",
                        "exit_code": process.returncode,
                        "execution_time": f"{execution_time:.3f}s",
                        "stdout": process.stdout.strip(),
                        "stderr": process.stderr.strip(),
                    },
                )
            else:
                return (
                    "FAIL",
                    {
                        "message": f"Command failed with exit code {process.returncode}, expected {expected_exit_code}",
                        "exit_code": process.returncode,
                        "execution_time": f"{execution_time:.3f}s",
                        "stdout": process.stdout.strip(),
                        "stderr": process.stderr.strip(),
                    },
                )
        except subprocess.TimeoutExpired:
            return ("FAIL", {"message": f"Command timed out after {timeout}s"})
        except Exception as e:
            return ("ERROR", {"message": f"Error running command: {str(e)}"})

    def _check_postgresql(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        ssl_mode: str,
        timeout: int,
    ) -> Tuple[str, Dict]:
        """Check PostgreSQL connection"""
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
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT current_timestamp;")
            db_time = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            connection_time = time.time() - start_time
            return (
                "PASS",
                {
                    "message": "Successfully connected to PostgreSQL database",
                    "connection_time": f"{connection_time:.3f}s",
                    "version": version,
                    "db_time": str(db_time),
                },
            )
        except psycopg2.OperationalError as e:
            return (
                "FAIL",
                {"message": f"Failed to connect to PostgreSQL database: {str(e)}"},
            )
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking PostgreSQL database: {str(e)}"},
            )

    def _check_mongodb_uri(self, uri: str, timeout: int) -> Tuple[str, Dict]:
        """Check MongoDB connection using URI"""
        try:
            start_time = time.time()
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=timeout * 1000)
            server_info = client.server_info()
            connection_time = time.time() - start_time
            return (
                "PASS",
                {
                    "message": "Successfully connected to MongoDB database",
                    "connection_time": f"{connection_time:.3f}s",
                    "version": server_info.get("version", "unknown"),
                },
            )
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return (
                "FAIL",
                {"message": f"Failed to connect to MongoDB database: {str(e)}"},
            )
        except Exception as e:
            return ("ERROR", {"message": f"Error checking MongoDB database: {str(e)}"})

    def _check_mongodb(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        timeout: int,
    ) -> Tuple[str, Dict]:
        """Check MongoDB connection"""
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
            server_info = client.server_info()
            connection_time = time.time() - start_time
            return (
                "PASS",
                {
                    "message": "Successfully connected to MongoDB database",
                    "connection_time": f"{connection_time:.3f}s",
                    "version": server_info.get("version", "unknown"),
                },
            )
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return (
                "FAIL",
                {"message": f"Failed to connect to MongoDB database: {str(e)}"},
            )
        except Exception as e:
            return ("ERROR", {"message": f"Error checking MongoDB database: {str(e)}"})

    def _check_redis(
        self, host: str, port: int, db: int, password: str, timeout: int
    ) -> Tuple[str, Dict]:
        """Check Redis connection"""
        try:
            start_time = time.time()
            r = redis.Redis(
                host=host, port=port, db=db, password=password, socket_timeout=timeout
            )
            info = r.info()
            connection_time = time.time() - start_time
            return (
                "PASS",
                {
                    "message": "Successfully connected to Redis database",
                    "connection_time": f"{connection_time:.3f}s",
                    "version": info.get("redis_version", "unknown"),
                    "mode": (
                        "cluster" if info.get("cluster_enabled", 0) else "standalone"
                    ),
                },
            )
        except redis.exceptions.ConnectionError as e:
            return (
                "FAIL",
                {"message": f"Failed to connect to Redis database: {str(e)}"},
            )
        except Exception as e:
            return ("ERROR", {"message": f"Error checking Redis database: {str(e)}"})

    def _check_api_endpoint(
        self,
        url: str,
        method: str,
        headers: Dict,
        data: Any,
        expected_status: int,
        timeout: int,
        content_check: Optional[str],
    ) -> Tuple[str, Dict]:
        """Check API endpoint"""
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
            status_check = response.status_code == expected_status
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
            if status_check and content_check_result:
                return (
                    "PASS",
                    {
                        "message": f"API endpoint check passed",
                        "status_code": response.status_code,
                        "response_time": f"{response_time:.3f}s",
                        "content_check": content_check_message,
                    },
                )
            else:
                return (
                    "FAIL",
                    {
                        "message": f"API endpoint check failed",
                        "status_code": response.status_code,
                        "expected_status": expected_status,
                        "response_time": f"{response_time:.3f}s",
                        "content_check": content_check_message,
                    },
                )
        except requests.exceptions.Timeout:
            return (
                "FAIL",
                {"message": f"API request to {url} timed out after {timeout}s"},
            )
        except requests.exceptions.ConnectionError:
            return ("FAIL", {"message": f"Connection error when connecting to {url}"})
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking API endpoint {url}: {str(e)}"},
            )

    def _check_k8s_nodes(self, core_v1: Any) -> Tuple[str, Dict]:
        """Check Kubernetes nodes"""
        try:
            nodes = core_v1.list_node().items
            node_statuses = []
            not_ready_nodes = []
            for node in nodes:
                node_name = node.metadata.name
                node_status = "Unknown"
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        if condition.status == "True":
                            node_status = "Ready"
                        else:
                            node_status = "NotReady"
                            not_ready_nodes.append(node_name)
                node_statuses.append(
                    {
                        "name": node_name,
                        "status": node_status,
                        "kubelet_version": node.status.node_info.kubelet_version,
                        "os_image": node.status.node_info.os_image,
                    }
                )
            if not_ready_nodes:
                return (
                    "FAIL",
                    {
                        "message": f"{len(not_ready_nodes)} node(s) not ready: {', '.join(not_ready_nodes)}",
                        "nodes": node_statuses,
                        "total_nodes": len(nodes),
                        "ready_nodes": len(nodes) - len(not_ready_nodes),
                    },
                )
            else:
                return (
                    "PASS",
                    {
                        "message": f"All {len(nodes)} nodes are ready",
                        "nodes": node_statuses,
                        "total_nodes": len(nodes),
                        "ready_nodes": len(nodes),
                    },
                )
        except Exception as e:
            return ("ERROR", {"message": f"Error checking Kubernetes nodes: {str(e)}"})

    def _check_k8s_pods(self, core_v1: Any, namespace: str) -> Tuple[str, Dict]:
        """Check Kubernetes pods in namespace"""
        try:
            pods = core_v1.list_namespaced_pod(namespace).items
            pod_statuses = []
            not_running_pods = []
            for pod in pods:
                pod_name = pod.metadata.name
                pod_status = pod.status.phase
                pod_statuses.append(
                    {
                        "name": pod_name,
                        "status": pod_status,
                        "ready": self._is_pod_ready(pod),
                        "restarts": self._get_pod_restarts(pod),
                        "age": self._get_pod_age(pod),
                    }
                )
                if pod_status != "Running" or not self._is_pod_ready(pod):
                    not_running_pods.append(f"{pod_name} ({pod_status})")
            if not_running_pods:
                return (
                    "FAIL",
                    {
                        "message": f"{len(not_running_pods)} pod(s) not running: {', '.join(not_running_pods)}",
                        "pods": pod_statuses,
                        "total_pods": len(pods),
                        "running_pods": len(pods) - len(not_running_pods),
                    },
                )
            else:
                return (
                    "PASS",
                    {
                        "message": f"All {len(pods)} pods are running",
                        "pods": pod_statuses,
                        "total_pods": len(pods),
                        "running_pods": len(pods),
                    },
                )
        except Exception as e:
            return ("ERROR", {"message": f"Error checking Kubernetes pods: {str(e)}"})

    def _is_pod_ready(self, pod: Any) -> bool:
        """Check if a pod is ready"""
        if pod.status.phase != "Running":
            return False
        for container_status in pod.status.container_statuses:
            if not container_status.ready:
                return False
        return True

    def _get_pod_restarts(self, pod: Any) -> int:
        """Get total restarts for a pod"""
        restarts = 0
        for container_status in pod.status.container_statuses:
            restarts += container_status.restart_count
        return restarts

    def _get_pod_age(self, pod: Any) -> str:
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

    def _check_k8s_deployments(self, apps_v1: Any, namespace: str) -> Tuple[str, Dict]:
        """Check Kubernetes deployments in namespace"""
        try:
            deployments = apps_v1.list_namespaced_deployment(namespace).items
            deployment_statuses = []
            not_ready_deployments = []
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
                    }
                )
                if available_replicas != replicas:
                    not_ready_deployments.append(
                        f"{deployment_name} ({available_replicas}/{replicas} ready)"
                    )
            if not_ready_deployments:
                return (
                    "FAIL",
                    {
                        "message": f"{len(not_ready_deployments)} deployment(s) not ready: {', '.join(not_ready_deployments)}",
                        "deployments": deployment_statuses,
                        "total_deployments": len(deployments),
                        "ready_deployments": len(deployments)
                        - len(not_ready_deployments),
                    },
                )
            else:
                return (
                    "PASS",
                    {
                        "message": f"All {len(deployments)} deployments are ready",
                        "deployments": deployment_statuses,
                        "total_deployments": len(deployments),
                        "ready_deployments": len(deployments),
                    },
                )
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking Kubernetes deployments: {str(e)}"},
            )

    def _check_k8s_services(self, core_v1: Any, namespace: str) -> Tuple[str, Dict]:
        """Check Kubernetes services in namespace"""
        try:
            services = core_v1.list_namespaced_service(namespace).items
            service_statuses = []
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
                service_statuses.append(
                    {
                        "name": service_name,
                        "type": service_type,
                        "cluster_ip": cluster_ip,
                        "ports": ports,
                    }
                )
            return (
                "PASS",
                {
                    "message": f"Found {len(services)} services",
                    "services": service_statuses,
                    "total_services": len(services),
                },
            )
        except Exception as e:
            return (
                "ERROR",
                {"message": f"Error checking Kubernetes services: {str(e)}"},
            )

    def _calculate_overall_status(self) -> None:
        """Calculate overall status based on check results"""
        status_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "UNKNOWN": 0}
        for category, checks in self.results["checks"].items():
            if isinstance(checks, dict):
                for check_name, check_data in checks.items():
                    if isinstance(check_data, dict) and "status" in check_data:
                        status = check_data["status"]
                        status_counts[status] = status_counts.get(status, 0) + 1
        if status_counts["ERROR"] > 0:
            self.results["status"] = "ERROR"
        elif status_counts["FAIL"] > 0:
            self.results["status"] = "FAIL"
        elif status_counts["UNKNOWN"] > 0:
            self.results["status"] = "WARN"
        else:
            self.results["status"] = "PASS"
        self.results["summary"] = {
            "total_checks": sum(status_counts.values()),
            "status_counts": status_counts,
        }

    def generate_report(
        self, format: str = "text", output_path: Optional[str] = None
    ) -> str:
        """Generate a report of the health check results"""
        if format == "json":
            report = json.dumps(self.results, indent=2)
        elif format == "html":
            report = self._generate_html_report()
        else:
            report = self._generate_text_report()
        if output_path:
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")
        return report

    def _generate_text_report(self) -> str:
        """Generate a text report"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"NEXORA ENVIRONMENT HEALTH CHECK REPORT - {self.env.upper()}")
        lines.append(f"Date: {self.results['timestamp']}")
        lines.append(f"Status: {self.results['status']}")
        lines.append("=" * 80)
        summary = self.results["summary"]
        lines.append("\nSUMMARY:")
        lines.append(f"Total checks: {summary['total_checks']}")
        for status, count in summary["status_counts"].items():
            lines.append(f"  {status}: {count}")
        for category, checks in self.results["checks"].items():
            if not checks:
                continue
            lines.append("\n" + "=" * 80)
            lines.append(f"{category.upper()} CHECKS:")
            lines.append("-" * 80)
            if isinstance(checks, dict):
                for check_name, check_data in checks.items():
                    if isinstance(check_data, dict) and "status" in check_data:
                        status = check_data["status"]
                        message = check_data.get("message", "No message")
                        lines.append(f"{check_name}: {status}")
                        lines.append(f"  {message}")
                        for key, value in check_data.items():
                            if key not in ["status", "message"] and (
                                not isinstance(value, (dict, list))
                            ):
                                lines.append(f"  {key}: {value}")
                        lines.append("")
            else:
                lines.append(f"{checks}")
                lines.append("")
        return "\n".join(lines)

    def _generate_html_report(self) -> str:
        """Generate an HTML report"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append(
            "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        )
        html.append("  <title>Nexora Environment Health Check Report</title>")
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
            "    .check { margin-bottom: 10px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }"
        )
        html.append(
            "    .check-header { display: flex; justify-content: space-between; }"
        )
        html.append("    .check-details { margin-top: 10px; }")
        html.append("    .check-message { margin: 5px 0; }")
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
        html.append("  <div class='report-header'>")
        html.append(
            f"    <h1>Nexora Environment Health Check Report - {self.env.upper()}</h1>"
        )
        html.append(f"    <p><strong>Date:</strong> {self.results['timestamp']}</p>")
        html.append(
            f"    <p><strong>Status:</strong> <span class='status status-{self.results['status']}'>{self.results['status']}</span></p>"
        )
        html.append("  </div>")
        summary = self.results["summary"]
        html.append("  <div class='summary'>")
        html.append("    <h2>Summary</h2>")
        html.append("    <table>")
        html.append(
            "      <tr><th>Total Checks</th><td>"
            + str(summary["total_checks"])
            + "</td></tr>"
        )
        for status, count in summary["status_counts"].items():
            html.append(f"      <tr><th>{status}</th><td>{count}</td></tr>")
        html.append("    </table>")
        html.append("  </div>")
        check_id = 0
        for category, checks in self.results["checks"].items():
            if not checks:
                continue
            html.append(f"  <div class='category'>")
            html.append(f"    <h2>{category.title()} Checks</h2>")
            if isinstance(checks, dict):
                for check_name, check_data in checks.items():
                    if isinstance(check_data, dict) and "status" in check_data:
                        check_id += 1
                        status = check_data["status"]
                        message = check_data.get("message", "No message")
                        html.append(f"    <div class='check'>")
                        html.append(f"      <div class='check-header'>")
                        html.append(f"        <h3>{check_name}</h3>")
                        html.append(
                            f"        <span class='status status-{status}'>{status}</span>"
                        )
                        html.append(f"      </div>")
                        html.append(f"      <div class='check-message'>{message}</div>")
                        html.append(
                            f"""      <button id='check-{check_id}-btn' class='toggle-btn' onclick="toggleDetails('check-{check_id}-details')">▼</button>"""
                        )
                        html.append(
                            f"      <div id='check-{check_id}-details' class='check-details'>"
                        )
                        for key, value in check_data.items():
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
                html.append(f"    <div class='check'>{checks}</div>")
            html.append("  </div>")
        html.append("  <div class='footer'>")
        html.append("    <p>Generated by Nexora Environment Health Check Script</p>")
        html.append("  </div>")
        html.append("</body>")
        html.append("</html>")
        return "\n".join(html)


def parse_args() -> Any:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Environment Health Check Script for Nexora",
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
        default="config/env_config.yaml",
        help="Path to config file (default: config/env_config.yaml)",
    )
    parser.add_argument("--output", help="Path to output report (default: stdout)")
    parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format (text, json, html) (default: text)",
    )
    parser.add_argument(
        "--notify", action="store_true", help="Send notifications on failures"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Alert threshold for resource usage (default: 80)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    return parser.parse_args()


def main() -> Any:
    """Main entry point"""
    args = parse_args()
    try:
        health_check = HealthCheck(
            config_path=args.config,
            env=args.env,
            threshold=args.threshold,
            verbose=args.verbose,
        )
        results = health_check.run_all_checks()
        report = health_check.generate_report(
            format=args.format, output_path=args.output
        )
        if not args.output:
            logger.info(report)
        if args.notify and results["status"] in ["FAIL", "ERROR"]:
            logger.info("Notifications would be sent (not implemented)")
        if results["status"] == "PASS":
            return 0
        elif results["status"] == "WARN":
            return 1
        else:
            return 2
    except Exception as e:
        logger.error(f"Error running health check: {str(e)}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
