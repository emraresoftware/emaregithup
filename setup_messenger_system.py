#!/usr/bin/env python3
"""
Tüm Emare projelerine haberleşme sistemi kurulumunu dağıtır:
1. emare_messenger.py (güncellenmiş, token dosyasından okuma destekli)
2. .github/copilot-instructions.md (her projeye özel)
3. .github_token (EMARE_ORTAK_CALISMA symlink'inden okunur)
"""

import os
import shutil

EMARE_BASE = "/Users/emre/Desktop/Emare"
ORTAK = os.path.join(EMARE_BASE, "EMARE_ORTAK_CALISMA")
MESSENGER_SRC = os.path.join(ORTAK, "emare_messenger.py")
INSTRUCTIONS_SRC = os.path.join(ORTAK, ".github", "copilot-instructions.md")

# Dağıtılmayacak klasörler
SKIP = {
    ".hub_venv", ".vscode", "_EMARE_TASIMA", "data", "hub_templates",
    "emare-token", "EMARE_ORTAK_CALISMA", ".git", "node_modules",
    "__pycache__", ".venv", "venv"
}

def get_project_dirs():
    """Emare altındaki proje klasörlerini bul."""
    projects = []
    for name in sorted(os.listdir(EMARE_BASE)):
        path = os.path.join(EMARE_BASE, name)
        if not os.path.isdir(path):
            continue
        if name.startswith("."):
            continue
        if name in SKIP:
            continue
        projects.append((name, path))
    return projects

def get_dervis_name(folder_name):
    """Klasör adından derviş adını türet."""
    # Boşlukları ve büyük harfleri normalize et
    return folder_name.lower().replace(" ", "").replace("-", "")

def distribute():
    projects = get_project_dirs()
    success = 0
    
    print(f"🚀 Haberleşme sistemi dağıtımı başlıyor...")
    print(f"📦 Kaynak: {ORTAK}")
    print(f"📋 Hedef: {len(projects)} proje\n")
    
    for name, path in projects:
        dervis_name = get_dervis_name(name)
        
        # 1. emare_messenger.py kopyala
        dst_messenger = os.path.join(path, "emare_messenger.py")
        shutil.copy2(MESSENGER_SRC, dst_messenger)
        
        # 2. .github/copilot-instructions.md oluştur (projeye özel)
        github_dir = os.path.join(path, ".github")
        os.makedirs(github_dir, exist_ok=True)
        
        # Template'i oku ve proje adını yerleştir
        with open(INSTRUCTIONS_SRC, "r") as f:
            template = f.read()
        
        # Proje adını yerleştir
        personalized = template.replace("<bu_proje_adi>", dervis_name)
        personalized = personalized.replace("<proje_adi>", dervis_name)
        
        dst_instructions = os.path.join(github_dir, "copilot-instructions.md")
        with open(dst_instructions, "w") as f:
            f.write(personalized)
        
        success += 1
        print(f"  ✅ {name} → ({dervis_name})")
    
    print(f"\n🎉 Toplam: {success}/{len(projects)} projeye dağıtıldı")
    print(f"\n📌 Token kaynakları:")
    print(f"   1. ~/.zshrc (ortam değişkeni - TÜM terminaller)")
    print(f"   2. EMARE_ORTAK_CALISMA/.github_token (dosya)")
    print(f"   3. Her projedeki symlink → EMARE_ORTAK_CALISMA/.github_token")

if __name__ == "__main__":
    distribute()
