#!/usr/bin/env python3
"""
Tüm Emare projelerinde auto_deploy_on_push = true yap.
deploy.json olmayanlar için oluştur.
Her değişikliği commit + push yap.
"""
import json
import os
import subprocess
import urllib.request

BASE = "/Users/emre/Desktop/Emare"
GITHUB_USER = "emraresoftware"

# Token oku
token = ""
token_path = os.path.join(BASE, "EMARE_ORTAK_CALISMA", ".github_token")
if os.path.exists(token_path):
    with open(token_path) as f:
        token = f.read().strip()

# GitHub'daki tüm repoları al
def github_repolari():
    repos = []
    page = 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&page={page}",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return {r["name"]: r for r in repos}

# Klasör → repo eşleştirme
def klasor_repo_esle():
    """Lokal klasörleri GitHub repo adlarıyla eşleştir."""
    github_repos = github_repolari()
    print(f"📦 GitHub'da {len(github_repos)} repo bulundu\n")
    
    # Tüm klasörleri listele
    klasorler = []
    skip = {"EMARE_ORTAK_CALISMA", ".git", "__pycache__", "node_modules", ".venv"}
    for item in os.listdir(BASE):
        full = os.path.join(BASE, item)
        if os.path.isdir(full) and item not in skip and not item.startswith("."):
            klasorler.append(full)
    
    print(f"📂 Lokalde {len(klasorler)} klasör bulundu\n")
    return klasorler, github_repos

def repo_adi_bul(klasor, github_repos):
    """Klasör adından repo adını tahmin et."""
    isim = os.path.basename(klasor)
    # Doğrudan eşleşme
    if isim in github_repos:
        return isim
    # Küçük harf
    for repo in github_repos:
        if repo.lower() == isim.lower():
            return repo
    # Tire ile
    alt = isim.replace(" ", "-").replace("_", "-")
    for repo in github_repos:
        if repo.lower() == alt.lower():
            return repo
    return None

def deploy_json_olustur(klasor, repo_adi):
    """Standart deploy.json oluştur."""
    slug = repo_adi.lower().replace(" ", "-")
    return {
        "slug": slug,
        "name": os.path.basename(klasor),
        "github_repo": f"{GITHUB_USER}/{repo_adi}",
        "branch": "main",
        "dc": "local",
        "server_host": None,
        "server_ssh_port": 22,
        "remote_path": f"/opt/{slug}",
        "stack": "auto",
        "port": None,
        "domain": "",
        "deploy_commands": [
            f"cd /opt/{slug}",
            "git pull origin main"
        ],
        "restart_command": None,
        "auto_deploy_on_push": True,
        "health_check_url": None
    }

def git_commit_push(klasor, mesaj):
    """Klasördeki değişikliği commit ve push yap."""
    try:
        # git repo mu kontrol et
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=klasor, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"    ⚠️  Git repo değil, atlanıyor")
            return False
        
        subprocess.run(["git", "add", "deploy.json"], cwd=klasor, capture_output=True)
        
        # Değişiklik var mı?
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=klasor, capture_output=True
        )
        if result.returncode == 0:
            print(f"    ℹ️  Değişiklik yok (zaten güncel)")
            return True
        
        subprocess.run(
            ["git", "commit", "-m", mesaj],
            cwd=klasor, capture_output=True, text=True
        )
        
        # Branch adını bul
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=klasor, capture_output=True, text=True
        )
        branch = branch_result.stdout.strip() or "main"
        
        result = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=klasor, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"    ✅ Push başarılı ({branch})")
            return True
        else:
            print(f"    ❌ Push hatası: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"    ❌ Hata: {e}")
        return False

def main():
    klasorler, github_repos = klasor_repo_esle()
    
    guncellenen = 0
    olusturulan = 0
    hatali = 0
    zaten_true = 0
    
    for klasor in sorted(klasorler):
        isim = os.path.basename(klasor)
        deploy_path = os.path.join(klasor, "deploy.json")
        repo_adi = repo_adi_bul(klasor, github_repos)
        
        print(f"📁 {isim}", end="")
        if repo_adi:
            print(f" (repo: {repo_adi})")
        else:
            print(f" (GitHub repo bulunamadı, atlanıyor)")
            continue
        
        if os.path.exists(deploy_path):
            # Mevcut deploy.json'ı güncelle
            with open(deploy_path) as f:
                data = json.load(f)
            
            current = data.get("auto_deploy_on_push", data.get("auto_deploy", False))
            if current == True:
                print(f"    ✅ Zaten auto_deploy=true")
                zaten_true += 1
                continue
            
            # auto_deploy_on_push = true yap
            data["auto_deploy_on_push"] = True
            # Eski key varsa kaldır
            if "auto_deploy" in data and "auto_deploy_on_push" in data:
                del data["auto_deploy"]
            
            with open(deploy_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
            print(f"    🔄 auto_deploy_on_push → true")
            git_commit_push(klasor, "feat: auto_deploy_on_push aktif edildi")
            guncellenen += 1
        else:
            # deploy.json oluştur
            data = deploy_json_olustur(klasor, repo_adi)
            with open(deploy_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
            print(f"    🆕 deploy.json oluşturuldu (auto_deploy=true)")
            git_commit_push(klasor, "feat: deploy.json oluşturuldu, auto_deploy aktif")
            olusturulan += 1
    
    print(f"""
╔══════════════════════════════════════════════════╗
║  Auto Deploy Güncelleme Sonucu                   ║
╠══════════════════════════════════════════════════╣
║  Zaten true  : {zaten_true:<33} ║
║  Güncellenen : {guncellenen:<33} ║
║  Oluşturulan : {olusturulan:<33} ║
║  Hatalı      : {hatali:<33} ║
║  Toplam      : {len(klasorler):<33} ║
╚══════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    main()
