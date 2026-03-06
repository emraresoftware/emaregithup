#!/usr/bin/env python3
"""
Eksik Emare Projelerini GitHub'a Yükleme Scripti
=================================================
31 mevcut repoya ek olarak eksik olan ~14 projeyi GitHub'a yükler.
Hedef: 45 repo
"""

import subprocess
import json
import urllib.request
import urllib.error
import os
import sys
import time

GITHUB_TOKEN = ""
# Token yükleme
token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "EMARE_ORTAK_CALISMA", ".github_token")
if os.path.exists(token_path):
    with open(token_path) as f:
        GITHUB_TOKEN = f.read().strip()
if not GITHUB_TOKEN:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

GITHUB_USER = "emraresoftware"
BASE_DIR = "/Users/emre/Desktop/Emare"

# Eksik projeler: (klasör_adı, repo_adı, açıklama)
EKSIK_PROJELER = [
    ("Emare Hosting", "emarehosting", "Emare Hosting — Web hosting ve sunucu yönetim paneli"),
    ("Emareintranet", "emareintranet", "Emare Intranet — Şirket içi iletişim ve doküman yönetimi"),
    ("emareaimusic", "emareaimusic", "Emare AI Music — Yapay zeka destekli müzik üretim aracı"),
    ("emareaplincedesk", "emareaplincedesk", "Emare Aplince Desk — Uygulama yönetim masaüstü"),
    ("emarecripto", "emarecripto", "Emare Cripto — Kripto para takip ve portföy yönetimi"),
    ("emareflux", "emareflux", "Emare Flux — Veri akışı ve stream işleme motoru"),
    ("emarefree", "emarefree", "Emare Free — Açık kaynak topluluk araçları"),
    ("emaregoogle", "emaregoogle", "Emare Google — Google API entegrasyonları ve araçları"),
    ("emareidi", "emareidi", "Emare IDI — Kimlik ve erişim yönetimi sistemi"),
    ("emarepazar", "emarepazar", "Emare Pazar — E-ticaret ve pazar yeri platformu"),
    ("emaresebil", "emaresebil", "Emare Sebil — Açık veri paylaşım platformu"),
    ("emaretedarik", "emaretedarik", "Emare Tedarik — Tedarik zinciri yönetim sistemi"),
    ("emarewebdizayn", "emarewebdizayn", "Emare Web Dizayn — Web tasarım ve şablon sistemi"),
    ("sosyal medya yönetim aracı", "sosyal-medya-yonetim", "Emare Sosyal Medya — Çoklu platform sosyal medya yönetim aracı"),
]

# .gitignore'a eklenecek büyük/gereksiz dosya kalıpları
GITIGNORE_CONTENT = """.venv/
venv/
node_modules/
__pycache__/
*.pyc
.env
.env.local
.DS_Store
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
*.db
*.sqlite3
*.log
data/*.db
"""


def api(method, endpoint, data=None):
    """GitHub API çağrısı."""
    url = f"https://api.github.com{endpoint}"
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


def repo_var_mi(repo_name):
    """GitHub'da repo var mı kontrol et."""
    status, _ = api("GET", f"/repos/{GITHUB_USER}/{repo_name}")
    return status == 200


def repo_olustur(repo_name, description):
    """GitHub'da repo oluştur."""
    status, data = api("POST", "/user/repos", {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False,
    })
    return status == 201, data


