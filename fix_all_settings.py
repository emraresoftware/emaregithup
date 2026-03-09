#!/usr/bin/env python3
"""
Tüm VS Code settings.json dosyalarını düzenle:
- Global settings: 190 satırlık gereksiz regex'leri temizle, eksik ayarları ekle
- Tüm profiller: auto-approve ayarlarını ekle/düzelt
"""
import json
import re
import os
import glob

# Eklenecek/güncellenecek ayarlar
GEREKLI_AYARLAR = {
    "chat.tools.terminal.autoApprove": {".*": True},
    "chat.tools.autoApprove": True,
    "chat.agent.autoFix": True,
    "chat.tools.terminal.sandbox.enabled": False,
    "chat.tools.terminal.ignoreDefaultAutoApproveRules": False,
    "chat.tools.urls.autoApprove": {"http://*": True, "https://*": True},
    "terminal.integrated.confirmOnPaste": False,
    "terminal.integrated.confirmOnKill": "never",
    "github.copilot.chat.agent.sandbox.allowedDomains": ["*"],
    "security.workspace.trust.enabled": False,
    "security.workspace.trust.untrustedFiles": "open",
    "security.workspace.trust.banner": "never",
    "github.copilot.chat.agent.autoApprove": True,
}


def temizle_ve_parse(content):
    """JSONC -> dict"""
    clean = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    clean = re.sub(r',\s*([\}\]])', r'\\1', clean)
    return json.loads(clean)


def satir_bazli_duzelt(content):
    """JSON parse edilemezse satır bazlı terminal.autoApprove bloğunu değiştir"""
    lines = content.split('\n')
    
    # chat.tools.terminal.autoApprove bloğunu bul
    start = None
    brace_count = 0
    end = None
    for i, line in enumerate(lines):
        if '"chat.tools.terminal.autoApprove"' in line:
            start = i
        if start is not None:
            brace_count += line.count('{')
            brace_count -= line.count('}')
            if brace_count == 0 and i > start:
                end = i
                break
    
    if start is not None and end is not None:
        # Virgül kontrolü
        sonraki = lines[end + 1].strip() if end + 1 < len(lines) else ''
        virgul = ',' if sonraki and not sonraki.startswith('}') else ','
        
        new_block = [
            '    "chat.tools.terminal.autoApprove": {',
            '        ".*": true',
            '    }' + virgul
        ]
        lines = lines[:start] + new_block + lines[end + 1:]
        print(f"  -> terminal.autoApprove bloğu temizlendi ({end - start + 1} satır -> 3 satır)")
    
    # Eksik ayarları dosya sonuna (kapanan }'den önce) ekle
    eklenecekler = []
    for key, val in GEREKLI_AYARLAR.items():
        if key == "chat.tools.terminal.autoApprove":
            continue  # Zaten yukarıda düzelttik
        key_found = False
        for line in lines:
            if f'"{key}"' in line:
                key_found = True
                break
        if not key_found:
            val_str = json.dumps(val)
            eklenecekler.append(f'    "{key}": {val_str}')
    
    if eklenecekler:
        # Son } 'den önce ekle
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '}':
                for ek in eklenecekler:
                    lines.insert(i, ek + ',')
                print(f"  -> {len(eklenecekler)} eksik ayar eklendi")
                break
    
    return '\n'.join(lines)


def dosya_duzelt(path, isim):
    """Tek bir settings.json dosyasını düzelt"""
    if not os.path.exists(path):
        print(f"[{isim}] Dosya bulunamadı: {path}")
        return
    
    with open(path, 'r') as f:
        content = f.read()
    
    orijinal_satir = len(content.split('\n'))
    
    try:
        settings = temizle_ve_parse(content)
        
        # Ayarları güncelle
        degisen = 0
        for key, val in GEREKLI_AYARLAR.items():
            if settings.get(key) != val:
                settings[key] = val
                degisen += 1
        
        with open(path, 'w') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        
        yeni_satir = len(json.dumps(settings, indent=4).split('\n'))
        print(f"[{isim}] ✓ JSON parse başarılı. {degisen} ayar güncellendi. {orijinal_satir} -> {yeni_satir} satır")
        
    except json.JSONDecodeError:
        print(f"[{isim}] JSON parse hatası, satır bazlı düzeltme yapılıyor...")
        content = satir_bazli_duzelt(content)
        
        with open(path, 'w') as f:
            f.write(content)
        
        yeni_satir = len(content.split('\n'))
        print(f"[{isim}] ✓ Satır bazlı düzeltme tamamlandı. {orijinal_satir} -> {yeni_satir} satır")


def main():
    base = os.path.expanduser("~/Library/Application Support/Code/User")
    
    # 1. Global settings
    print("=" * 60)
    print("1. GLOBAL SETTINGS")
    print("=" * 60)
    dosya_duzelt(os.path.join(base, "settings.json"), "Global")
    
    # 2. Tüm profiller
    print("\n" + "=" * 60)
    print("2. PROFİL SETTINGS")
    print("=" * 60)
    profiles_dir = os.path.join(base, "profiles")
    if os.path.exists(profiles_dir):
        for profil in sorted(os.listdir(profiles_dir)):
            profil_path = os.path.join(profiles_dir, profil, "settings.json")
            if os.path.exists(profil_path):
                dosya_duzelt(profil_path, f"Profil:{profil}")
    
    # 3. Özet
    print("\n" + "=" * 60)
    print("ÖZET")
    print("=" * 60)
    print("Eklenen/düzeltilen ayarlar:")
    for key, val in GEREKLI_AYARLAR.items():
        print(f"  {key}: {json.dumps(val)}")
    print("\n✅ Tüm settings.json dosyaları güncellendi!")
    print("⚠️  VS Code'da Cmd+Shift+P > 'Reload Window' yapın.")


if __name__ == "__main__":
    main()
