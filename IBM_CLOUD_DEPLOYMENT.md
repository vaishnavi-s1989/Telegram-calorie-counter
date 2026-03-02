# IBM Cloud & IBM Code Engine — Full Deployment Guide

**Telegram Calorie Tracker Bot**

This guide takes you from zero to a live bot running on IBM Cloud in about 30 minutes.

---

## What You Will End Up With

```
User sends "/log 2 eggs" on Telegram
          │
          ▼  HTTPS (Telegram pushes the message)
IBM Code Engine App  (your container, port 8080)
  ├── POST /webhook  ← receives Telegram messages
  ├── GET  /health   ← IBM health probe
  └── REST /api/...  ← optional API access
          │
          ▼  SQL over TLS
PostgreSQL Database  (IBM Cloud or free ElephantSQL)
```

---

## Prerequisites Checklist

- [ ] IBM Cloud account — https://cloud.ibm.com (free to sign up)
- [ ] Telegram Bot Token — from [@BotFather](https://t.me/botfather)
- [ ] Docker Desktop installed — https://www.docker.com/products/docker-desktop
- [ ] IBM Cloud CLI installed (see Step 1)

---

## Step 1 — Install IBM Cloud CLI

```bash
# macOS
curl -fsSL https://clis.cloud.ibm.com/install/osx | sh

# Verify installation
ibmcloud --version

# Install the two required plugins
ibmcloud plugin install code-engine
ibmcloud plugin install container-registry

# Verify plugins
ibmcloud plugin list
```

---

## Step 2 — Login to IBM Cloud

```bash
# Login (opens a browser window for SSO)
ibmcloud login --sso

# After login, set your region and resource group
# Use the resource group name shown in your IBM Cloud dashboard
ibmcloud target -r us-south -g calorie_counter_VS

# Confirm you are logged in correctly
ibmcloud target
```

---

## Step 3 — Set Up the Database

You have two options. **Option A is free**, Option B is IBM-native.

### Option A — Free PostgreSQL via ElephantSQL (Recommended for getting started)

1. Go to https://www.elephantsql.com and sign up (free, no credit card)
2. Click **"Create New Instance"**
3. Name: `calorie-tracker` → Plan: **Tiny Turtle (Free)** → Region: **US-East-1** → Create
4. Click your instance → copy the **URL** field

It looks like:
```
postgres://user:password@raja.db.elephantsql.com/dbname
```

> ElephantSQL free tier gives 20 MB — enough for hundreds of users.

---

### Option B — IBM Databases for PostgreSQL (~$15/month)

> **Important:** IBM Databases for PostgreSQL requires `--service-endpoints` to be
> specified, otherwise the create command fails with "No service endpoint type specified".
>
> - `--service-endpoints private` — database is only reachable within IBM Cloud
>   (Code Engine can connect; your laptop cannot). **More secure, recommended.**
> - `--service-endpoints public` — database is reachable from anywhere on the internet.
>   Use this only if you need to connect from outside IBM Cloud (e.g., local dev tools).

```bash
# Create the PostgreSQL service instance (private endpoint — recommended)
ibmcloud resource service-instance-create \
  calorie-tracker-db \
  databases-for-postgresql \
  standard \
  us-south \
  --service-endpoints private

# Wait for provisioning (takes 5-10 minutes)
# Check status until it shows "active"
ibmcloud resource service-instance calorie-tracker-db

# Once active, create service credentials
ibmcloud resource service-key-create calorie-tracker-db-creds \
  --instance-name calorie-tracker-db

# Extract the PostgreSQL connection URL
ibmcloud resource service-key calorie-tracker-db-creds --output json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data:
  pg = d['credentials']['connection']['postgres']
  print('DATABASE_URL:', pg['composed'][0])
"
```

The URL will look like:
```
postgresql://ibm_user:password@host.databases.appdomain.cloud:30123/ibmclouddb?sslmode=require
```

> **Note:** IBM Cloud service credentials may show `sslmode=verify-full` in the URL.
> Code Engine containers cannot verify IBM's internal CA, so `config.py` automatically
> rewrites `sslmode=verify-full` → `sslmode=require` at startup.  You do not need to
> edit the URL manually.

> Save this URL — you will need it in Step 9.

---

## Step 4 — Set Up IBM Container Registry (ICR)

IBM Container Registry stores your Docker image.

```bash
# Set region
ibmcloud cr region-set us-south

# Login to the container registry
ibmcloud cr login


# Create a namespace (must be globally unique)
# Use something like your-name-calorie-tracker
ibmcloud cr namespace-add calorie-tracker-ns

# Confirm the namespace was created
ibmcloud cr namespace-list
```

---

## Step 5 — Build and Push the Docker Image

Run these commands from the **project root directory**:

```bash
# Navigate to the project
cd "/Users/vaishnavi/Desktop/Whatsupp calorie counter"

# Build the Docker image
# --platform linux/amd64 is required when building on Apple Silicon (M1/M2/M3)
# so the image runs correctly on IBM Code Engine (x86_64 / amd64)
# Replace 'calorie-tracker-ns' with your ICR namespace from Step 4
docker build --platform linux/amd64 -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .

# This takes 2-5 minutes on first build
# You will see: [+] Building 45.2s (12/12) FINISHED

# Push the image to IBM Container Registry
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

# Verify the image is in ICR
ibmcloud cr image-list
```

---

## Step 6 — Create the Code Engine Project

```bash
# Create a new Code Engine project
ibmcloud ce project create --name calorie-tracker-project

# Select (activate) the project
ibmcloud ce project select --name calorie-tracker-project

# Confirm the project is active
ibmcloud ce project current
```

---

## Step 7 — Create a Registry Pull Secret

Code Engine needs permission to pull your image from ICR.

```bash
# Create an IBM Cloud API key and save the output
ibmcloud iam api-key-create calorie-tracker-key \
  -d "Code Engine ICR pull key" \
  --output json

# From the output, copy the value of "apikey", then run:
ibmcloud ce secret create \
  --format registry \
  --name icr-secret \
  --server us.icr.io \
  --username iamapikey \
  --password <PASTE_YOUR_API_KEY_HERE>
```

---

## Step 8 — Generate a Webhook Secret

This is a random password Telegram sends with every update so your app
can verify the request is genuinely from Telegram.

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Save the output (64 hex characters). Example:
```
a3f8c2d1e4b5a6f7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1
```

---

## Step 9 — Deploy to Code Engine (First Deploy)

The app exposes `POST /webhook` and waits for Telegram to call it.
The webhook URL is registered with Telegram **after** deployment (Step 10),
so you can deploy with `WEBHOOK_MODE=true` straight away.

```bash
ibmcloud ce application create \
  --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest \
  --registry-secret icr-secret \
  --port 8080 \
  --min-scale 1 \
  --max-scale 3 \
  --cpu 0.25 \
  --ephemeral-storage 0.4G \
  --memory 2G \
  --env APP_ENV=production \
  --env DEBUG=false \
  --env WEBHOOK_MODE=true \
  --env TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN> \
  --env DATABASE_URL="<YOUR_POSTGRESQL_URL_FROM_STEP_3>" \
  --env WEBHOOK_SECRET=<YOUR_WEBHOOK_SECRET_FROM_STEP_8>
```

Wait for it to be ready:
```bash
ibmcloud ce application get --name calorie-tracker-bot
# Look for: Status: ready
```

---

## Step 10 — Get the App URL and Register the Webhook (Once)

```bash
# Get your application URL
ibmcloud ce application get --name calorie-tracker-bot
# Look for the "URL" field in the output
# It looks like: https://calorie-tracker-bot.abc123def.us-south.codeengine.appdomain.cloud
```

The app simply exposes `POST /webhook` — it never calls Telegram's
`setWebhook` or `deleteWebhook` API at startup/shutdown.  This avoids
`RetryAfter` rate-limit errors during container restarts.

Register the webhook **once** with a single `curl` command:

```bash
# Replace <YOUR_BOT_TOKEN>, <YOUR_APP_URL>, and <YOUR_WEBHOOK_SECRET>
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://<YOUR_APP_URL>/webhook" \
  -d "secret_token=<YOUR_WEBHOOK_SECRET>" \
  -d "allowed_updates=[\"message\",\"edited_message\",\"callback_query\"]" \
  -d "drop_pending_updates=true" | python3 -m json.tool
```


Expected response:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

You only need to run this command again if:
- Your Code Engine app URL changes (rare — it is stable)
- You rotate your `WEBHOOK_SECRET`

---

## Step 11 — Verify Everything Works

### Check the webhook is registered with Telegram
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo" | python3 -m json.tool
```
Expected response:
```json
{
  "ok": true,
  "result": {
    "url": "https://calorie-tracker-bot.abc123def.us-south.codeengine.appdomain.cloud/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_message": null
  }
}
```

If `url` is empty, run the `setWebhook` curl command from Step 10 again.

### Check the health endpoint
```bash
curl https://calorie-tracker-bot.abc123def.us-south.codeengine.appdomain.cloud/health
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-01T10:00:00.000000",
  "db": "postgresql"
}
```

### Test the bot
Open Telegram, find your bot, send `/start` — it should respond immediately.

---

## Viewing Logs

```bash
# Last 50 lines of logs
ibmcloud ce application logs --name calorie-tracker-bot --tail 50

