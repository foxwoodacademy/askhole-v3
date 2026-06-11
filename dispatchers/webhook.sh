#!/bin/bash
# askhole_webhook.sh — Webhook dispatcher
# Usage: Set AH_SUBJECT, AH_BODY, AH_TARGET, AH_CTA env vars
# Set WEBHOOK_URL env var

URL="${WEBHOOK_URL:-http://localhost:8080/hook}"

PAYLOAD=$(cat <<EOF
{
  "target": "$AH_TARGET",
  "subject": "$AH_SUBJECT",
  "body": "$AH_BODY",
  "cta": "$AH_CTA",
  "timestamp": "$(date -Iseconds)"
}
EOF
)

curl -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
