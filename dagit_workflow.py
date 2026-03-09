#!/usr/bin/env python3
"""
Tüm Emare projelerine mesaj-alici workflow + güncellenmiş copilot-instructions dağıt.
Adımlar:
1. mesaj-alici.yml workflow'u tüm projelere kopyala
2. copilot-instructions.md'yi YENI_MESAJ.md kontrolü ekleyerek güncelle
3. Her projeyi commit + push et
4. Merkezi mesaj-dagitici.yml'yi de commit + push et
"""
import os
import re
import subprocess
import shutil

EMARE_DIR = "/Users/emre/Desktop/Emare"
ORTAK = os.path.join(EMARE_DIR, "EMARE_ORTAK_CALISMA")
KAYNAK_WORKFLOW = os.path.join(EMARE_DIR, "emaregithup", ".github", "workflows", "mesaj-alici.yml")

ATLA = {"EMARE_ORTAK_CALISMA", ".git", "__pycache__", "node_modules", "emareasistan"}

# copilot-instructions template
TEMPLATE = '''# 🧠 Emare Derviş Copilot Talimatları

## Sen Kimsin?
Sen bir **Emare Dervişi**sin. Bu projenin yapay zeka geliştirme asistanısın. Emare ekosisteminde 43+ proje birlikte çalışır ve sen bu kolektifin bir üyesisin.

## ⚡ OTOMATİK MESAJ KONTROLÜ (HER OTURUMDA ZORUNLU)

> **Bu talimat her yanıttan önce geçerlidir. Oturumda henüz mesaj kontrolü yapılmadıysa, kullanıcının ilk isteğine yanıt vermeden ÖNCE aşağıdaki komutu çalıştır:**

```bash
python3 EMARE_ORTAK_CALISMA/emare_messenger.py {DERVIS_ADI} oku
```

- Bu komut mesaj kutusu kontrolüdür ve **ONAY BEKLEMEDEN** çalıştırılmalıdır.
- 🔴 **Acil mesaj** varsa → Kullanıcıya hemen bildir ve önce onu çöz
- 📢 **Duyuru** varsa → Kullanıcıya özetle
- 📨 **Normal mesaj** varsa → Not al, kullanıcıya bildir
- ✅ Mesaj yoksa veya sadece eski mesajlar varsa → Sessizce devam et

**Bu adımı atlamak yasaktır.** Oturumda bir kez yapılması yeterlidir.

### 🔔 Push Bildirim Kontrolü

Eğer `.github/YENI_MESAJ.md` dosyası varsa, içeriğini oku ve kullanıcıya bildir.
Bu dosya GitHub Actions tarafından yeni mesaj geldiğinde otomatik oluşturulur.

Mesajı okuduktan sonra dosyayı sil:
```bash
rm -f .github/YENI_MESAJ.md && git add -A && git commit -m "docs: mesaj okundu" && git push
```

## Oturum Başlangıç Protokolü (İLK FIRSATTA)

Kullanıcı ilk isteğini verdikten sonra, arka planda şu dosyaları oku:

### 1. Anayasayı Oku
```
EMARE_ORTAK_CALISMA/EMARE_ANAYASA.md
```

### 2. Hafızayı Oku
```
EMARE_ORTAK_CALISMA/EMARE_ORTAK_HAFIZA.md
EMARE_ORTAK_CALISMA/EMARE_AI_COLLECTIVE.md
```

### 3. Proje Hafızasını Oku
```
{PROJE_ADI}_hafiza.md
DOSYA_YAPISI.md
```

## Haberleşme Sistemi

Başka dervişlerle iletişim kurmak için `emare_messenger.py` kullan:

```python
from emare_messenger import EmareMesaj

mesaj = EmareMesaj("{DERVIS_ADI}")

# Birine mesaj gönder
mesaj.gonder("hedef_dervis", "Mesaj içeriği")

# Herkese duyuru
mesaj.gonder_herkese("Duyuru içeriği")

# Mesajları oku
mesaj.oku()

# Yanıt ver
mesaj.yanit(issue_no, "Yanıt")
```

### Ne Zaman Mesaj Gönder?
- ✅ API endpoint değiştiğinde → etkilenen dervişlere bildir
- ✅ Breaking change yaptığında → herkese duyur
- ✅ Kritik bug bulduğunda → acil mesaj gönder
- ✅ Yeni servis/modül eklediğinde → duyur
- ✅ Başka dervişin API'sine ihtiyacın olduğunda → o dervişe sor

### Mesaj Formatı
```
[Ne yapıldı]. [Detay/Endpoint/Versiyon]. [Etki/Breaking change varsa].
```

## Genel Kurallar
- EMARE_ORTAK_CALISMA bir **symlink**'tir, doğrudan değiştirme
- Token: `GITHUB_TOKEN` ortam değişkeninden veya `.github_token` dosyasından okunur
- Tüm kod Emare Anayasası'na uygun olmalı (18 madde)
- Türkçe fonksiyon/değişken adı kullan (mümkün olduğunca)
- Her değişikliği commit et: `git commit -m "feat|fix|docs: açıklama"`
'''


