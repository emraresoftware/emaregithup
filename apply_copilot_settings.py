import os, json

settings = {
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
    "chat.agent.maxRequests": 100
}

base = "/Users/emre/Desktop/Emare"
skip = {".DS_Store", ".hub_pids.json", ".hub_venv", ".vscode", "_EMARE_TASIMA", "hub_templates", "data"}
count = 0

for item in sorted(os.listdir(base)):
    path = os.path.join(base, item)
    if not os.path.isdir(path):
        continue
    if item.startswith("."):
        continue
    if item in skip:
        continue

    vscode_dir = os.path.join(path, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)

    settings_path = os.path.join(vscode_dir, "settings.json")
    existing = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)
        except Exception as e:
            print(f"  WARN: {item} mevcut ayar okunamadi: {e}")

    existing.update(settings)

    with open(settings_path, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    count += 1
    print(f"  OK {item}")

print(f"\nToplam: {count} proje guncellendi")
