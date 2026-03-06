#!/usr/bin/env python3
"""
Emare Projeleri GitHub Toplu Yükleme Scripti
Tüm Emare projelerini GitHub'a repo oluşturup yükler.
"""

import subprocess
import json
import urllib.request
import os
import sys
import time

GITHUB_TOKEN = None
GITHUB_USER = "emraresoftware"
BASE_DIR = "/Users/emre/Desktop/Emare"
PROJECTS_JSON = os.path.join(BASE_DIR, "projects.json")

# Yüklenecek projeler: (klasör_adı, repo_adı, açıklama)
PROJECTS = [
    ("emareasistan", "emareasistan", "Multi-tenant SaaS AI müşteri hizmetleri platformu — WhatsApp/Telegram/Instagram otomasyonu"),
    ("emarecloud", "emarecloud", "Multi-tenant altyapı yönetim paneli — SSH, firewall, LXD, marketplace, Cloudflare"),
    ("Emare Finance", "emare-finance", "Multi-tenant SaaS POS + işletme yönetim yazılımı — e-Fatura, SMS, pazarlama, AI asistan"),
    ("emarepos", "emarepos", "Restoran/kafe için web tabanlı POS + adisyon yönetim sistemi"),
    ("emare desk", "emaredesk", "Python + Web tabanlı uzak masaüstü yazılımı — WebSocket ekran akışı"),
    ("emaresetup", "emaresetup", "AI destekli yazılım fabrikası CLI — doğal dil ile modül üretimi"),
    ("EmareHup", "emarehup", "Yazılım fabrikası ana üssü + DevM otonom geliştirme platformu"),
    ("Emarebot", "emarebot", "Trendyol kozmetik mağazası müşteri soru yanıtlama uygulaması"),
    ("emarecc", "emarecc", "AI destekli çağrı merkezi — Asterisk VoIP, NLP, otomatik raporlama"),
    ("emareai", "emareai", "Emare AI — Ollama/Gemini hibrit yapay zeka motoru"),
    ("emare code", "emare-code", "Emare Code — AI destekli yazılım geliştirme aracı"),
    ("Emare os", "emareos", "EmareOS — Rust tabanlı nöro-çekirdek işletim sistemi"),
    ("Emare Log", "emare-log", "EmareLog — Log yönetim ve analiz sistemi"),
    ("Emaremakale", "emaremakale", "Emare Makale — AI destekli makale toplama ve üretme aracı"),
    ("Emaresiber", "emaresiber", "Emare Siber — Çok ajanlı siber güvenlik platformu"),
    ("emareads", "emareads", "Emare Ads — Reklam yönetim platformu"),
    ("emaredatabase", "emaredatabase", "Emare Database — Özel veritabanı motoru"),
    ("emareflow", "emareflow", "Emare Flow — İş akışı otomasyon motoru"),
    ("emarekatip", "emarekatip", "Emare Katip — Yazılım analiz ve raporlama aracı"),
    ("emareteam", "emareteam", "Emare Team — Takım yönetim paneli"),
    ("emareulak", "emareulak", "Emare Ulak — Neural Network tabanlı mesajlaşma/haberleşme sistemi"),
    ("emarevscodeasistan", "emarevscodeasistan", "Emare VSCode Asistan — VS Code senkronizasyon aracı"),
    ("emarework", "emarework", "Emare Work — Yazılım geliştirme koordinasyon sistemi"),
    ("emareapi", "emareapi", "Emare API — Merkezi API gateway ve derviş mimarisi"),
    ("emare_dashboard", "emare-dashboard", "Emare Dashboard — Proje izleme paneli"),
    ("emare-token", "emare-token", "Emare Token — Token yönetim sistemi"),
    ("EMARE_ORTAK_CALISMA", "emare-ortak-calisma", "Emare Ortak Çalışma — AI kolektif hafıza ve anayasa"),
]


def projeleri_yukle():
    """projects.json dosyasından proje listesini yükler, hata olursa sabit listeye düşer."""
    if not os.path.exists(PROJECTS_JSON):
        print(f"⚠️  {PROJECTS_JSON} bulunamadı, sabit liste kullanılacak")
        return PROJECTS

    try:
        with open(PROJECTS_JSON, "r", encoding="utf-8") as f:
            kayitlar = json.load(f)
    except Exception as e:
        print(f"⚠️  projects.json okunamadı ({e}), sabit liste kullanılacak")
        return PROJECTS

    projeler = []
    for kayit in kayitlar:
        proje_id = str(kayit.get("id", "")).strip()
        aciklama = str(kayit.get("description", "")).strip()
        proje_yolu = str(kayit.get("path", "")).strip()

        if not proje_id or not proje_yolu:
            continue

        klasor_adi = os.path.basename(proje_yolu.rstrip("/"))
        if not klasor_adi:
            continue

        if not aciklama:
            aciklama = f"{proje_id} projesi"

        projeler.append((klasor_adi, proje_id, aciklama))

    if not projeler:
        print("⚠️  projects.json içinden geçerli proje çıkarılamadı, sabit liste kullanılacak")
        return PROJECTS

    print(f"✅ Proje listesi projects.json üzerinden yüklendi: {len(projeler)} kayıt")
    return projeler


def github_tokenunu_yukle():
    """GitHub token'ı ortam değişkeni veya .github_token dosyasından yükler."""
    env_token = os.getenv("GITHUB_TOKEN", "").strip()
    if env_token:
        return env_token

    aday_dosyalar = [
        os.path.join(BASE_DIR, ".github_token"),
        os.path.join(BASE_DIR, "EMARE_ORTAK_CALISMA", ".github_token"),
    ]
    for dosya in aday_dosyalar:
        if os.path.exists(dosya):
            try:
                with open(dosya, "r", encoding="utf-8") as f:
                    token = f.read().strip()
                if token:
                    return token
            except Exception:
                continue

    raise RuntimeError(
        "GITHUB_TOKEN bulunamadı.\n"
        "Çözüm: ortam değişkeni ayarla veya /Users/emre/Desktop/Emare/.github_token dosyasına yaz."
    )

