import json

path = "/Users/emre/Library/Application Support/Code/User/settings.json"

with open(path, "r") as f:
    d = json.load(f)

# Copilot otomatik onay ayarlarını ekle/güncelle
updates = {
    "chat.tools.autoApprove": True,
    "github.copilot.chat.agent.autoApprove": True,
    "chat.commandCenter.enabled": True,
    "github.copilot.enable": {
        "*": True,
        "plaintext": True,
        "markdown": True,
        "scminput": True
    },
    "github.copilot.chat.runCommand.enabled": True,
    "chat.agent.maxRequests": 100,
}

# Mevcut copilot ayarlarını göster
print("MEVCUT COPILOT AYARLARI:")
for k in sorted(d.keys()):
    if "copilot" in k.lower() or "autoApprove" in k or "chat.tools" in k or "chat.agent" in k:
        print(f"  {k} = {d[k]}")

d.update(updates)

with open(path, "w") as f:
    json.dump(d, f, indent=4, ensure_ascii=False)

print("\nEKLENEN/GUNCELLENEN AYARLAR:")
for k, v in updates.items():
    print(f"  {k} = {v}")

print("\nGlobal settings.json guncellendi!")