# Follow logs in real time (like tail -f)
ibmcloud ce application logs --name calorie-tracker-bot --follow

# View application events (scaling, crashes, restarts)
ibmcloud ce application events --name calorie-tracker-bot
```

---

## Updating the App After Code Changes

```bash
# 1. Rebuild the Docker image with your changes
docker build --platform linux/amd64 -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .

# 2. Push the new image
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

# 3. Tell Code Engine to use the new image (triggers a rolling restart)
ibmcloud ce application update \
  --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest
```

---

## Environment Variables Reference

| Variable | Example Value | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-DEF...` | From @BotFather |
| `WEBHOOK_MODE` | `true` | Must be `true` on Code Engine |
| `WEBHOOK_URL` | `https://app.hash.region.codeengine.appdomain.cloud` | Your Code Engine app URL |
| `WEBHOOK_SECRET` | `a3f8c2d1...` (64 chars) | Generated in Step 8 |
| `DATABASE_URL` | `postgresql://user:pass@host:port/db?sslmode=require` | From Step 3 |
| `APP_ENV` | `production` | |
| `DEBUG` | `false` | Set `true` only for troubleshooting |
| `PORT` | `8080` | Must be 8080 on Code Engine |

---

## Cost Estimate

| Service | Plan | Monthly Cost |
|---|---|---|
| IBM Code Engine | Pay-per-use (1 instance, 0.25 CPU, 512 MB) | ~$0–3 |
| ElephantSQL | Tiny Turtle (free, 20 MB) | **$0** |
| IBM Container Registry | Lite (500 MB free) | **$0** |
| **Total with free DB** | | **~$0–3/month** |
| IBM Databases for PostgreSQL | Standard | ~$15/month |
| **Total with IBM DB** | | **~$15–18/month** |