# Standart .gitignore içeriği
GITIGNORE_CONTENT = """# Dependencies
node_modules/
vendor/
.venv/
venv/
__pycache__/
*.pyc

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.cursor/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
target/
*.egg-info/

# Logs
*.log
logs/

# Database
*.db
*.sqlite3
instance/

# Misc
*.zip
*.tar.gz
.coverage
.pytest_cache/
.ruff_cache/
"""


def run_cmd(cmd, cwd=None):
    """Komut çalıştır ve sonucu döndür"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=120)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def github_api(method, endpoint, data=None):
    """GitHub API çağrısı yap"""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {"message": body}


def create_repo(repo_name, description):
    """GitHub'da repo oluştur"""
    status, resp = github_api("POST", "/user/repos", {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False,
    })
    
    if status == 201:
        print(f"  ✅ Repo oluşturuldu: {repo_name}")
        return True
    elif status == 422 and "already exists" in str(resp):
        print(f"  ℹ️  Repo zaten mevcut: {repo_name}")
        return True
    else:
        print(f"  ❌ Repo oluşturulamadı: {repo_name} — {resp.get('message', resp)}")
        return False


def push_project(folder_name, repo_name, description, force_push=False):
    """Projeyi GitHub'a yükle"""
    project_path = os.path.join(BASE_DIR, folder_name)
    
    if not os.path.isdir(project_path):
        print(f"  ⚠️  Klasör bulunamadı: {folder_name}")
        return False
    
    # Klasör boş mu kontrol et
    contents = [f for f in os.listdir(project_path) if f != '.DS_Store' and f != 'EMARE_ORTAK_CALISMA']
    if not contents:
        print(f"  ⚠️  Klasör boş: {folder_name}")
        return False
    
    print(f"\n📦 {folder_name} → github.com/{GITHUB_USER}/{repo_name}")
    
    # 1. GitHub'da repo oluştur
    if not create_repo(repo_name, description):
        return False
    
    # 2. .gitignore ekle (yoksa)
    gitignore_path = os.path.join(project_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(GITIGNORE_CONTENT)
        print("  📝 .gitignore oluşturuldu")
    
    # 3. Git başlat (yoksa)
    git_dir = os.path.join(project_path, ".git")
    if not os.path.isdir(git_dir):
        run_cmd("git init", cwd=project_path)
        print("  🔧 git init yapıldı")
    
    # 4. Git config
    run_cmd('git config user.email "emraresoftware@users.noreply.github.com"', cwd=project_path)
    run_cmd('git config user.name "emraresoftware"', cwd=project_path)
    
    # 5. Remote ekle/güncelle
    remote_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
    run_cmd("git remote remove origin", cwd=project_path)
    run_cmd(f'git remote add origin "{remote_url}"', cwd=project_path)
    
    # 6. Tüm dosyaları ekle
    run_cmd("git add -A", cwd=project_path)
    
    # 7. Commit
    code, out, err = run_cmd('git commit -m "İlk yükleme — Emare projesi"', cwd=project_path)
    if code == 0:
        print("  💾 Commit yapıldı")
    elif "nothing to commit" in (out + err):
        print("  ℹ️  Zaten commit edilmiş, değişiklik yok")
    
    # 8. Branch adını main yap
    run_cmd("git branch -M main", cwd=project_path)
    
    # 9. Push
    push_cmd = "git push -u origin main --force" if force_push else "git push -u origin main"
    code, out, err = run_cmd(push_cmd, cwd=project_path)
    if code == 0:
        print(f"  🚀 Push başarılı! → https://github.com/{GITHUB_USER}/{repo_name}")
        return True
    else:
        print(f"  ❌ Push hatası: {err[:200]}")
        return False


def main():
    global GITHUB_TOKEN
    GITHUB_TOKEN = github_tokenunu_yukle()

    force_push = "--force-push" in sys.argv

    projeler = projeleri_yukle()

    print("=" * 60)
    print("🏗️  EMARE PROJELERİ GITHUB TOPLU YÜKLEME")
    print(f"👤 Kullanıcı: {GITHUB_USER}")
    print(f"📁 Kaynak: {BASE_DIR}")
    print(f"📊 Toplam proje: {len(projeler)}")
    print(f"⚙️  Push modu: {'FORCE' if force_push else 'NORMAL'}")
    print("=" * 60)
    
    success = 0
    failed = 0
    skipped = 0
    
    for folder_name, repo_name, description in projeler:
        try:
            result = push_project(folder_name, repo_name, description, force_push=force_push)
            if result:
                success += 1
            elif result is False:
                project_path = os.path.join(BASE_DIR, folder_name)
                if not os.path.isdir(project_path):
                    skipped += 1
                else:
                    contents = [f for f in os.listdir(project_path) if f != '.DS_Store' and f != 'EMARE_ORTAK_CALISMA']
                    if not contents:
                        skipped += 1
                    else:
                        failed += 1
            time.sleep(1)  # GitHub API rate limit için kısa bekleme
        except Exception as e:
            print(f"  ❌ Hata: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 SONUÇ RAPORU")
    print(f"  ✅ Başarılı: {success}")
    print(f"  ❌ Başarısız: {failed}")
    print(f"  ⚠️  Atlanan: {skipped}")
    print(f"  🔗 GitHub: https://github.com/{GITHUB_USER}?tab=repositories")
    print("=" * 60)


if __name__ == "__main__":
    main()
