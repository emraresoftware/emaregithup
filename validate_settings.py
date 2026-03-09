#!/usr/bin/env python3
"""VS Code JSONC settings dosyalarini dogrula"""
import json
import re

def strip_jsonc_comments(text):
    """JSONC yorumlari sil (string icindeki // korunur)"""
    result = []
    i = 0
    in_string = False
    while i < len(text):
        c = text[i]
        if c == '"' and (i == 0 or text[i-1] != '\\'):
            in_string = not in_string
            result.append(c)
            i += 1
        elif not in_string and i + 1 < len(text) and text[i] == '/' and text[i+1] == '/':
            while i < len(text) and text[i] != '\n':
                i += 1
        elif not in_string and i + 1 < len(text) and text[i] == '/' and text[i+1] == '*':
            i += 2
            while i < len(text) - 1 and not (text[i] == '*' and text[i+1] == '/'):
                i += 1
            i += 2
        else:
            result.append(c)
            i += 1
    return ''.join(result)


def dogrula(path, isim):
    try:
        with open(path) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[{isim}] Dosya yok")
        return

    clean = strip_jsonc_comments(content)
    clean = re.sub(r',(\s*[\}\]])', r'\1', clean)

    try:
        d = json.loads(clean)
        print(f"[{isim}] Valid JSON, {len(d)} keys, {len(content.splitlines())} lines")
        for k in [
            'chat.tools.terminal.autoApprove',
            'chat.tools.autoApprove',
            'chat.tools.terminal.sandbox.enabled',
            'security.workspace.trust.enabled',
            'github.copilot.chat.agent.autoApprove',
            'terminal.integrated.confirmOnPaste',
            'chat.tools.urls.autoApprove',
            'chat.agent.autoFix',
        ]:
            v = d.get(k, 'YOK')
            status = 'OK' if v != 'YOK' else 'EKSIK'
            print(f"  [{status}] {k}: {v}")
    except json.JSONDecodeError as e:
        print(f"[{isim}] INVALID: {e}")


import os
base = os.path.expanduser("~/Library/Application Support/Code/User")

print("=" * 60)
dogrula(os.path.join(base, "settings.json"), "Global")

print()
profiles = os.path.join(base, "profiles")
if os.path.exists(profiles):
    for p in sorted(os.listdir(profiles)):
        sf = os.path.join(profiles, p, "settings.json")
        if os.path.exists(sf):
            dogrula(sf, f"Profil:{p}")
            print()