---

## Troubleshooting

### `exec format error` — container fails to start on Code Engine

This happens when the Docker image is built on an **Apple Silicon Mac (M1/M2/M3)**
without specifying the target platform. The image is built for `arm64` but IBM Code
Engine runs on `amd64` (x86_64), so the `gunicorn` binary cannot execute.

**Fix — always build with `--platform linux/amd64`:**

```bash
docker build --platform linux/amd64 \
  -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

# Then redeploy
ibmcloud ce application update \
  --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest
```

The `Dockerfile` already pins the platform via `FROM --platform=linux/amd64 python:3.11-slim`,
but passing `--platform linux/amd64` to `docker build` is the definitive safeguard.

---

### "No service endpoint type specified" when creating PostgreSQL

You must add `--service-endpoints` to the create command. Choose one:
```bash
# Recommended — private endpoint (only reachable within IBM Cloud)
ibmcloud resource service-instance-create \
  calorie-tracker-db \
  databases-for-postgresql \
  standard \
  us-south \
  --service-endpoints private

# Alternative — public endpoint (reachable from anywhere, including your laptop)
ibmcloud resource service-instance-create \
  calorie-tracker-db \
  databases-for-postgresql \
  standard \
  us-south \
  --service-endpoints public
```

### `SSL error: certificate verify failed` — IBM Cloud CA not trusted

