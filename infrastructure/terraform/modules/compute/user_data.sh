#!/bin/bash

# Enhanced user data script for ${app_name} ${environment} instances
# This script includes security hardening and compliance configurations

set -euo pipefail

# Variables
APP_NAME="${app_name}"
ENVIRONMENT="${environment}"
REGION="${region}"
KMS_KEY_ID="${kms_key_id}"
LOG_GROUP="/aws/ec2/$APP_NAME-$ENVIRONMENT"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/user-data.log
}

log "Starting user data script for $APP_NAME $ENVIRONMENT instance"

# Update system packages
log "Updating system packages"
yum update -y

# Install essential packages
log "Installing essential packages"
yum install -y \
    awscli \
    amazon-cloudwatch-agent \
    amazon-ssm-agent \
    docker \
    git \
    htop \
    jq \
    unzip \
    wget \
    yum-utils

# Configure CloudWatch agent
log "Configuring CloudWatch agent"
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "$LOG_GROUP",
                        "log_stream_name": "{instance_id}/var/log/messages",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/secure",
                        "log_group_name": "$LOG_GROUP",
                        "log_stream_name": "{instance_id}/var/log/secure",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/user-data.log",
                        "log_group_name": "$LOG_GROUP",
                        "log_stream_name": "{instance_id}/var/log/user-data",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/docker",
                        "log_group_name": "$LOG_GROUP",
                        "log_stream_name": "{instance_id}/var/log/docker",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "CWAgent",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
log "Starting CloudWatch agent"
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s

# Configure and start SSM agent
log "Configuring SSM agent"
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Security hardening
log "Applying security hardening"

# Disable root login
sed -i 's/^#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Disable password authentication (key-based only)
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Configure SSH security
echo "Protocol 2" >> /etc/ssh/sshd_config
echo "MaxAuthTries 3" >> /etc/ssh/sshd_config
echo "ClientAliveInterval 300" >> /etc/ssh/sshd_config
echo "ClientAliveCountMax 2" >> /etc/ssh/sshd_config

# Restart SSH service
systemctl restart sshd

# Configure firewall (iptables)
log "Configuring firewall"
iptables -F
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables-save > /etc/sysconfig/iptables

# Enable and configure fail2ban
log "Installing and configuring fail2ban"
amazon-linux-extras install epel -y
yum install -y fail2ban

cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/secure
maxretry = 3
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure Docker with security settings
log "Configuring Docker"
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Configure Docker daemon with security options
cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "awslogs",
    "log-opts": {
        "awslogs-group": "$LOG_GROUP",
        "awslogs-region": "$REGION",
        "awslogs-stream-prefix": "docker"
    },
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true
}
EOF

systemctl restart docker

# Set up log rotation
log "Configuring log rotation"
cat > /etc/logrotate.d/application << EOF
/var/log/application/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ec2-user ec2-user
}
EOF

# Create application directories
log "Creating application directories"
mkdir -p /opt/app
mkdir -p /var/log/application
chown ec2-user:ec2-user /opt/app
chown ec2-user:ec2-user /var/log/application

# Mount additional EBS volume
log "Mounting additional EBS volume"
while [ ! -e /dev/xvdf ]; do
    log "Waiting for EBS volume to be attached..."
    sleep 5
done

# Format and mount the additional volume
if ! blkid /dev/xvdf; then
    log "Formatting additional EBS volume"
    mkfs.ext4 /dev/xvdf
fi

mkdir -p /data
mount /dev/xvdf /data
chown ec2-user:ec2-user /data

# Add to fstab for persistent mounting
echo "/dev/xvdf /data ext4 defaults,nofail 0 2" >> /etc/fstab

# Install and configure AWS Inspector agent
log "Installing AWS Inspector agent"
wget https://inspector-agent.amazonaws.com/linux/latest/install
bash install

# Configure automatic security updates
log "Configuring automatic security updates"
yum install -y yum-cron
sed -i 's/update_cmd = default/update_cmd = security/' /etc/yum/yum-cron.conf
sed -i 's/apply_updates = no/apply_updates = yes/' /etc/yum/yum-cron.conf
systemctl enable yum-cron
systemctl start yum-cron

