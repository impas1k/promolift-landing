#!/usr/bin/env python3
"""Simple deploy test - just the HTML file"""
import json, requests, uuid, io, os

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

# Read index.html
with open("/data/data/com.termux/files/home/promolift-landing/index.html", "rb") as f:
    html_content = f.read()

manifest = {"index.html": "text/html; charset=utf-8"}
boundary = str(uuid.uuid4())
body = io.BytesIO()

def w(data):
    if isinstance(data, str): body.write(data.encode())
    else: body.write(data)

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
add_field("index.html", "index.html", html_content, "text/html; charset=utf-8")
w("--" + boundary + "--\r\n")
body_data = body.getvalue()

headers = {
    "X-Auth-Email": CF_EMAIL,
    "X-Auth-Key": CF_KEY,
    "Content-Type": f"multipart/form-data; boundary={boundary}"
}

print("Deploying...")
resp = requests.post(
    f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJECT}/deployments",
    data=body_data, headers=headers, timeout=120
)
res = resp.json()
print(f"Status: {resp.status_code}")
if res.get("success"):
    r = res["result"]
    print(f"URL: {r.get('url')}")
    for s in sorted(r.get('stages', []), key=lambda x: x.get('name', '')):
        print(f"  {s.get('name')}: {s.get('status')}")
    print(f"Aliases: {r.get('aliases', [])}")
else:
    print(f"Error: {res.get('errors')}")
