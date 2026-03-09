#!/usr/bin/env python3
"""Tüm mesajları oku ve dosyaya yaz."""
import json
import urllib.request

token = open("/Users/emre/Desktop/Emare/EMARE_ORTAK_CALISMA/.github_token").read().strip()
BASE = "https://api.github.com/repos/emraresoftware/emare-ortak-calisma"

def api(endpoint):
    req = urllib.request.Request(
        f"{BASE}{endpoint}",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

issues = api("/issues?state=open&per_page=30&sort=updated&direction=desc")

output = []
output.append("=" * 60)
output.append("TÜM AÇIK MESAJLAR (güncel→eski)")
output.append("=" * 60)

for i in issues:
    labels = [l["name"] for l in i.get("labels", [])]
    output.append(f"\n### #{i['number']} | {i['updated_at']}")
    output.append(f"Başlık: {i['title']}")
    output.append(f"Labels: {labels}")
    output.append(f"Body:\n{i['body']}")
    
    if i.get("comments", 0) > 0:
        comments = api(f"/issues/{i['number']}/comments?per_page=10")
        for c in comments:
            output.append(f"\n  --- Yorum ({c['created_at']}) ---")
            output.append(f"  {c['body']}")

result = "\n".join(output)
with open("/tmp/emare_messages.txt", "w") as f:
    f.write(result)
print(f"Yazıldı: {len(output)} satır, {len(result)} karakter")
print("Dosya: /tmp/emare_messages.txt")