IBM Databases for PostgreSQL service credentials contain `sslmode=verify-full`, which
requires psycopg2 to verify the server certificate against a trusted CA.  IBM Cloud
uses its own internal CA that is **not** in the standard OS trust store, so the
verification always fails inside the container.

**`config.py` already fixes this automatically** — it rewrites `sslmode=verify-full`
→ `sslmode=require` at startup.  `require` still enforces TLS encryption but skips
CA verification, which is safe because both Code Engine and IBM Databases for
PostgreSQL run inside IBM Cloud's private network.

If you see this error you are running an **older image**.  Rebuild and redeploy:

```bash
docker build --platform linux/amd64 \
  -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

ibmcloud ce application update \
  --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest
```

Alternatively, change `sslmode=verify-full` to `sslmode=require` in your
`DATABASE_URL` environment variable directly.

---

### `root certificate file does not exist` — SSL connection to IBM PostgreSQL fails

IBM Databases for PostgreSQL enforces TLS.  By default psycopg2 looks for a
client root certificate at `~/.postgresql/root.crt`, which does not exist inside
the container, causing:

```
psycopg2.OperationalError: root certificate file "/home/appuser/.postgresql/root.crt"
does not exist
Either provide the file, use the system's trusted roots with sslrootcert=system,
or change sslmode to disable server certificate verification.
```

**`config.py` already fixes this automatically** — when the `DATABASE_URL` contains
`sslmode=` (as IBM Cloud URLs do) and does not already specify `sslrootcert=`, it
appends `sslrootcert=system`.  This tells psycopg2 to use the OS trusted CA bundle
that ships with the `python:3.11-slim` base image, so no certificate file is needed.

If you see this error you are running an **older image**.  Rebuild and redeploy:

```bash
docker build --platform linux/amd64 \
  -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

ibmcloud ce application update \
  --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest
```

Alternatively, add `sslrootcert=system` to your `DATABASE_URL` manually:
```
postgresql://user:pass@host:port/db?sslmode=require&sslrootcert=system
```

---

### `Can't load plugin: sqlalchemy.dialects:postgres` — database fails to connect

SQLAlchemy 2.x removed support for the legacy `postgres://` URL scheme.
ElephantSQL and some other providers still issue URLs that start with `postgres://`
instead of `postgresql://`.

**`config.py` already normalises this automatically** — it rewrites `postgres://` →
`postgresql://` at startup, so no manual change to your `DATABASE_URL` is needed.

If you see this error it means you are running an **older image** built before this
fix was applied.  Rebuild and redeploy:

```bash
docker build --platform linux/amd64 \
  -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

ibmcloud ce application update \
  --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest
```

Alternatively, you can change the `DATABASE_URL` value itself so it starts with
`postgresql://` instead of `postgres://` — both approaches work.

---

### Bot not responding to messages

```bash
# Check webhook is registered and has no errors
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
# Look for "last_error_message" — if present, that is the problem

# Check app is running
ibmcloud ce application get --name calorie-tracker-bot
# STATUS must be "ready"

# Check logs for errors
ibmcloud ce application logs --name calorie-tracker-bot --tail 100
```

