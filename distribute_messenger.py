import os
import shutil

base = "/Users/emre/Desktop/Emare"
source = os.path.join(base, "EMARE_ORTAK_CALISMA", "emare_messenger.py")
skip = {".DS_Store", ".hub_pids.json", ".hub_venv", ".vscode", "_EMARE_TASIMA", "hub_templates", "data", "EMARE_ORTAK_CALISMA"}
count = 0

for item in sorted(os.listdir(base)):
    path = os.path.join(base, item)
    if not os.path.isdir(path):
        continue
    if item.startswith("."):
        continue
    if item in skip:
        continue

    dest = os.path.join(path, "emare_messenger.py")
    shutil.copy2(source, dest)
    count += 1
    print(f"  OK {item}")

print(f"\nToplam: {count} projeye dağıtıldı")
