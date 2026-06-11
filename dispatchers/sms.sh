#!/bin/bash
# askhole_sms.sh — SMS dispatcher
# Requires: twilio-cli or termux-sms
# Usage: Set AH_SUBJECT, AH_BODY, AH_TARGET env vars

PHONE="${AH_TARGET_PHONE:-+15551234567}"
MSG="${AH_SUBJECT}. ${AH_CTA}"

# Termux method
if command -v termux-sms-send &> /dev/null; then
    termux-sms-send -n "$PHONE" "$MSG"
    exit 0
fi

# Twilio CLI method
if command -v twilio &> /dev/null; then
    twilio api:core:messages:create --to "$PHONE" --from "$TWILIO_FROM" --body "$MSG"
    exit 0
fi

echo "No SMS method found. Install termux-api or twilio-cli."
exit 1
