#!/bin/bash
# askhole_email.sh — Email dispatcher
# Requires: msmtp or mutt configured in Termux
# Usage: Set AH_SUBJECT, AH_BODY, AH_TARGET env vars

TO="${AH_TARGET_EMAIL:-prospect@example.com}"
SUBJECT="${AH_SUBJECT:-Quick question}"
BODY="${AH_BODY:-No body}"

# msmtp method
if command -v msmtp &> /dev/null; then
    echo -e "Subject: $SUBJECT\n\n$BODY\n\n${AH_CTA}" | msmtp "$TO"
    exit 0
fi

# mutt method  
if command -v mutt &> /dev/null; then
    echo -e "$BODY\n\n${AH_CTA}" | mutt -s "$SUBJECT" "$TO"
    exit 0
fi

echo "No email client found. Install msmtp or mutt."
exit 1
