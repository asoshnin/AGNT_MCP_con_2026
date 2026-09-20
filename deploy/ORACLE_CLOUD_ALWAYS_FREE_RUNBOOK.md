# Oracle Cloud "Always Free" Production Runbook
## Zero-Cost, Permanent Hosting & Anti-Reclamation Guide

This runbook provides the definitive, battle-tested procedure for hosting the **AGNTCon + MCPCon Europe 2026 Intelligence Hub** on Oracle Cloud Infrastructure (OCI).

Follow this guide to guarantee two critical outcomes:
1. **You are NEVER charged a single cent ($0.00 / month forever).**
2. **Your instance is NEVER shut down, stopped, or reclaimed due to inactivity.**

---

## 🏛️ The Three Golden Invariants

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Zero-Cost Envelope: Stay strictly within 4 OCPU, 24 GB RAM, and 200 GB boot volume.       │
│ 2. Permanent Anti-Reclamation: Upgrade to Pay-As-You-Go (PAYG) for official exemption.      │
│ 3. Zero Inbound Attack Surface: Cloudflare Tunnel routes traffic without open firewall ports.│
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Account Creation & Hard Cost Guards

### Step 1.1: Sign Up for Oracle Cloud Free Tier
1. Go to [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/).
2. Select your **Home Region** carefully. 
   - *Recommendation:* Choose a major metropolitan datacenter near you or your target audience (e.g. `Frankfurt`, `Amsterdam`, `London`, `Ashburn`, or `San Jose`).
   - *Note:* You cannot change your home region later. Free-tier resources are provisioned in your home region.
3. Complete identity verification. Oracle requires a valid credit/debit card to prevent fraud and bot abuse. Oracle performs a temporary pre-authorization hold (~$1.00 USD) that is immediately reversed.

### Step 1.2: Set Up a $0.01 Hard Budget Alert (Cost Guardrail)
To guarantee you are never surprised by unexpected costs:
1. In the OCI Console, open the hamburger menu (≡) $\to$ **Billing & Cost Management** $\to$ **Budgets**.
2. Click **Create Budget**:
   - **Scope:** Tenancy
   - **Target Amount:** `$1.00`
   - **Threshold Type:** Absolute amount (`$0.01` or 1%)
   - **Alert Type:** Actual Spend
   - **Email Recipients:** Your personal email
3. If any billable resource is ever accidentally created, you will receive an immediate automated email warning before incurring material charges.

---

## Part 2: The Critical Invariant — Permanent Anti-Reclamation (PAYG Protocol)

### Why Oracle Reclaims Free Instances
In 2023, Oracle implemented an automated reclamation policy for **standard Free Trial / Free Tier** accounts:
> If an instance has less than 20% CPU utilization, less than 20% memory utilization, and less than 20% network traffic over a 7-day period, Oracle classifies it as "Idle" and shuts down or reclaims it.

### The Official Fix: Upgrade to Pay-As-You-Go (PAYG)
Oracle's official documentation explicitly specifies:
> **"Tenancies with Pay-As-You-Go (PAYG) status are 100% exempt from idle instance reclamation."**

When you upgrade your tenancy to PAYG:
1. **You keep all Always Free resource entitlements forever.**
2. **Oracle will NEVER charge you as long as you remain within the Always Free limits.**
3. **Your compute instances will NEVER be stopped or reclaimed due to inactivity.**
4. Oracle re-authorizes your credit card with a temporary hold (~$100 USD) which is automatically released within 24–72 hours. Your monthly bill remains **$0.00**.

#### How to Upgrade:
1. In the OCI Console, open the hamburger menu (≡) $\to$ **Billing & Cost Management** $\to$ **Payment Information** (or **Upgrade to Paid**).
2. Choose **Pay As You Go** (PAYG).
3. Confirm billing details and submit. Approval typically takes 1 to 24 hours.

---

## Part 3: Provisioning the "Always Free" Compute Instance

### Exact Resource Specification Table