### "WEBHOOK_URL is required" error at startup

```bash
ibmcloud ce application update \
  --name calorie-tracker-bot \
  --env WEBHOOK_URL=https://calorie-tracker-bot.<hash>.us-south.codeengine.appdomain.cloud
```

### Database connection errors

```bash
# Test your DATABASE_URL locally
python3 -c "
import psycopg2
conn = psycopg2.connect('<YOUR_DATABASE_URL>')
print('Connection OK')
conn.close()
"
# For IBM PostgreSQL: URL must end with ?sslmode=require
# For ElephantSQL: URL works as-is
```

### Container fails to start — test locally first

```bash
docker run --rm \
  -e TELEGRAM_BOT_TOKEN=<token> \
  -e WEBHOOK_MODE=false \
  -e DATABASE_URL=sqlite:///./test.db \
  -e APP_ENV=production \
  -e DEBUG=true \
  -e PORT=8080 \
  -p 8080:8080 \
  us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

# In another terminal:
curl http://localhost:8080/health
```

### Slow response / cold start delays

Code Engine can scale to zero when idle. Keep 1 instance always warm:
```bash
ibmcloud ce application update --name calorie-tracker-bot --min-scale 1
```

---

## Clean Up (Delete Everything)

```bash
# Remove the Code Engine application
ibmcloud ce application delete --name calorie-tracker-bot --force

# Delete the Code Engine project
ibmcloud ce project delete --name calorie-tracker-project --force

# Remove the Docker image from ICR
ibmcloud cr image-rm us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

# Remove the ICR namespace
ibmcloud cr namespace-rm calorie-tracker-ns

# Delete IBM PostgreSQL (if you created one)
ibmcloud resource service-instance-delete calorie-tracker-db --force
```

---

## Quick Reference — All Commands in Order

```bash
# 1. Login
ibmcloud login --sso
ibmcloud target -r us-south -g calorie_counter_VS

# 2. Setup ICR
ibmcloud cr login
ibmcloud cr namespace-add calorie-tracker-ns

# 3. Build & push image
cd "/Users/vaishnavi/Desktop/Whatsupp calorie counter"
docker build --platform linux/amd64 -t us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest .
docker push us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest

# 4. Create Code Engine project
ibmcloud ce project create --name calorie-tracker-project
ibmcloud ce project select --name calorie-tracker-project

# 5. Create registry secret
ibmcloud iam api-key-create calorie-tracker-key --output json
ibmcloud ce secret create --format registry --name icr-secret \
  --server us.icr.io --username iamapikey --password <API_KEY>

# 6. Generate webhook secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# 7. Deploy
ibmcloud ce application create --name calorie-tracker-bot \
  --image us.icr.io/calorie-tracker-ns/calorie-tracker-bot:latest \
  --registry-secret icr-secret --port 8080 --min-scale 1 \
  --env TELEGRAM_BOT_TOKEN=<token> \
  --env DATABASE_URL="<pg-url>" \
  --env WEBHOOK_SECRET=<secret> \
  --env WEBHOOK_MODE=true \
  --env APP_ENV=production --env DEBUG=false --env PORT=8080

# 8. Get the app URL
ibmcloud ce application get --name calorie-tracker-bot

# 9. Register the webhook ONCE manually (replace placeholders)
curl -s "https://api.telegram.org/bot<token>/setWebhook" \
  -d "url=https://calorie-tracker-bot.<hash>.us-south.codeengine.appdomain.cloud/webhook" \
  -d "secret_token=<secret>" \
  -d "allowed_updates=[\"message\",\"edited_message\",\"callback_query\"]" \
  -d "drop_pending_updates=true"

# 10. Verify
curl https://calorie-tracker-bot.<hash>.us-south.codeengine.appdomain.cloud/health
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

*Made with Bob*