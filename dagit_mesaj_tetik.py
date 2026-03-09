#!/usr/bin/env python3
"""
Tüm Emare projelerine güncellenmiş copilot-instructions.md dağıt.
Mesaj kontrol mekanizmasını güçlendirilmiş haliyle tüm dervişlere yayar.
"""
import os
import json
import re

EMARE_DIR = "/Users/emre/Desktop/Emare"
ORTAK = os.path.join(EMARE_DIR, "EMARE_ORTAK_CALISMA")

# Template — {DERVIS_ADI} ve {PROJE_ADI} değiştirilecek
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
    # Eğer mevcut copilot-instructions varsa, oradan oku
    ci_path = os.path.join(proje_dir, ".github", "copilot-instructions.md")
    if os.path.exists(ci_path):
        with open(ci_path) as f:
            content = f.read()
        # emare_messenger.py XXXX oku pattern'ini ara
        m = re.search(r'emare_messenger\.py\s+(\w+)\s+oku', content)
        if m:
            return m.group(1)
    return dirname


def main():
    # Projeleri bul
    projeler = []
    atla = {"EMARE_ORTAK_CALISMA", ".git", "__pycache__", "node_modules", "emareasistan"}
    
    for item in sorted(os.listdir(EMARE_DIR)):
        full = os.path.join(EMARE_DIR, item)
        if not os.path.isdir(full):
            continue
        if item in atla or item.startswith("."):
            continue
        # .github dizini olan projeler
        github_dir = os.path.join(full, ".github")
        if os.path.exists(github_dir):
            projeler.append(full)
    
    print(f"Toplam {len(projeler)} proje bulundu\n")
    
    guncellenen = 0
    zaten_guncel = 0
    hata = 0
    
    for proje_dir in projeler:
        proje_adi = os.path.basename(proje_dir)
        dervis = dervis_adi_bul(proje_dir)
        
        ci_path = os.path.join(proje_dir, ".github", "copilot-instructions.md")
        
        # Template'i doldur
        yeni_icerik = TEMPLATE.replace("{DERVIS_ADI}", dervis).replace("{PROJE_ADI}", proje_adi)
        
        # Mevcut dosyayı kontrol et
        if os.path.exists(ci_path):
            with open(ci_path) as f:
                mevcut = f.read()
            # Zaten güncel mi?
            if "OTOMATİK MESAJ KONTROLÜ" in mevcut and "ONAY BEKLEMEDEN" in mevcut:
                zaten_guncel += 1
                print(f"  ✓ {proje_adi} ({dervis}) — zaten güncel")
                continue
        
        # Yaz
        try:
            os.makedirs(os.path.dirname(ci_path), exist_ok=True)
            with open(ci_path, "w") as f:
                f.write(yeni_icerik)
            guncellenen += 1
            print(f"  ✅ {proje_adi} ({dervis}) — güncellendi")
        except Exception as e:
            hata += 1
            print(f"  ❌ {proje_adi} ({dervis}) — HATA: {e}")
    
    print(f"\n{'='*50}")
    print(f"Güncellenen: {guncellenen}")
    print(f"Zaten güncel: {zaten_guncel}")
    print(f"Hata: {hata}")
    print(f"Toplam: {len(projeler)}")


if __name__ == "__main__":
    main()