| Setting | Exact Value to Select | Always Free Limit |
| :--- | :--- | :--- |
| **Name** | `agntcon-hub-prod` | N/A |
| **Placement** | Availability Domain 1 (or any available) | N/A |
| **Image** | **Canonical Ubuntu 24.04 LTS (aarch64)** | Always Free Eligible |
| **Shape** | **Ampere VM.Standard.A1.Flex** (ARM64) | Always Free Eligible |
| **OCPUs** | **2 OCPU** (or 4 OCPU max) | Up to 4 OCPU total |
| **Memory** | **12 GB RAM** (or 24 GB RAM max) | Up to 24 GB RAM total |
| **Networking** | Virtual Cloud Network (VCN) with public subnet | Always Free |
| **Boot Volume** | **100 GB** | Up to 200 GB total across tenancy |
| **SSH Keys** | Paste your public key (`~/.ssh/id_ed25519.pub`) | N/A |

### Provisioning Steps:
1. In OCI Console: **Compute** $\to$ **Instances** $\to$ **Create Instance**.
2. Under **Image and shape**:
   - Click **Change image** $\to$ Select **Canonical Ubuntu** $\to$ Version: **24.04 Minimal aarch64** (or standard 24.04 aarch64).
   - Click **Change shape** $\to$ Select **Ampere** $\to$ **VM.Standard.A1.Flex**.
   - Set Slider: **2 OCPUs** and **12 GB Memory** (this leaves 2 OCPUs and 12 GB free in your tenancy for future projects!).
3. Under **Networking**: Select "Create new virtual cloud network" and check "Assign a public IPv4 address".
4. Under **Add SSH keys**: Select "Upload public key files" and upload your public SSH key.
5. Under **Boot volume**: Check "Specify a custom boot volume size" and set to **100 GB**.
6. Click **Create**. The instance status will turn green (**Running**) in 60–90 seconds. Note its **Public IP Address**.

*(Note: If your chosen region reports "Out of capacity for shape VM.Standard.A1.Flex", see the troubleshooting section below).*

---

## Part 4: OS Hardening & Hub Installation

### Step 4.1: Connect via SSH
From your local terminal:
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<YOUR_INSTANCE_PUBLIC_IP>
```

### Step 4.2: Update System & Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl ufw fail2ban
```

### Step 4.3: Harden Host Firewall (UFW)
Because we route all public web traffic through an outbound Cloudflare Tunnel, we **close all inbound web ports**:
```bash
# Allow SSH so you don't lock yourself out
sudo ufw allow OpenSSH

# Enable firewall (rejects all other inbound ports)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

### Step 4.4: Deploy Hub Application
```bash
# 1. Clone repository to /opt/agntcon-hub
sudo git clone https://github.com/asoshnin/AGNT_MCP_con_2026.git /opt/agntcon-hub
sudo chown -R ubuntu:ubuntu /opt/agntcon-hub
cd /opt/agntcon-hub/02_public_hub

# 2. Create Python 3.12 Virtual Environment
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

# 3. Configure Production Environment
sudo mkdir -p /etc/agntcon-hub
sudo cp deploy/.env.production.example /etc/agntcon-hub/hub.env
sudo chmod 600 /etc/agntcon-hub/hub.env

# Generate a secure admin password and edit the file
openssl rand -hex 16
sudo nano /etc/agntcon-hub/hub.env
```

### Step 4.5: Enable Systemd Service
```bash
# Copy systemd unit file
sudo cp deploy/agntcon-hub.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now agntcon-hub