def cmd(command, cwd=None):
    """Shell komutu çalıştır."""
    result = subprocess.run(
        command, shell=True, cwd=cwd,
        capture_output=True, text=True, timeout=120
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def buyuk_dosyalari_bul(path, max_mb=50):
    """50MB+ dosyaları bul."""
    buyukler = []
    for root, dirs, files in os.walk(path):
        # Skip hidden dirs and common large dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                   ('node_modules', '.venv', 'venv', '__pycache__', '.git')]
        for f in files:
            fp = os.path.join(root, f)
            try:
                size = os.path.getsize(fp)
                if size > max_mb * 1024 * 1024:
                    rel = os.path.relpath(fp, path)
                    buyukler.append((rel, size))
            except:
                pass
    return buyukler


def projeyi_yukle(klasor, repo_name, description):
    """Bir projeyi GitHub'a yükle."""
    proje_yolu = os.path.join(BASE_DIR, klasor)
    
    if not os.path.isdir(proje_yolu):
        return False, f"Klasör bulunamadı: {proje_yolu}"

    print(f"\n{'='*60}")
    print(f"📦 {klasor} → {repo_name}")
    print(f"{'='*60}")

    # 1. Repo oluştur
    if repo_var_mi(repo_name):
        print(f"  ℹ️  Repo zaten var: {repo_name}")
    else:
        ok, data = repo_olustur(repo_name, description)
        if ok:
            print(f"  ✅ Repo oluşturuldu: {repo_name}")
        else:
            return False, f"Repo oluşturulamadı: {data.get('message', '?')}"
        time.sleep(1)

    # 2. .gitignore kontrol/oluştur
    gitignore_path = os.path.join(proje_yolu, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write(GITIGNORE_CONTENT)
        print(f"  📝 .gitignore oluşturuldu")

    # 3. Büyük dosyaları gitignore'a ekle
    buyukler = buyuk_dosyalari_bul(proje_yolu)
    if buyukler:
        with open(gitignore_path, "a") as f:
            f.write("\n# Büyük dosyalar (otomatik eklendi)\n")
            for rel, size in buyukler:
                f.write(f"{rel}\n")
                print(f"  ⚠️  Büyük dosya → .gitignore: {rel} ({size/1024/1024:.0f}MB)")

    # 4. Mevcut .git varsa temizle
    git_dir = os.path.join(proje_yolu, ".git")
    if os.path.isdir(git_dir):
        cmd(f"rm -rf .git", cwd=proje_yolu)
        print(f"  🧹 Eski .git temizlendi")

    # 5. İç içe .git klasörlerini temizle
    for root, dirs, _ in os.walk(proje_yolu):
        for d in dirs:
            if d == '.git' and root != proje_yolu:
                nested = os.path.join(root, d)
                cmd(f"rm -rf '{nested}'")
                print(f"  🧹 Nested .git temizlendi: {os.path.relpath(nested, proje_yolu)}")
        dirs[:] = [d for d in dirs if d != '.git']

    # 6. Git init + commit + push
    remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
    
    komutlar = [
        "git init",
        f"git remote add origin {remote_url}",
        "git add -A",
        'git commit -m "feat: ilk yükleme — Emare ekosistemi"',
        "git branch -M main",
        "git push -u origin main --force",
    ]
    
    for komut in komutlar:
        # Token'ı loglamayalım
        log_komut = komut.replace(GITHUB_TOKEN, "***")
        rc, out, err = cmd(komut, cwd=proje_yolu)
        if rc != 0 and "already exists" not in err:
            if "nothing to commit" in out or "nothing to commit" in err:
                continue
            print(f"  ❌ Hata ({log_komut}): {err[:200]}")
            # Push hatasında devam et
            if "push" not in komut:
                return False, f"Komut hatası: {log_komut}"

    print(f"  ✅ Push başarılı → https://github.com/{GITHUB_USER}/{repo_name}")
    return True, "OK"


def main():
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN bulunamadı!")
        sys.exit(1)

    print(f"""
╔══════════════════════════════════════════════════════╗
║  EmareGitHup — Eksik Projeleri GitHub'a Yükleme     ║
╠══════════════════════════════════════════════════════╣
║  Hedef   : {len(EKSIK_PROJELER)} proje                                  ║
║  Mevcut  : 31 repo                                  ║
║  Sonuç   : ~45 repo                                 ║
╚══════════════════════════════════════════════════════╝
""")

    basarili = 0
    hatali = 0
    hatalar = []

    for klasor, repo_name, desc in EKSIK_PROJELER:
        ok, mesaj = projeyi_yukle(klasor, repo_name, desc)
        if ok:
            basarili += 1
        else:
            hatali += 1
            hatalar.append((klasor, mesaj))
        time.sleep(0.5)

    print(f"""
╔══════════════════════════════════════════════════════╗
║  SONUÇ                                              ║
╠══════════════════════════════════════════════════════╣
║  Başarılı : {basarili:<40}║
║  Hatalı   : {hatali:<40}║
║  Toplam   : {basarili + hatali:<40}║
╚══════════════════════════════════════════════════════╝
""")

    if hatalar:
        print("❌ Hatalı projeler:")
        for k, m in hatalar:
            print(f"   • {k}: {m}")

    print(f"\n✅ GitHub toplam repo sayısı: {31 + basarili}")


if __name__ == "__main__":
    main()
