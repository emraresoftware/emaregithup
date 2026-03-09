#!/usr/bin/env python3
"""ACİL GÜVENLİK KONTROLÜ - Token sızıntısı değerlendirmesi."""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime

TOKEN = open("/Users/emre/Desktop/Emare/EMARE_ORTAK_CALISMA/.github_token").read().strip()

def api(endpoint):
    req = urllib.request.Request(
        f"https://api.github.com{endpoint}",
        headers={
            "Authorization": f"token {TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}

print("=" * 60)
print("🔴 ACİL GÜVENLİK DEĞERLENDİRMESİ")
print("=" * 60)

# 1. Token hala aktif mi?
print("\n1️⃣  TOKEN DURUMU:")
status, user = api("/user")
if status == 200:
    print(f"   ⚠️  TOKEN HALA AKTİF! User: {user.get('login')}")
    print(f"   Scopes: Tüm repoları okuma/yazma riski!")
else:
    print(f"   ✅ Token iptal edilmiş (HTTP {status})")

# 2. soru-cevap repo durumu
print("\n2️⃣  SORU-CEVAP REPO:")
status, repo = api("/repos/emraresoftware/soru-cevap")
if status == 200:
    print(f"   Repo: {repo.get('full_name')}")
    print(f"   Private: {repo.get('private')}")
    print(f"   Visibility: {repo.get('visibility')}")
    
    # Repo'nun içeriğine bak
    status2, contents = api("/repos/emraresoftware/soru-cevap/contents/")
    if status2 == 200:
        print(f"   Dosyalar: {[c['name'] for c in contents]}")
else:
    print(f"   HTTP {status} - Repo bulunamadı veya erişim yok")

# 3. Son events - yetkisiz aktivite
print("\n3️⃣  SON AKTİVİTELER (son 30):")
status, events = api("/users/emraresoftware/events?per_page=30")
if status == 200:
    for e in events[:20]:
        t = e.get("type", "?")
        repo = e.get("repo", {}).get("name", "?")
        date = e.get("created_at", "?")
        actor = e.get("actor", {}).get("login", "?")
        print(f"   {date} | {actor} | {t} | {repo}")
else:
    print(f"   Events alınamadı: HTTP {status}")

# 4. Son oluşturulan/silinen repolar
print("\n4️⃣  TÜM REPOLAR (silinmiş/eklenmiş var mı?):")
repos = []
page = 1
while True:
    s, data = api(f"/user/repos?per_page=100&page={page}&affiliation=owner")
    if s != 200 or not data:
        break
    repos.extend(data)
    if len(data) < 100:
        break
    page += 1
print(f"   Toplam repo: {len(repos)}")

# Son oluşturulan repoları kontrol et
recent = sorted(repos, key=lambda r: r.get("created_at", ""), reverse=True)[:5]
print("   Son oluşturulan:")
for r in recent:
    print(f"     {r['created_at']} | {r['name']} | private={r['private']}")

# 5. Deploy keys ve webhooks - kötü niyetli ekleme var mı?
print("\n5️⃣  WEBHOOK SAYILARI (anormal var mı?):")
suspicious = []
for r in repos[:10]:  # ilk 10'u kontrol et
    s, hooks = api(f"/repos/emraresoftware/{r['name']}/hooks")
    if s == 200 and hooks:
        for h in hooks:
            url = h.get("config", {}).get("url", "?")
            if "emarecloud.tr" not in url:
                suspicious.append(f"  ⚠️  {r['name']}: {url}")
            else:
                pass  # Bizim webhook

if suspicious:
    print("   🔴 ŞÜPHELİ WEBHOOK'LAR BULUNDU:")
    for s in suspicious:
        print(f"   {s}")
else:
    print("   ✅ Tüm webhook'lar emarecloud.tr'ye ait (normal)")

# 6. Audit log - org events
print("\n6️⃣  TOKEN SCOPES:")
req = urllib.request.Request(
    "https://api.github.com/user",
    headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
)
try:
    with urllib.request.urlopen(req) as resp:
        scopes = resp.headers.get("X-OAuth-Scopes", "?")
        print(f"   Scopes: {scopes}")
        rate = resp.headers.get("X-RateLimit-Remaining", "?")
        print(f"   Rate limit kalan: {rate}")
except:
    print("   Token zaten iptal edilmiş olabilir")

print("\n" + "=" * 60)
print("📋 YAPILMASI GEREKENLER:")
print("=" * 60)
print("1. github.com/settings/tokens → Bu token'ı HEMEN iptal et")
print("2. Yeni token oluştur (minimum scope)")
print("3. .github_token dosyasını güncelle")
print("4. soru-cevap repo'daki config'den token'ı temizle")
print("5. Git history'den token'ı temizle (BFG/filter-branch)")
print("=" * 60)