# Verify service is active and healthy
sudo systemctl status agntcon-hub
curl -s http://127.0.0.1:8088/api/queue-status
```
You should see: `{"active_tasks": 0, "waiting_tasks": 0, "max_concurrent": 2, "status": "ready"}`.

### Step 4.6: (Optional) Defense-in-Depth Anti-Idle Cron Job
If you have not yet completed the PAYG tenancy upgrade, set up the keepalive watchdog script:
```bash
# Add a cron job to generate a tiny 60s activity pulse every 6 hours
(crontab -l 2>/dev/null; echo "0 */6 * * * /opt/agntcon-hub/02_public_hub/deploy/scripts/oci_keepalive.sh >> /var/log/oci_keepalive.log 2>&1") | crontab -
```

---

## Part 5: Zero-Port Public Ingress via Cloudflare Tunnel

Cloudflare Tunnel (`cloudflared`) connects your Oracle Cloud VM to Cloudflare's global edge network via an **outbound-only connection**. You do NOT need to open port 80 or 443, and your server's IP address remains completely hidden.

### Step 5.1: Create Tunnel in Cloudflare Dashboard
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) $\to$ Select your domain.
2. In the left navigation, go to **Zero Trust** $\to$ **Networks** $\to$ **Tunnels**.
3. Click **Create a tunnel** $\to$ Select **Cloudflared** $\to$ Click **Next**.
4. Name your tunnel: `agntcon-europe-hub`.
5. Under **Install and run a connector**, select **Debian 64-bit (ARM64 / aarch64)**.
6. Copy the command provided by Cloudflare. It will look like:
   ```bash
   sudo cloudflared service install eyJhIjoi...<YOUR_TOKEN>...
   ```

### Step 5.2: Install on Your Oracle VM
Paste and run the command on your Oracle VM:
```bash
# Install cloudflared for ARM64 (Ampere)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb

# Install and run connector service using your token
sudo cloudflared service install <YOUR_TOKEN>
```
In the Cloudflare dashboard, the connector status will immediately show a green checkmark (**Active**).

### Step 5.3: Route Public Subdomain to Loopback
In Cloudflare Tunnel dashboard $\to$ **Public Hostnames** tab:
1. Click **Add a public hostname**.
2. **Subdomain:** `agntcon` (or `@` for apex domain).
3. **Domain:** Select your domain (e.g. `vwoosh.com`).
4. **Service Type:** `HTTP`
5. **URL:** `127.0.0.1:8088`
6. Under **Additional application settings** $\to$ **HTTP Settings**:
   - Check **HTTP2 support** (Enabled).
7. Click **Save hostname**.

---

## Part 6: Verification & Final Acceptance Test

Visit your live public URL (e.g. `https://agntcon.vwoosh.com`):
1. **SSL/TLS Check:** Verified lock icon with Cloudflare universal SSL.
2. **Search API Check:** Perform a search (e.g. `red teaming`) $\to$ Results render in <10ms.
3. **Chat Assistant Check:** Ask a question $\to$ Queue indicator updates and answer streams with grounded citations.
4. **Export Check:** Click `[📄 .pdf]` and `[⬇️ .md]` on the assistant answer $\to$ Exports download cleanly.
5. **Admin Access:** Navigate to `/admin` $\to$ Log in with your `ADMIN_PASSWORD`.

---

## 🛠️ Operational Cheat Sheet & Maintenance

```bash
# View live application logs
sudo journalctl -u agntcon-hub -f

# Restart application
sudo systemctl restart agntcon-hub

# Update application to latest Git version
cd /opt/agntcon-hub && git pull origin main
sudo systemctl restart agntcon-hub

# Backup SQLite CRM and Index
tar -czvf ~/agntcon_backup_$(date +%F).tar.gz /opt/agntcon-hub/02_public_hub/data/
```

---

## ❓ Troubleshooting

### "Out of capacity for shape VM.Standard.A1.Flex"
- **Cause:** Oracle Cloud sometimes experiences temporary demand spikes for Ampere ARM64 cores in specific regions.
- **Solution 1:** Upgrading to **Pay-As-You-Go (PAYG)** gives your account higher provisioning priority over free trial accounts.
- **Solution 2:** Try provisioning with 2 OCPU and 12 GB RAM instead of the maximum 4 OCPU / 24 GB.
- **Solution 3 (Fallback):** If immediate provisioning is needed, provision an Always Free **AMD instance** (`VM.Standard.E2.1.Micro` - 1 OCPU, 1 GB RAM, x86_64). Our public hub is so lightweight it runs smoothly on 1 GB RAM!
