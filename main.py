#!/usr/bin/env python3
# Emare GitHup — Giriş Noktası

"""
Emare GitHup — GitHub Yönetim Aracı

Özellikler:
  - Tüm projeleri GitHub'a push (github_push_all.py)
  - GitHub Push Webhook alıcısı (webhook_receiver.py)
    → EmareCloud paneline ileterek otomatik deploy tetikler

Kullanım:
  python main.py                      # Webhook sunucusunu başlat (varsayılan)
  python main.py --push               # Tüm projeleri GitHub'a push et
  python main.py --port 8112          # Özel port
  python main.py --panel http://...   # Özel panel URL'i

Webhook Kurulum (GitHub):
  Settings → Webhooks → Add webhook
  Payload URL : https://<YOUR_SERVER>:8112/github-webhook
  Content type: application/json
  Secret      : GITHUB_WEBHOOK_SECRET env değişkeni ile aynı
  Events      : Just the push event ✓
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Emare GitHup — GitHub Webhook & Deploy Yöneticisi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--push', action='store_true',
                        help='Tüm projeleri GitHub\'a push et')
    parser.add_argument('--port', type=int,
                        default=int(os.environ.get('WEBHOOK_PORT', 8112)),
                        help='Webhook sunucu portu (varsayılan: 8112)')
    parser.add_argument('--panel',
                        default=os.environ.get('EMARECLOUD_PANEL', 'https://emarecloud.tr'),
                        help='EmareCloud panel URL')
    parser.add_argument('--daemon', action='store_true',
                        help='Webhook sunucusunu arka planda başlat')

    args = parser.parse_args()

    if args.push:
        # Tüm projeleri GitHub'a push et
        print("📤 Tüm projeler GitHub'a push ediliyor...")
        from github_push_all import tum_projeleri_pushla
        tum_projeleri_pushla()
    else:
        # Webhook sunucusunu başlat
        os.environ['EMARECLOUD_PANEL'] = args.panel
        from webhook_receiver import basla
        basla(port=args.port)


if __name__ == "__main__":
    main()
