#!/usr/bin/env python3
"""
AskHole v3 — The question you didn't want to ask.
Auto-scout. Economics DB. Dispatch ready.
"""

import argparse
import json
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# --- PATHS ---
BASE_DIR = Path(__file__).parent
VERTICALS_DIR = BASE_DIR / "verticals"
OUTREACH_DIR = BASE_DIR / "outreach"
DISPATCHERS_DIR = BASE_DIR / "dispatchers"
ECONOMICS_FILE = BASE_DIR / "economics.json"

# --- PROVIDERS ---
PROVIDERS = [
    {
        "name": "cerebras",
        "model": "gpt-oss-120b",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key_env": "CEREBRAS_API_KEY",
    },
    {
        "name": "mistral",
        "model": "mistral-large-latest",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key_env": "MISTRAL_API_KEY",
    },
    {
        "name": "openrouter",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
    },
    {
        "name": "fireworks",
        "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "url": "https://api.fireworks.ai/inference/v1/chat/completions",
        "key_env": "FIREWORKS_API_KEY",
    },
    {
        "name": "groq",
        "model": "llama-3.3-70b-versatile",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
    },
    {
        "name": "gemini",
        "model": "gemini-2.0-flash",
        "key_env": "GEMINI_API_KEY",
    },

    {
        "name": "cerebras",
        "model": "gpt-oss-120b",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "key": os.environ.get("CEREBRAS_API_KEY", ""),
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
    {
        "name": "openrouter",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": os.environ.get("OPENROUTER_API_KEY", ""),
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
    {
        "name": "gemini",
        "model": "gemini-2.0-flash",
        "key": os.environ.get("GEMINI_KEY", ""),
    },
    {
        "name": "groq",
        "model": "llama3-70b-8192",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key": os.environ.get("GROQ_KEY", ""),
        "headers": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
    },
]

# --- ASKHOLE SYSTEM PROMPT ---
ASKHOLE_SYSTEM = """You are AskHole.

Voice: Lewis Black with a spreadsheet. Jon Stewart reading a financial audit. Norm MacDonald delivering a punchline that happens to be true.
Direct. Impatient. Precise. Occasionally devastating.
Say what the prospect doesn't want to hear. Then prove it with math.

Job: Build a complete business intelligence brief that makes the owner feel like
someone finally looked at their actual situation and told them the truth.
Stress-test every claim until it holds or dies.
No corporate padding. No hedging. No buzzwords.

Output this format. Each section as long as it needs to be. No word limit.

---
THE SITUATION: What this business actually looks like from outside. Be specific. Name real numbers.

THE LEAK: Where the money is leaving. Show the math. Monthly and annual loss. Use economics provided.

THE COMPETITION: Who is already eating their lunch and how far ahead they are. Name names.

BOTTLENECKS: The 2-3 specific operational choke points killing this business right now.

RED FLAGS: What will blow this up if left unaddressed. Be brutal.

THE FIX: What the solution does. Specific steps. No buzzwords. What changes on day 1, week 2, month 3.

90-DAY ROADMAP:
  Week 1-2: [specific actions]
  Month 1: [specific milestones]
  Month 2: [specific milestones]  
  Month 3: [target outcome with number]

PRICE POINT ANALYSIS: What they are paying now for the problem vs what the fix costs. Show the ROI math.

TAX AND INVESTMENT ANGLE: Any legitimate tax write-off, deduction, or investment framing that applies to this vertical and situation.

LOOPHOLES: Any competitive advantage, timing window, or market gap they could exploit right now.

THE CATCH: Why this might fail. One specific scenario. Brutal.

THE REVERSAL: Why the catch is manageable. Or write OVERRULED and explain why the risk is worth it.

THE ASK: One next step. Specific. Time-bound.

THE HOOK: Cold outreach subject line. Provocative. Under 10 words.
---

Rules:
- Use the economics numbers provided. Show your math.
- If a number is missing estimate it and say so
- Kill marketing fluff on sight
- Forbidden: leverage, synergy, optimize, streamline, holistic, paradigm, ecosystem
- Be specific to THIS business not generic advice
- The roadmap must have actual steps not platitudes
- The tax angle must be real not invented"""

# --- PROVIDER CALL ---
def call_model(prompt, system=None):
    import requests, os
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    for p in PROVIDERS:
        key = os.getenv(p.get("key_env","")) or p.get("key","")
        if not key:
            continue
        p = {**p, "key": key}
        try:
            if p["name"] == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{p['model']}:generateContent?key={p['key']}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                if system:
                    payload["system_instruction"] = {"parts": [{"text": system}]}
                r = requests.post(url, json=payload, timeout=30)
                r.raise_for_status()
                return r.json()["candidates"][0]["content"]["parts"][0]["text"], p["name"]
            else:
                headers = p.get("headers", lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"})(key)
                r = requests.post(
                    p["url"],
                    headers=headers,
                    json={"model": p["model"], "messages": msgs, "max_tokens": 1200, "temperature": 0.4},
                    timeout=30
                )
                if r.status_code == 429:
                    print(f"  [{p['name']}] rate limited, trying next...")
                    continue
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"], p["name"]
        except Exception as e:
            print(f"  [{p['name']}] failed: {e}")
            continue
    raise RuntimeError("All providers failed")

# --- ECONOMICS ---
def load_economics():
    if ECONOMICS_FILE.exists():
        return json.loads(ECONOMICS_FILE.read_text())
    return {}

def get_vertical_econ(vertical):
    econ = load_economics()
    return econ.get(vertical, {})

# --- SCOUT ---
def auto_scout(business, city, vertical):
    """Auto-scout via Google Places or fallback to manual."""
    print(f"[Scout] Hunting: {business} in {city}...")

    # Try Google Places API if key exists
    gkey = os.environ.get("GOOGLE_PLACES_KEY", "")
    if gkey:
        try:
            import requests
            # Find place
            find_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            find_params = {
                "input": f"{business} {city}",
                "inputtype": "textquery",
                "fields": "place_id,name,rating,user_ratings_total,formatted_address",
                "key": gkey
            }
            fr = requests.get(find_url, params=find_params, timeout=15)
            fr.raise_for_status()
            fdata = fr.json()

            if fdata.get("candidates"):
                place = fdata["candidates"][0]
                place_id = place.get("place_id")

                # Get details + reviews
                detail_url = "https://maps.googleapis.com/maps/api/place/details/json"
                detail_params = {
                    "place_id": place_id,
                    "fields": "name,rating,reviews,formatted_phone_number,website,opening_hours",
                    "key": gkey
                }
                dr = requests.get(detail_url, params=detail_params, timeout=15)
                dr.raise_for_status()
                ddata = dr.json().get("result", {})

                reviews = ddata.get("reviews", [])
                review_texts = [r.get("text", "") for r in reviews[:10]]

                intel = {
                    "business": ddata.get("name", business),
                    "rating": ddata.get("rating"),
                    "review_count": ddata.get("user_ratings_total", len(reviews)),
                    "address": ddata.get("formatted_address", ""),
                    "phone": ddata.get("formatted_phone_number", ""),
                    "reviews": review_texts,
                    "source": "google_places_api"
                }
                print(f"[Scout] Found: {intel['rating']} stars, {intel['review_count']} reviews")
                return intel
        except Exception as e:
            print(f"[Scout] Google Places failed: {e}")

    # Fallback: try serpapi or just return None for manual
    print("[Scout] No API key or API failed. Use --intel to paste raw data.")
    return None

def save_scout_cache(vertical, intel_dict):
    vfile = VERTICALS_DIR / f"{vertical}.json"
    vfile.write_text(json.dumps(intel_dict, indent=2))
    print(f"[Scout] Cached: {vfile}")

def load_scout_cache(vertical):
    vfile = VERTICALS_DIR / f"{vertical}.json"
    if vfile.exists():
        return json.loads(vfile.read_text())
    return None

def parse_manual_intel(raw_intel):
    """Parse unstructured text into structured cache."""
    ratings = re.findall(r'(\d\.\d)\s*stars?', raw_intel, re.IGNORECASE)
    reviews = re.findall(r'(\d+)\s+reviews?', raw_intel, re.IGNORECASE)
    complaints = re.findall(r'(?:bad|rude|slow|never|worst|terrible|awful|hate|suck|useless)[^\.]{0,60}', raw_intel, re.IGNORECASE)

    return {
        "rating": float(ratings[0]) if ratings else None,
        "review_count": int(reviews[0]) if reviews else None,
        "complaints": complaints[:8],
        "raw": raw_intel,
        "source": "manual"
    }

# --- PROMPT BUILDER ---
def build_prompt(target, vertical, scout_intel, econ, extra_context=""):
    parts = [
        f"Target business: {target}",
        f"Vertical: {vertical}",
        f"Vertical economics: {json.dumps(econ, indent=2)}",
    ]
    if scout_intel:
        parts.append(f"Scouted intel: {json.dumps(scout_intel, indent=2)}")
    if extra_context:
        parts.append(f"Additional context: {extra_context}")
    parts.append("Generate the AskHole report now.")
    return "\n\n".join(parts)

# --- REPORT ---
def generate_report(target, vertical, scout_intel, econ, extra=""):
    prompt = build_prompt(target, vertical, scout_intel, econ, extra)
    try:
        text, provider = call_model(prompt, system=ASKHOLE_SYSTEM)
        if 'THE SITUATION' in text:
            text = text[text.index('THE SITUATION'):]
        print(f"[AskHole] Generated via {provider}")
        return text
    except RuntimeError as e:
        print(f"[AskHole] FAILED: {e}")
        # Build fallback from template + econ
        leak = econ.get("missed_call_cost", "NUMBER NEEDED")
        signal = econ.get("comp_signal", "NUMBER NEEDED")
        return f"""THE LEAK: {target} is leaving money on the table. Missed calls cost ~${leak} each.
PROOF OF LIFE: {signal}
THE FIX: AI intake captures, qualifies, and schedules inbound inquiries before human touch.
THE CATCH: If staff don't check the dashboard, this is a $249/month ornament.
THE REVERSAL: They already don't check voicemail. This is faster.
THE ASK: 15-minute call. Tuesday or Thursday. Pick one, I'll bring numbers.
THE HOOK: Your voicemail is funding your competitors
"""

def save_report(target, vertical, report):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^\w-]", "_", target)[:40]
    fname = f"{safe}_{vertical}_{ts}.txt"
    fpath = OUTREACH_DIR / fname
    fpath.write_text(report)
    return fpath

def save_payload(target, vertical, report, fpath):
    hook = re.search(r"THE HOOK:\s*(.+)", report, re.IGNORECASE)
    ask = re.search(r"THE ASK:\s*(.+)", report, re.IGNORECASE)
    leak = re.search(r"THE LEAK:\s*(.+)", report, re.IGNORECASE)
    payload = {
        "subject": hook.group(1).strip() if hook else "Quick question",
        "body": report,
        "cta": ask.group(1).strip() if ask else "Reply if interested",
        "lead_value": leak.group(1).strip() if leak else "Unknown",
        "target": target,
        "vertical": vertical,
        "generated": datetime.now().isoformat()
    }
    opath = OUTREACH_DIR / (fpath.stem + "_payload.json")
    opath.write_text(json.dumps(payload, indent=2))
    return payload, opath

# --- DISPATCH ---
def dispatch(payload, method="print"):
    """Send the outreach payload. Methods: print, email, sms, webhook"""
    dispatcher = DISPATCHERS_DIR / f"{method}.sh"

    if method == "print":
        print(f"\n{'='*50}")
        print(f"TO: {payload['target']}")
        print(f"SUBJECT: {payload['subject']}")
        print(f"\n{payload['body']}")
        print(f"\nCTA: {payload['cta']}")
        print(f"{'='*50}")
        return True

    if dispatcher.exists():
        # Pass payload as env vars to shell script
        env = os.environ.copy()
        env["AH_SUBJECT"] = payload["subject"]
        env["AH_BODY"] = payload["body"]
        env["AH_CTA"] = payload["cta"]
        env["AH_TARGET"] = payload["target"]
        result = subprocess.run([str(dispatcher)], env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[Dispatch] Sent via {method}")
            return True
        else:
            print(f"[Dispatch] {method} failed: {result.stderr}")
            return False

    print(f"[Dispatch] No dispatcher found for '{method}'. Create {dispatcher}")
    return False

# --- MAIN ---
def main():
    parser = argparse.ArgumentParser(description="AskHole v3 — Auto-scout, Economics, Dispatch")
    parser.add_argument("--text", required=True, help="Target business")
    parser.add_argument("--vertical", required=True, help="Vertical/niche")
    parser.add_argument("--city", default="", help="City, State for auto-scout")
    parser.add_argument("--intel", default="", help="Raw intel text (manual scout)")
    parser.add_argument("--context", default="", help="Extra context")
    parser.add_argument("--outreach", action="store_true", help="Generate payload")
    parser.add_argument("--send", default="print", help="Dispatch method: print, email, sms, webhook")
    parser.add_argument("--no-scout", action="store_true", help="Skip auto-scout, use cache only")

    args = parser.parse_args()

    print(f"[AskHole] Target: {args.text}")
    print(f"[AskHole] Vertical: {args.vertical}")

    # 1. SCOUT
    scout_intel = None
    if not args.no_scout:
        cached = load_scout_cache(args.vertical)
        if cached:
            print("[AskHole] Using cached scout data")
            scout_intel = cached
        elif args.city:
            scout_intel = auto_scout(args.text, args.city, args.vertical)
            if scout_intel:
                save_scout_cache(args.vertical, scout_intel)
        elif args.intel:
            scout_intel = parse_manual_intel(args.intel)
            save_scout_cache(args.vertical, scout_intel)

    # 2. ECONOMICS
    econ = get_vertical_econ(args.vertical)
    if econ:
        print(f"[AskHole] Loaded economics for {args.vertical}")
    else:
        print(f"[AskHole] WARNING: No economics for '{args.vertical}'. Add to economics.json")

    # 3. REPORT
    report = generate_report(args.text, args.vertical, scout_intel, econ, args.context)
    fpath = save_report(args.text, args.vertical, report)

    print(f"\n{'='*50}")
    print(report)
    print(f"{'='*50}")
    print(f"\n[AskHole] Report: {fpath}")

    # 4. OUTREACH + DISPATCH
    if args.outreach or args.send != "print":
        payload, opath = save_payload(args.text, args.vertical, report, fpath)
        print(f"[AskHole] Payload: {opath}")
        dispatch(payload, method=args.send)

if __name__ == "__main__":
    main()
