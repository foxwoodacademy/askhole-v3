# AskHole v3

> The question you didn't want to ask.

Auto-scout. Economics DB. One-shot dispatch.

## Setup

```bash
# API keys
export GEMINI_KEY="your_key"
export GROQ_KEY="your_key"
export GOOGLE_PLACES_KEY="your_key"  # optional, for auto-scout

# Or hardcode in askhole.py PROVIDERS list
```

## Usage

### Full auto (Google Places scout + report + print)
```bash
python askhole.py \
  --text "Chew Plumbing" \
  --city "Wellington KS" \
  --vertical plumber \
  --outreach
```

### Manual intel (paste reviews)
```bash
python askhole.py \
  --text "Shitty Local Bank" \
  --vertical bank \
  --intel "2.3 stars 47 reviews nobody answers phone..." \
  --outreach
```

### Cache-only (skip scout, use existing)
```bash
python askhole.py \
  --text "Chew Plumbing" \
  --vertical plumber \
  --no-scout \
  --outreach
```

### Dispatch
```bash
# Print to terminal (default)
python askhole.py --text "..." --vertical plumber --send print

# Email (requires msmtp/mutt configured)
python askhole.py --text "..." --vertical plumber --send email

# SMS (requires termux-sms or twilio-cli)
python askhole.py --text "..." --vertical plumber --send sms

# Webhook (set WEBHOOK_URL env var)
python askhole.py --text "..." --vertical plumber --send webhook
```

## Adding Verticals

Edit `economics.json`. Add a new key with the same fields as "plumber" or "bank".

## Output

- `outreach/*.txt` — The report
- `outreach/*_payload.json` — Subject, body, CTA, lead value
- `verticals/*.json` — Cached scout data

## Dispatchers

Shell scripts in `dispatchers/` handle actual sending. Edit to match your Termux setup.
- `email.sh` — msmtp or mutt
- `sms.sh` — termux-sms-send or twilio
- `webhook.sh` — curl POST to your endpoint