# Install and configure AIDE (Advanced Intrusion Detection Environment)
log "Installing and configuring AIDE"
yum install -y aide
aide --init
mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Create AIDE check script
cat > /usr/local/bin/aide-check.sh << 'EOF'
#!/bin/bash
/usr/sbin/aide --check
if [ $? -ne 0 ]; then
    echo "AIDE detected file system changes" | logger -t aide
fi
EOF

chmod +x /usr/local/bin/aide-check.sh

# Add AIDE to cron for daily checks
echo "0 2 * * * root /usr/local/bin/aide-check.sh" >> /etc/crontab

# Configure system auditing with auditd
log "Configuring system auditing"
systemctl enable auditd
systemctl start auditd

# Add audit rules for financial compliance
cat >> /etc/audit/rules.d/audit.rules << EOF
# Monitor file access
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k identity

# Monitor system calls
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change

# Monitor network configuration
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/sysconfig/network -p wa -k system-locale

# Monitor login/logout events
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# Monitor process and session initiation
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session
EOF

# Restart auditd to apply new rules
service auditd restart

# Create health check endpoint
log "Creating health check endpoint"
cat > /opt/app/health-check.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
from datetime import datetime

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                # Basic health checks
                health_status = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "checks": {
                        "disk_space": self.check_disk_space(),
                        "memory": self.check_memory(),
                        "docker": self.check_docker(),
                        "services": self.check_services()
                    }
                }
                
                # Determine overall status
                all_healthy = all(check["status"] == "ok" for check in health_status["checks"].values())
                if not all_healthy:
                    health_status["status"] = "unhealthy"
                
                self.send_response(200 if all_healthy else 503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(health_status).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def check_disk_space(self):
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                usage = lines[1].split()[4].rstrip('%')
                return {"status": "ok" if int(usage) < 90 else "warning", "usage": f"{usage}%"}
        except:
            pass
        return {"status": "error", "message": "Unable to check disk space"}
    
    def check_memory(self):
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
            available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1])
            usage = ((total - available) / total) * 100
            return {"status": "ok" if usage < 90 else "warning", "usage": f"{usage:.1f}%"}
        except:
            pass
        return {"status": "error", "message": "Unable to check memory"}
    
    def check_docker(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', 'docker'], capture_output=True, text=True)
            status = result.stdout.strip()
            return {"status": "ok" if status == "active" else "error", "service_status": status}
        except:
            pass
        return {"status": "error", "message": "Unable to check Docker status"}
    
    def check_services(self):
        services = ['amazon-ssm-agent', 'amazon-cloudwatch-agent']
        service_status = {}
        all_ok = True
        
        for service in services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True)
                status = result.stdout.strip()
                service_status[service] = status
                if status != "active":
                    all_ok = False
            except:
                service_status[service] = "error"
                all_ok = False
        
        return {"status": "ok" if all_ok else "error", "services": service_status}

if __name__ == "__main__":
    PORT = 80
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        print(f"Health check server running on port {PORT}")
        httpd.serve_forever()
EOF

chmod +x /opt/app/health-check.py

# Create systemd service for health check
cat > /etc/systemd/system/health-check.service << EOF
[Unit]
Description=Health Check Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/app
ExecStart=/usr/bin/python3 /opt/app/health-check.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable health-check
systemctl start health-check

# Final security configurations
log "Applying final security configurations"

# Set proper file permissions
chmod 600 /etc/ssh/sshd_config
chmod 644 /etc/passwd
chmod 644 /etc/group
chmod 000 /etc/shadow
chmod 000 /etc/gshadow

# Disable unnecessary services
systemctl disable postfix 2>/dev/null || true
systemctl stop postfix 2>/dev/null || true

# Configure kernel parameters for security
cat >> /etc/sysctl.conf << EOF
# Network security
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.ip_forward = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
EOF

sysctl -p

# Signal completion
log "User data script completed successfully"

# Send completion signal to CloudFormation (if needed)
# /opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${AWS::Region}

exit 0

