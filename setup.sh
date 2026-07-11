#!/bin/bash
apt-get update -qq && apt-get install -y -qq dnsutils > /dev/null 2>&1
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "✅ Starting MX Mailer API on port 8080 ..."
python3 "$SCRIPT_DIR/mail_api.py"
