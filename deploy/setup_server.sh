#!/usr/bin/env bash
set -euo pipefail

echo "==> 1. Updating APT and installing baseline packages..."
sudo DEBIAN_FRONTEND=noninteractive apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git python3-venv python3-pip curl ufw fail2ban htop jq

echo "==> 2. Installing Cloudflared..."
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | sudo tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo DEBIAN_FRONTEND=noninteractive apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y cloudflared

echo "==> 3. Configuring UFW Host Firewall (SSH only)..."
sudo ufw allow 22/tcp
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw --force enable

echo "==> 4. Setting up /opt/agntcon-hub directory..."
sudo mkdir -p /opt/agntcon-hub
sudo chown -R ubuntu:ubuntu /opt/agntcon-hub

echo "==> Baseline provisioning complete!"
cloudflared --version
git --version
python3 --version
