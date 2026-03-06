#!/usr/bin/env python3
"""
GitHub Webhook Kurulum Scripti
===============================
emraresoftware hesabındaki tüm repolara push webhook ekler.

Webhook → POST http(s)://<server>:8112/github-webhook
        → webhook_receiver.py dinler
        → EmareCloud paneline iletir
        → Otomatik deploy tetiklenir

Kullanım:
  python3 setup_webhooks.py                    # Listeleme (dry-run)
  python3 setup_webhooks.py --apply            # Webhook ekle
  python3 setup_webhooks.py --list             # Mevcut webhook'ları listele
  python3 setup_webhooks.py --delete-all       # Tüm webhook'ları sil
"""

import json
import os
import sys
import urllib.request
import urllib.error

# ── Yapılandırma ──
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    token_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "EMARE_ORTAK_CALISMA", ".github_token"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "EMARE_ORTAK_CALISMA", ".github_token"),
    ]
    for p in token_paths:
        if os.path.exists(p):
            with open(p) as f:
                GITHUB_TOKEN = f.read().strip()
            break

GITHUB_USER = "emraresoftware"
API_BASE = "https://api.github.com"

# Webhook ayarları
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "emare-deploy-secret-2025")
# Sunucu IP/domain — deploy sırasında güncellenmeli
WEBHOOK_SERVER = os.getenv("WEBHOOK_SERVER", "localhost")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8112"))
WEBHOOK_URL = f"http://{WEBHOOK_SERVER}:{WEBHOOK_PORT}/github-webhook"


def api(method, endpoint, data=None):
    """GitHub API çağrısı."""
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except:
            return e.code, {"message": str(e)}


def repolari_listele():
    """Tüm repoları al."""
    repolar = []
    page = 1
    while True:
        status, data = api("GET", f"/users/{GITHUB_USER}/repos?per_page=100&page={page}")
        if status != 200 or not data:
            break
        repolar.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repolar


def mevcut_webhooks(repo_name):
    """Bir repodaki mevcut webhook'ları listele."""
    status, data = api("GET", f"/repos/{GITHUB_USER}/{repo_name}/hooks")
    if status == 200:
        return data
    return []


def webhook_ekle(repo_name, url, secret):
    """Bir repoya push webhook ekle."""
    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": url,
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0"
        }
    }
    status, data = api("POST", f"/repos/{GITHUB_USER}/{repo_name}/hooks", payload)
    return status, data


def webhook_sil(repo_name, hook_id):
    """Bir webhook'u sil."""
    status, data = api("DELETE", f"/repos/{GITHUB_USER}/{repo_name}/hooks/{hook_id}")
    return status


def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN bulunamadı!")
        sys.exit(1)

    mode = "dry-run"
    if "--apply" in sys.argv:
        mode = "apply"
    elif "--list" in sys.argv:
        mode = "list"
    elif "--delete-all" in sys.argv:
        mode = "delete"

    print(f"""
╔══════════════════════════════════════════════════╗
║  EmareGitHup — GitHub Webhook Kurulum Scripti    ║
╠══════════════════════════════════════════════════╣
║  Mod      : {mode:<36} ║
║  URL      : {WEBHOOK_URL:<36} ║
║  Secret   : {'*' * min(len(WEBHOOK_SECRET), 10) + '...':<36} ║
║  Kullanıcı: {GITHUB_USER:<36} ║
╚══════════════════════════════════════════════════╝
""")

    repolar = repolari_listele()
    print(f"📦 Toplam {len(repolar)} repo bulundu\n")

    if mode == "list":
        for repo in repolar:
            name = repo["name"]
            hooks = mevcut_webhooks(name)
            if hooks:
                print(f"  📎 {name}: {len(hooks)} webhook")
                for h in hooks:
                    url = h.get("config", {}).get("url", "?")
                    events = h.get("events", [])
                    active = "✅" if h.get("active") else "❌"
                    print(f"     {active} #{h['id']} → {url} ({','.join(events)})")
            else:
                print(f"  ⚪ {name}: webhook yok")
        return

    if mode == "delete":
        deleted = 0
        for repo in repolar:
            name = repo["name"]
            hooks = mevcut_webhooks(name)
            for h in hooks:
                status = webhook_sil(name, h["id"])
                if status == 204:
                    print(f"  🗑️  {name} → #{h['id']} silindi")
                    deleted += 1
                else:
                    print(f"  ❌ {name} → #{h['id']} silinemedi ({status})")
        print(f"\n🗑️  Toplam {deleted} webhook silindi")
        return

    # dry-run veya apply
    eklenen = 0
    atlanan = 0
    hatali = 0

    for repo in repolar:
        name = repo["name"]

        # Mevcut webhook'ları kontrol et — aynı URL varsa ekleme
        hooks = mevcut_webhooks(name)
        zaten_var = any(
            h.get("config", {}).get("url", "") == WEBHOOK_URL
            for h in hooks
        )

        if zaten_var:
            print(f"  ⏭️  {name}: Webhook zaten mevcut, atlandı")
            atlanan += 1
            continue

        if mode == "dry-run":
            print(f"  🔍 {name}: Webhook eklenecek (dry-run)")
            eklenen += 1
        else:
            status, data = webhook_ekle(name, WEBHOOK_URL, WEBHOOK_SECRET)
            if status == 201:
                print(f"  ✅ {name}: Webhook eklendi (#{data.get('id', '?')})")
                eklenen += 1
            else:
                msg = data.get("message", str(status))
                print(f"  ❌ {name}: Hata — {msg}")
                hatali += 1

    print(f"""
╔══════════════════════════════════════════════════╗
║  Sonuç                                           ║
╠══════════════════════════════════════════════════╣
║  Eklenen : {eklenen:<37} ║
║  Atlanan : {atlanan:<37} ║
║  Hatalı  : {hatali:<37} ║
║  Toplam  : {len(repolar):<37} ║
╚══════════════════════════════════════════════════╝
""")

    if mode == "dry-run":
        print("💡 Uygulamak için: python3 setup_webhooks.py --apply")
        print("⚠️  WEBHOOK_SERVER değişkenini sunucu IP/domain ile güncelleyin!")


if __name__ == "__main__":
    main()
