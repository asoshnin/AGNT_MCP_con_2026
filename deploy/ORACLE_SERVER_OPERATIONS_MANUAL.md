---
title: "Oracle Cloud — Always Free Server Operations & Maintenance Manual"
date: 2026-09-21
updated: 2026-09-21
tags:
  - infrastructure
  - devops
  - oracle-cloud
  - sysadmin
  - linux
  - mcp-gateway
  - cloudflare
  - vwoosh
server_name: "agntcon-hub-prod"
public_ip: "84.235.169.106"
private_ip: "10.0.0.103"
region: "eu-amsterdam-1"
os: "Ubuntu 24.04.4 LTS (Noble Numbat) aarch64"
shape: "VM.Standard.A1.Flex (Ampere ARM)"
specs: "1 OCPU / 6 GB RAM / 46.6 GB Disk"
monthly_cost: "€0.00 (Always Free Eligible)"
tenancy: "asoshnin (root) / Medixspace"
---

# 🏛️ Oracle Cloud: Always Free Server Operations & Maintenance Manual
### Server Identity: `agntcon-hub-prod` (Amsterdam — `eu-amsterdam-1`)

> [!ABSTRACT] Executive Purpose
> This document is the definitive operational memo for the dedicated, permanently free cloud server hosting the **AGNTCon + MCPCon Europe 2026 Intelligence Hub & MCP Gateway**. It captures the exact steps, configurations, commands, and lessons learned during provisioning so that connecting, maintaining, updating, monitoring, and troubleshooting this machine requires **zero trial and error**.

---

## 📌 1. Server Hardware & Network Inventory

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SERVER METADATA & SPECIFICATION MATRIX                                                 │
├───────────────────────┬────────────────────────────────────────────────────────────────┤
│ Hostname              │ agntcon-hub-prod                                               │
│ Public IPv4           │ 84.235.169.106 (Ephemeral — 100% Free)                         │
│ Private IPv4          │ 10.0.0.103                                                     │
│ Cloud Region          │ eu-amsterdam-1 (Netherlands Northwest, Amsterdam)             │
│ Availability Domain   │ AD-1 (Fault Domain FD-3)                                       │
│ Tenancy Compartment   │ asoshnin (root) / Medixspace                                   │
│ Processor / Shape     │ Ampere Altra A1 (VM.Standard.A1.Flex, aarch64 ARM)             │
│ Compute Allocation    │ 1 OCPU (leaves 3 OCPU free in tenancy)                         │
│ Memory Allocation     │ 6.0 GB RAM (leaves 18 GB RAM free in tenancy)                  │
│ Boot Volume           │ 46.6 GB Balanced SSD (leaves 153.4 GB free in tenancy)         │
│ Bandwidth Cap         │ 1.0 Gbps (First 10 TB/month outbound is free)                  │
│ Operating System      │ Canonical Ubuntu 24.04.4 LTS Minimal (aarch64)                │
│ Python Environment    │ Python 3.12.3 (Native system binary)                           │
│ Default User          │ ubuntu (sudo authorized)                                       │
│ Billing Status        │ €0.00 / month forever (Always Free Eligible)                   │
└───────────────────────┴────────────────────────────────────────────────────────────────┘
```

> [!NOTE] Tenancy Resource Safety Margin
> Oracle Cloud Always Free provides **4 OCPUs, 24 GB RAM, and 200 GB storage**. 
> Because this instance uses only **1 OCPU, 6 GB RAM, and 46.6 GB disk**, your account retains **75% of its free compute quota completely untouched** for future workloads.

---

## 🔑 2. How to Connect & Access the Server

### 2.1 Direct SSH from Your ThinkPad (One-Liner)
The server is already configured with your local SSH public key (`~/.ssh/id_ed25519.pub`).

Open your terminal and run:
```bash
ssh ubuntu@84.235.169.106
```

### 2.2 Recommended SSH Client Configuration (`~/.ssh/config`)
To connect by simply typing `ssh oracle-agntcon`, add this block to your local `~/.ssh/config` file:

```sshconfig
Host oracle-agntcon
    HostName 84.235.169.106
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Now you can log in, copy files, or forward ports effortlessly:
```bash
# Direct login:
ssh oracle-agntcon

# Copy file to server:
scp ./myfile.tar.gz oracle-agntcon:/opt/agntcon-hub/

# Copy database from server to laptop:
scp oracle-agntcon:/opt/agntcon-hub/02_public_hub/data/crm.sqlite ./backup_crm.sqlite
```