def dervis_adi_bul(proje_dir):
    """Proje dizininden derviş adını çıkar"""
    dirname = os.path.basename(proje_dir)
    ci_path = os.path.join(proje_dir, ".github", "copilot-instructions.md")
    if os.path.exists(ci_path):
        with open(ci_path) as f:
            content = f.read()
        m = re.search(r'emare_messenger\.py\s+(\w+)\s+oku', content)
        if m:
            return m.group(1)
    return dirname


def git_push(proje_dir, commit_msg):
    """Git add, commit, push"""
    try:
        subprocess.run(["git", "add", "-A"], cwd=proje_dir, capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=proje_dir, capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return "skip"  # Değişiklik yok
        
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=proje_dir, capture_output=True, timeout=15
        )
        push = subprocess.run(
            ["git", "push"],
            cwd=proje_dir, capture_output=True, timeout=30
        )
        if push.returncode != 0:
            return f"push-hata: {push.stderr.decode()[:100]}"
        return "ok"
    except Exception as e:
        return f"hata: {e}"


def main():
    # 1. Projeleri bul
    projeler = []
    for item in sorted(os.listdir(EMARE_DIR)):
        full = os.path.join(EMARE_DIR, item)
        if not os.path.isdir(full):
            continue
        if item in ATLA or item.startswith("."):
            continue
        github_dir = os.path.join(full, ".github")
        if os.path.exists(github_dir):
            projeler.append(full)
    
    print(f"{'='*60}")
    print(f"  EMARE WORKFLOW DAĞITIM SİSTEMİ")
    print(f"  {len(projeler)} proje bulundu")
    print(f"{'='*60}\n")
    
    # 2. Workflow dosyasını kontrol et
    if not os.path.exists(KAYNAK_WORKFLOW):
        print(f"❌ Kaynak workflow bulunamadı: {KAYNAK_WORKFLOW}")
        return
    
    with open(KAYNAK_WORKFLOW) as f:
        workflow_icerik = f.read()
    
    istatistik = {"workflow": 0, "instructions": 0, "push_ok": 0, "push_skip": 0, "push_hata": 0}
    
    for proje_dir in projeler:
        proje_adi = os.path.basename(proje_dir)
        dervis = dervis_adi_bul(proje_dir)
        print(f"\n📦 {proje_adi} ({dervis})")
        
        # 2a. Workflow kopyala
        wf_dir = os.path.join(proje_dir, ".github", "workflows")
        os.makedirs(wf_dir, exist_ok=True)
        wf_hedef = os.path.join(wf_dir, "mesaj-alici.yml")
        
        with open(wf_hedef, "w") as f:
            f.write(workflow_icerik)
        istatistik["workflow"] += 1
        print(f"  ✅ workflow kopyalandı")
        
        # 2b. copilot-instructions güncelle
        ci_path = os.path.join(proje_dir, ".github", "copilot-instructions.md")
        yeni_icerik = TEMPLATE.replace("{DERVIS_ADI}", dervis).replace("{PROJE_ADI}", proje_adi)
        
        with open(ci_path, "w") as f:
            f.write(yeni_icerik)
        istatistik["instructions"] += 1
        print(f"  ✅ copilot-instructions güncellendi")
        
        # 2c. Commit + Push
        sonuc = git_push(proje_dir, "feat: mesaj-alici workflow + push bildirim sistemi")
        if sonuc == "ok":
            istatistik["push_ok"] += 1
            print(f"  🚀 push başarılı")
        elif sonuc == "skip":
            istatistik["push_skip"] += 1
            print(f"  ⏭️  değişiklik yok")
        else:
            istatistik["push_hata"] += 1
            print(f"  ❌ {sonuc}")
    
    # 3. Merkezi workflow'u da push et (EMARE_ORTAK_CALISMA)
    print(f"\n{'='*60}")
    print(f"📡 Merkezi workflow (EMARE_ORTAK_CALISMA)")
    merkez_sonuc = git_push(ORTAK, "feat: mesaj-dagitici merkezi workflow eklendi")
    if merkez_sonuc == "ok":
        print(f"  🚀 merkez push başarılı")
    elif merkez_sonuc == "skip":
        print(f"  ⏭️  merkez değişiklik yok")
    else:
        print(f"  ❌ merkez: {merkez_sonuc}")
    
    # 4. Sonuç
    print(f"\n{'='*60}")
    print(f"  SONUÇ RAPORU")
    print(f"{'='*60}")
    print(f"  Workflow kopyalanan: {istatistik['workflow']}")
    print(f"  Instructions güncellenen: {istatistik['instructions']}")
    print(f"  Push başarılı: {istatistik['push_ok']}")
    print(f"  Push atlandı (değişiklik yok): {istatistik['push_skip']}")
    print(f"  Push hatalı: {istatistik['push_hata']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
