#!/usr/bin/env python3
"""Deploy promolift-landing to Cloudflare Pages"""
import os, json, requests, mimetypes
from pathlib import Path

CF_EMAIL = "Germanfedorenko.gf@gmail.com"
CF_KEY = os.environ.get("CF_GLOBAL_KEY", "")
if not CF_KEY:
    with open("/data/data/com.termux/files/home/.env") as f:
        for line in f:
            if "CF_GLOBAL_KEY" in line:
                CF_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
ACCT = "869d3a332168f7fcc9c243943f913c8b"
PROJECT = "promolift"
DIR = Path("/data/data/com.termux/files/home/promolift-landing")

headers = {"X-Auth-Email": CF_EMAIL, "X-Auth-Key": CF_KEY}

# Stage 1: Create deployment
print("Creating deployment...")
r = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJECT}/deployments",
    headers={**headers, "Content-Type": "application/json"},
    json={},
    timeout=30,
)
d = r.json()
print(f"  success={d.get('success')}")
if not d.get("success"):
    print(f"  errors: {d.get('errors', [])}")
    exit(1)

deploy_id = d["result"]["id"]
print(f"  deployment_id={deploy_id}")

# Stage 2: Upload files
upload_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJECT}/deployments/{deploy_id}/upload-files"
total, errors = 0, 0
for fpath in sorted(DIR.rglob("*")):
    if fpath.is_file() and fpath.stat().st_size > 0 and fpath.name != "deploy.py":
        rel = str(fpath.relative_to(DIR))
        mime = mimetypes.guess_type(str(fpath))[0] or "application/octet-stream"
        if rel.endswith(".html"):
            mime = "text/html; charset=utf-8"
        r2 = requests.post(
            upload_url,
            headers=headers,
            files={"file": (rel, fpath.read_bytes(), mime)},
            timeout=60,
        )
        res = r2.json()
        if res.get("success"):
            total += 1
        else:
            errors += 1
            print(f"  FAIL {rel}: {res.get('errors', [{}])[0].get('message','?')[:80]}")
print(f"  Uploaded {total} files ({errors} errors)")

# Stage 3: Finalize
print("Finalizing deployment...")
r3 = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJECT}/deployments/{deploy_id}",
    headers={**headers, "Content-Type": "application/json"},
    json={},
    timeout=30,
)
res3 = r3.json()
print(f"  success={res3.get('success')}")
print(f"  state={res3.get('result', {}).get('state', '?')}")
print(f"  url={res3.get('result', {}).get('url', '?')}")