### 2.3 Emergency Web Console Access (If SSH is Blocked)
If you ever accidentally lock the firewall or lose SSH connectivity:
1. Log in to the [Oracle Cloud Console](https://cloud.oracle.com/?region=eu-amsterdam-1).
2. Go to **Compute** $\to$ **Instances** $\to$ Click **`agntcon-hub-prod`**.
3. Under **Resources** (left menu), click **Console connection**.
4. Click **Launch Cloud Shell connection**.
5. This opens a native Linux serial tty inside your browser directly connected to the kernel.

---

## 🛠️ 3. How to Configure the Server (Initial Setup Playbook)

Run these commands once when setting up the server environment from scratch:

```bash
# 1. Update OS package repositories and upgrade existing packages
sudo apt update && sudo apt upgrade -y

# 2. Install essential system tools, Python virtual environment & firewall
sudo apt install -y git python3-venv curl ufw fail2ban htop

# 3. Configure UFW Host Firewall (Zero Inbound Web Ports)
# Cloudflare Tunnel connects strictly OUTBOUND; we only open SSH!
sudo ufw allow OpenSSH
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw --force enable

# 4. Clone Hub Repository into /opt/agntcon-hub
sudo git clone https://github.com/asoshnin/AGNT_MCP_con_2026.git /opt/agntcon-hub
sudo chown -R ubuntu:ubuntu /opt/agntcon-hub
cd /opt/agntcon-hub/02_public_hub

# 5. Create Python 3.12 Virtual Environment
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

# 6. Configure Production Environment File
sudo mkdir -p /etc/agntcon-hub
sudo cp deploy/.env.production.example /etc/agntcon-hub/hub.env
sudo chmod 600 /etc/agntcon-hub/hub.env

# 7. Install and start the Systemd Service Daemon
sudo cp deploy/agntcon-hub.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now agntcon-hub

# 8. Verify the local healthcheck responds with HTTP 200
curl -s http://127.0.0.1:8088/api/queue-status
```

---

## ⚡ 4. How to Run, Stop, Restart & Control the Service

The Hub is managed as a native Linux systemd background daemon (`agntcon-hub.service`).

```bash
# Check service status (Active / Inactive / Errors)
sudo systemctl status agntcon-hub

# Start service
sudo systemctl start agntcon-hub

# Stop service
sudo systemctl stop agntcon-hub

# Restart service (e.g. after code changes or git pull)
sudo systemctl restart agntcon-hub

# Disable autostart on system boot
sudo systemctl disable agntcon-hub

# Enable autostart on system boot
sudo systemctl enable agntcon-hub
```

> [!DANGER] Critical Invariant: Server Lifecycle in Oracle Console
> Inside the Oracle Cloud Console:
> - **Reboot / Soft Stop:** Safe.
> - **Stop (Deallocate):** Safe (you can start it again anytime).
> - **NEVER click "Terminate"** on the instance unless you intend to permanently destroy it. If you ever must terminate, ensure the checkbox *"Permanently delete the attached boot volume"* is **UNCHECKED** so your data is preserved.

---

## 📊 5. How to Monitor & Inspect the Server

### 5.1 Real-Time Application Logs
To watch incoming visitor queries, MCP tool calls, CRM submissions, and queue events in real time:
```bash
# Tail live systemd service logs
sudo journalctl -u agntcon-hub -f

# View the last 100 log lines
sudo journalctl -u agntcon-hub -n 100 --no-pager
```

### 5.2 Application Concurrency & Healthcheck
```bash
# Fast query queue state (< 2ms response)
curl -s http://127.0.0.1:8088/api/queue-status | jq .
```
Expected output:
```json
{
  "active_tasks": 0,
  "waiting_tasks": 0,
  "waiting_depth": 0,
  "queue_depth": 0,
  "max_concurrent": 2,
  "status": "ready"
}
```

### 5.3 System Hardware Health
```bash
# Check memory consumption:
free -h

# Check SSD disk utilization:
df -h /

# Interactive process manager:
htop
```

---

## 🔄 6. How to Maintain & Update the Hub

### 6.1 Deploying Code Updates from GitHub (Zero Downtime)
Whenever you push new improvements or features to `main` on GitHub:
```bash
cd /opt/agntcon-hub
git pull origin main
sudo systemctl restart agntcon-hub
sudo journalctl -u agntcon-hub -n 20 --no-pager
```

### 6.2 Backing Up the Live SQLite Databases
The live database files live in `/opt/agntcon-hub/02_public_hub/data/`:
- `crm.sqlite` (Speaker feedback, collaboration inquiries, ticket status)
- `agntcon2026.sqlite` (Full conference search index and vector embeddings)

To take an instant compressed snapshot:
```bash
# Create timestamped local backup on the server:
tar -czvf ~/agntcon_data_backup_$(date +%F_%H%M).tar.gz -C /opt/agntcon-hub/02_public_hub data/

# Download backup directly to your laptop:
scp oracle-agntcon:~/agntcon_data_backup_*.tar.gz ~/Backups/
```

### 6.3 OS Security Patches
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 🛡️ 7. Permanent Anti-Idle & Anti-Reclamation Protocol

> [!WARNING] The Inactivity Trap Explained
> Oracle's automated bots scan **standard Free Trial / Free Tier** accounts. If CPU, memory, and network usage remain under 20% for 7 consecutive days, Oracle may mark the instance as "Idle" and reclaim it.

### The Two-Tier Protection Architecture:

#### Tier 1: The Official Oracle Exemption (Pay-As-You-Go Upgrade)
* **What it is:** Upgrading your Oracle tenancy account type to **Pay As You Go (PAYG)**.
* **Why it guarantees safety:** Oracle's official documentation states:
  > *"Tenancies with Pay-As-You-Go (PAYG) status are 100% exempt from idle instance reclamation."*
* **Does it cost anything?** **No. It remains €0.00/month.** As long as you stay within the Always Free limits (4 OCPU, 24 GB RAM, 200 GB disk), Oracle invoices you €0.00.
* **How to activate:**
  1. Open [Oracle Cloud Console](https://cloud.oracle.com/?region=eu-amsterdam-1).
  2. Navigate to **Billing & Cost Management** $\to$ **Upgrades and Payment**.
  3. Select **Pay As You Go (PAYG)** and submit.

#### Tier 2: The Defense-in-Depth Watchdog Script (`oci_keepalive.sh`)
If you have not yet completed the PAYG upgrade, activate our bundled synthetic keepalive watchdog:
```bash
# Add a gentle 60s CPU pulse every 6 hours to stay above the 7-day idle threshold
(crontab -l 2>/dev/null; echo "0 */6 * * * /opt/agntcon-hub/02_public_hub/deploy/scripts/oci_keepalive.sh >> /var/log/oci_keepalive.log 2>&1") | crontab -
```

---

## 🌐 8. Public Web Ingress via Cloudflare Tunnel (Zero Open Ports)

Instead of exposing port 80/443 directly to internet port scanners and DDoS attacks, we use an encrypted **outbound Cloudflare Tunnel (`cloudflared`)**.

```
[ Visitor Browser ] ──HTTPS──> [ Cloudflare Global Edge ] ──Encrypted Tunnel──> [ cloudflared on Server ] ──> [ 127.0.0.1:8088 ]
```

### Installation on `agntcon-hub-prod` (ARM64 Ampere):
```bash
# 1. Download official ARM64 deb package:
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb

# 2. Authenticate and register tunnel connector using token from Cloudflare Zero Trust:
sudo cloudflared service install <YOUR_CLOUDFLARE_TUNNEL_TOKEN>

# 3. Check connector status:
sudo systemctl status cloudflared
```

### In Cloudflare Zero Trust Dashboard:
1. Navigate to **Networks** $\to$ **Tunnels** $\to$ Select your tunnel.
2. Under **Public Hostname**:
   - **Subdomain:** `agntcon` (e.g. `agntcon.vwoosh.com`)
   - **Service Type:** `HTTP`
   - **URL:** `127.0.0.1:8088`
3. Click **Save Hostname**.
4. The site is instantly live with automatic SSL and DDoS mitigation!

---

## 🚨 9. Troubleshooting & Recovery Playbook

### Scenario A: "Permission denied (publickey)" when running SSH
* **Cause:** Wrong key selected, or permissions on local key file are too open.
* **Fix:**
  ```bash
  chmod 600 ~/.ssh/id_ed25519
  ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes ubuntu@84.235.169.106
  ```

### Scenario B: "Connection timed out" on port 22
* **Cause:** Public IP changed after a full instance deallocation, or UFW disabled SSH.
* **Fix:**
  1. Check the Oracle Cloud Console under **Compute** $\to$ **Instances** $\to$ **`agntcon-hub-prod`**.
  2. Verify that **Public IP address** is still `84.235.169.106`. If a different ephemeral IP was assigned after a hard shutdown, update your SSH command with the new IP.
  3. *(Optional Pro Tip)*: Under **IP administration**, you can convert the IP to a **Reserved Public IP** (free for active instances) so it never changes even across reboots.

### Scenario C: Hub returns HTTP 500 or won't start
* **Check logs:**
  ```bash
  sudo journalctl -u agntcon-hub -n 50 --no-pager
  ```
* **Common fix:** Port 8088 already bound by a stray process:
  ```bash
  sudo fuser -k 8088/tcp
  sudo systemctl restart agntcon-hub
  ```

### Scenario D: Cost estimator shows €0.57 in the Oracle Console
* **Explanation:** Oracle's calculator displays list prices before Always Free credits are deducted. Every tenancy receives **200 GB of free boot storage** every month. A 46.6 GB drive is 100% discounted on your actual monthly invoice, resulting in **€0.00**.

---

## 🎯 Quick Reference Cheat Sheet

| Task | Command |
| :--- | :--- |
| **Connect** | `ssh ubuntu@84.235.169.106` |
| **Service Status** | `sudo systemctl status agntcon-hub` |
| **Restart Service** | `sudo systemctl restart agntcon-hub` |
| **Watch Logs** | `sudo journalctl -u agntcon-hub -f` |
| **Queue Health** | `curl -s http://127.0.0.1:8088/api/queue-status` |
| **Check RAM** | `free -h` |
| **Check Disk** | `df -h /` |
| **Git Pull & Reload** | `cd /opt/agntcon-hub && git pull origin main && sudo systemctl restart agntcon-hub` |
