# CVEBOT — Full Hosting Guide

This guide walks through deploying CVEBOT on the most common VPS and PaaS
platforms so the bot is always online and updates automatically whenever you
push to the `main` branch.

Every approach uses the same Docker image built by GitHub Actions
(`.github/workflows/docker-publish.yml`) and Watchtower for zero-touch updates.
If you haven't read the main [README](README.md) yet, start there for the
Discord Developer Portal setup.

---

## Table of contents

1. [Before you start — what you need everywhere](#before-you-start)
2. [OVH VPS](#ovh-vps)
3. [Hetzner Cloud](#hetzner-cloud)
4. [DigitalOcean Droplet](#digitalocean-droplet)
5. [AWS EC2 Free Tier](#aws-ec2-free-tier)
6. [Railway (free PaaS)](#railway-free-paas)
7. [Render (free PaaS)](#render-free-paas)
8. [Post-deploy checklist](#post-deploy-checklist)

---

## Before you start

Regardless of provider, you will need:

| Item | Where to get it |
|---|---|
| Discord bot token | [discord.com/developers/applications](https://discord.com/developers/applications) → your app → Bot → Reset Token |
| NVD API key (optional but recommended) | [nvd.nist.gov/developers/request-an-api-key](https://nvd.nist.gov/developers/request-an-api-key) |
| GitHub token (optional) | GitHub → Settings → Developer settings → Personal access tokens → Fine-grained, read-only public repos scope |

Keep these in a local `.env` file based on `.env.example`.  You will upload
this file (or paste the values as environment variables) on each provider.

---

## OVH VPS

OVH offers cheap VPS starting at ~€3–5/month (VPS Starter / VPS Value range).
The smallest plan is more than enough for this bot.

### 1 — Order a VPS

1. Go to [ovhcloud.com/en/vps](https://www.ovhcloud.com/en/vps/) and choose
   **VPS Starter** (1 vCPU, 2 GB RAM, 20 GB SSD) — this is overkill for the
   bot but the cheapest available.
2. Select the **Ubuntu 22.04** OS image.
3. Choose a region close to you (e.g. Gravelines for EU, Beauharnois for NA).
4. At checkout, choose SSH key authentication (recommended) or set a root
   password.
5. After the order is confirmed, OVH sends you an email with the server IP and
   your root credentials within a few minutes.

### 2 — First login & system update

```bash
ssh root@YOUR_OVH_IP
apt update && apt upgrade -y
```

### 3 — Create a non-root user (recommended)

```bash
adduser cvebot
usermod -aG sudo cvebot
# copy your SSH key to the new user (if you used key auth)
rsync --archive --chown=cvebot:cvebot ~/.ssh /home/cvebot
```

From now on, log in as `cvebot`:

```bash
ssh cvebot@YOUR_OVH_IP
```

### 4 — Install Docker & Docker Compose

```bash
# Install Docker's official apt repository
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Allow current user to run Docker without sudo
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

```bash
docker --version          # Docker version 26.x.x …
docker compose version    # Docker Compose version v2.x.x …
```

### 5 — Deploy CVEBOT

```bash
git clone https://github.com/Ret2skillz/CVEBOT.git ~/cvebot
cd ~/cvebot

cp .env.example .env
nano .env   # paste your DISCORD_TOKEN, NVD_API_KEY, GITHUB_TOKEN
```

Start the bot and Watchtower:

```bash
docker compose up -d
```

### 6 — Verify

```bash
docker compose ps          # both cvebot and watchtower should be "running"
docker compose logs -f cvebot
```

You should see discord.py login messages and `Logged in as CVEBOT#XXXX`.

### 7 — OVH firewall (optional)

The bot only makes outbound connections (to Discord and NVD APIs). OVH's
default firewall allows all outbound traffic, so no changes are needed.
If you later enable OVH's built-in "Network Firewall", make sure TCP
outbound on ports 443 (HTTPS) and 8080/8443 (Discord gateway) is allowed.

### 8 — Auto-updates

Watchtower is already running from step 5. Whenever you push to `main`,
GitHub Actions builds a new image and pushes it to GHCR. Within 5 minutes,
Watchtower pulls the new image and restarts `cvebot` automatically.

To watch Watchtower work:

```bash
docker compose logs -f watchtower
```

---

## Hetzner Cloud

Hetzner is the best price-to-performance provider in Europe.
A **CX22** instance (2 vCPU, 4 GB RAM) costs ~€4/month.

### 1 — Create a server

1. Sign up at [hetzner.com/cloud](https://www.hetzner.com/cloud).
2. Create a new project → **Add Server**.
3. Location: Falkenstein or Nuremberg (EU) / Ashburn (US).
4. Image: **Ubuntu 24.04**.
5. Type: **Shared CPU → CX22** (cheapest, sufficient).
6. Under "SSH keys", paste your public key, or note the root password from the
   welcome email.
7. Click **Create & Buy now**.

### 2 — First login & system update

```bash
ssh root@YOUR_HETZNER_IP
apt update && apt upgrade -y
```

### 3 — Install Docker

Same commands as the OVH section above (steps 4):

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

### 4 — Deploy CVEBOT

```bash
git clone https://github.com/Ret2skillz/CVEBOT.git ~/cvebot
cd ~/cvebot
cp .env.example .env && nano .env
docker compose up -d
docker compose logs -f cvebot
```

### 5 — Hetzner firewall (Cloud Firewall)

Hetzner Cloud Firewalls are free and applied per-server. The bot only needs
outbound HTTPS (443). If you want to lock down inbound too:

In the Hetzner Cloud Console → Firewalls → Create Firewall:

| Direction | Protocol | Port | Source/Dest | Note |
|---|---|---|---|---|
| Inbound | TCP | 22 | Your IP /32 | SSH access (your IP only) |
| Outbound | TCP | 443 | 0.0.0.0/0 | HTTPS to Discord & APIs |
| Outbound | TCP | 80 | 0.0.0.0/0 | HTTP (package updates) |

Assign the firewall to your server.

---

## DigitalOcean Droplet

DigitalOcean's **Basic Droplet** starts at $4/month (512 MB RAM / 1 vCPU / 10 GB SSD).
For this bot, even the cheapest plan works fine.

### 1 — Create a Droplet

1. Sign up at [digitalocean.com](https://www.digitalocean.com) (you get $200
   credit for 60 days with a new account).
2. Create → Droplet.
3. Image: **Ubuntu 24.04 LTS**.
4. Size: **Basic → Regular → $4/mo** (the cheapest).
5. Region: closest to your users.
6. Authentication: SSH key (recommended) or password.
7. Click **Create Droplet**.

### 2 — Connect & update

```bash
ssh root@YOUR_DROPLET_IP
apt update && apt upgrade -y
```

### 3 — One-click Docker install (DigitalOcean shortcut)

DigitalOcean maintains a handy install script:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
# Compose v2 is included; verify:
docker compose version
```

### 4 — Deploy CVEBOT

```bash
git clone https://github.com/Ret2skillz/CVEBOT.git ~/cvebot
cd ~/cvebot
cp .env.example .env && nano .env
docker compose up -d
docker compose logs -f cvebot
```

### 5 — DigitalOcean Cloud Firewall (optional)

Droplets are behind no firewall by default (UFW is present but inactive).
Enable UFW with outbound-only if you like:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh        # keep SSH open!
sudo ufw enable
```

Or use the DigitalOcean Networking → Firewalls UI for the same rules.

---

## AWS EC2 Free Tier

AWS offers a **t2.micro** (1 vCPU, 1 GB RAM) instance free for 12 months.
After the free period it costs ~$8/month — consider switching to Hetzner or
OVH for a better price.

### 1 — Launch an EC2 instance

1. Log into [aws.amazon.com/console](https://aws.amazon.com/console).
2. Go to **EC2 → Instances → Launch instances**.
3. Name: `cvebot`.
4. AMI: **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type** (Free tier eligible).
5. Instance type: **t2.micro** (Free tier eligible).
6. Key pair: Create new or select existing (`.pem` file) → download it.
7. Network settings → Security group → **Allow SSH from My IP** only.
8. Storage: 8 GB gp3 is fine.
9. Click **Launch instance**.

### 2 — Connect via SSH

```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 3 — Install Docker

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker compose version
```

### 4 — Security Group — outbound rule

In the AWS Console → EC2 → Security Groups → your group → Outbound rules:

AWS allows all outbound by default, so no changes are required.
If you created a restrictive group, ensure **HTTPS (TCP 443) to 0.0.0.0/0** is
allowed.

### 5 — Deploy CVEBOT

```bash
git clone https://github.com/Ret2skillz/CVEBOT.git ~/cvebot
cd ~/cvebot
cp .env.example .env && nano .env
docker compose up -d
docker compose logs -f cvebot
```

### 6 — Keep the free tier from expiring unnoticed

Set up a **AWS Budget** alert (Billing → Budgets → Create budget → $1/month
threshold) so you are notified before you are charged.

---

## Railway (free PaaS)

Railway is a PaaS that can run a persistent worker process.  
The **free Hobby plan** gives $5/month of credits (~500 hours), enough for
constant uptime if the bot is the only service.

### 1 — Prepare your fork

Railway deploys directly from a GitHub repo. Make sure:
- You have forked `Ret2skillz/CVEBOT` to your own GitHub account.
- Your fork has the `Dockerfile` at the repo root (it already does after the
  previous PR).

### 2 — Create a Railway project

1. Sign up at [railway.app](https://railway.app) with your GitHub account.
2. New Project → **Deploy from GitHub repo** → select your CVEBOT fork.
3. Railway auto-detects the `Dockerfile` and sets the build command.

### 3 — Set environment variables

In the Railway project → your service → **Variables**:

| Key | Value |
|---|---|
| `DISCORD_TOKEN` | your bot token |
| `NVD_API_KEY` | your NVD key |
| `GITHUB_TOKEN` | your GitHub token |
| `DB_PATH` | `/data/cves.db` |

### 4 — Add a persistent volume (for SQLite)

1. Service → **Volumes** → Add Volume.
2. Mount path: `/data`.
3. Railway will persist the SQLite database across redeploys.

### 5 — Deploy

Click **Deploy**.  Railway builds the Docker image, starts the container, and
tails the logs. You should see `Logged in as CVEBOT#XXXX` within ~2 minutes.

### 6 — Automatic redeploys

Railway automatically rebuilds and redeploys whenever you push to the branch
you selected. No Watchtower needed — Railway is the update mechanism.

---

## Render (free PaaS)

Render's **free tier** spins down after 15 minutes of inactivity, which will
disconnect a Discord bot. **Use the Starter plan ($7/month) for a persistent
background worker**, or use Railway / a VPS instead.

### 1 — Create a Web Service (Background Worker)

1. Sign up at [render.com](https://render.com) with your GitHub account.
2. New → **Background Worker**.
3. Connect your CVEBOT fork.
4. Name: `cvebot`.
5. Runtime: **Docker** (auto-detected from `Dockerfile`).
6. Instance type: **Starter ($7/month)** for always-on.

### 2 — Set environment variables

In the service → **Environment** tab, add:

| Key | Value |
|---|---|
| `DISCORD_TOKEN` | your bot token |
| `NVD_API_KEY` | your NVD key |
| `GITHUB_TOKEN` | your GitHub token |
| `DB_PATH` | `/data/cves.db` |

### 3 — Add a persistent disk

Service → **Disks** → Add disk:
- Mount path: `/data`
- Size: 1 GB (free on paid plans)

### 4 — Deploy

Click **Save and Deploy**. Render pulls and builds the image, starts the worker,
and streams logs. Look for `Logged in as CVEBOT#XXXX`.

### 5 — Automatic redeploys

Every push to your repo's default branch triggers a Render redeploy automatically.

---

## Post-deploy checklist

After deploying on any provider, verify these items in Discord:

- [ ] Bot shows as **Online** in your server's member list.
- [ ] `/weekly` responds (try `/weekly` with no arguments).
- [ ] `/id CVE-2021-44228` returns a Log4Shell embed.
- [ ] Pagination arrows (⬅️ ➡️) work when there are multiple results.
- [ ] `/save CVE-2021-44228` and then `/searchmy` returns the saved entry.
- [ ] `docker compose logs -f cvebot` (or provider log UI) shows no ERROR lines.

If slash commands do not appear in the Discord UI:
1. Re-check that **`applications.commands`** scope was used in the invite URL.
2. Global commands can take up to 1 hour to propagate after the first boot.
3. Restart the bot — `setup_hook` calls `tree.sync()` on every startup.
