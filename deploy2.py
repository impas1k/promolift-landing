#!/usr/bin/env python3
"""Deploy promolift-landing to Cloudflare Pages (multipart upload)"""
import os, json, requests, mimetypes, uuid, io
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

# Build manifest
manifest = {}
files_data = {}
for fpath in sorted(DIR.rglob("*")):
    if fpath.is_file() and fpath.stat().st_size > 0 and fpath.name != "deploy.py":
        rel = str(fpath.relative_to(DIR))
        ct, _ = mimetypes.guess_type(str(fpath))
        if not ct:
            ct = "application/octet-stream"
        if rel.endswith(".html"):
            ct = "text/html; charset=utf-8"
        manifest[rel] = ct
        with open(fpath, "rb") as f:
            files_data[rel] = f.read()

print(f"Uploading {len(manifest)} files...")

boundary = str(uuid.uuid4())
body = io.BytesIO()

def w(data):
    if isinstance(data, str):
        body.write(data.encode())
    else:
        body.write(data)

def add_field(name, filename, data, ct):
    w("--" + boundary + "\r\n")
    if filename:
        w(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n')
    else:
        w(f'Content-Disposition: form-data; name="{name}"\r\n')
    w(f"Content-Type: {ct}\r\n\r\n")
    w(data)
    w("\r\n")

add_field("manifest", None, json.dumps(manifest), "application/json")
for rel, ct in manifest.items():
    filename = rel.split("/")[-1]
    add_field(rel, filename, files_data[rel], ct)

w("--" + boundary + "--\r\n")
body_data = body.getvalue()

headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

resp = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJECT}/deployments",
    data=body_data,
    headers=headers,
    timeout=120,
)
print(f"Status: {resp.status_code}")
result = resp.json()
if result.get("success"):
    r = result["result"]
    print("DEPLOYED!")
    print(f"URL: {r.get('url', '?')}")
    print(f"Stage: {r.get('latest_stage', {}).get('name', '?')}")
else:
    print(f"Error: {json.dumps(result.get('errors', result), indent=2)[:600]}")
