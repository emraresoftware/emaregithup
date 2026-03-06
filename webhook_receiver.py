#!/usr/bin/env python3
"""
emaregithup/webhook_receiver.py — GitHub Push Webhook Alıcısı
==============================================================
Bu servis GitHub'dan gelen push event'lerini dinler ve
EmareCloud paneline ileterek otomatik deploy tetikler.

Çalışma Akışı:
  GitHub Push → POST /github-webhook
                         ↓ X-Hub-Signature-256 doğrula
                         ↓ repo slug çıkar
                         ↓ EmareCloud /api/deploy/webhook/<secret> çağır
                         ↓ DeployJob başlar (SSH üzerinden)

Kurulum:
  1. GitHub reposunda: Settings → Webhooks → Add webhook
     Payload URL : http(s)://<server_ip>:8112/github-webhook
     Content type: application/json
     Secret      : WEBHOOK_SECRET ile aynı
     Events      : Just the push event ✓

  2. Servisi başlat:
     python webhook_receiver.py             # ön planda
     python webhook_receiver.py --daemon    # arka planda (nohup)

Ortam Değişkenleri:
  GITHUB_WEBHOOK_SECRET  — GitHub webhook secret (varsayılan: emare-deploy-secret-2025)
  EMARECLOUD_PANEL       — Panel URL (varsayılan: https://emarecloud.tr)
  EMARECLOUD_TOKEN       — Panel API token (Bearer)
  WEBHOOK_PORT           — Dinleme portu (varsayılan: 8112)
"""

import hashlib
import hmac
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# ──────────────────────────────────────────
# Yapılandırma
# ──────────────────────────────────────────
WEBHOOK_SECRET   = os.environ.get('GITHUB_WEBHOOK_SECRET', 'emare-deploy-secret-2025')
EMARECLOUD_PANEL = os.environ.get('EMARECLOUD_PANEL', 'https://emarecloud.tr')
EMARECLOUD_TOKEN = os.environ.get('EMARECLOUD_TOKEN', '')
WEBHOOK_PORT     = int(os.environ.get('WEBHOOK_PORT', 8112))
FORWARD_TIMEOUT  = 30  # saniye

# ──────────────────────────────────────────
# Loglama
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('emaregithup.webhook')


# ──────────────────────────────────────────
# İmza doğrulama
# ──────────────────────────────────────────
def imza_dogrula(body: bytes, signature_header: str) -> bool:
    """GitHub X-Hub-Signature-256 imzasını doğrular."""
    if not signature_header:
        return False
    if not signature_header.startswith('sha256='):
        return False
    beklenen = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(beklenen, signature_header)


# ──────────────────────────────────────────
# EmareCloud paneline ilet
# ──────────────────────────────────────────
def panele_ilet(slug: str, body: bytes, headers: dict) -> dict:
    """
    GitHub webhook payload'unu EmareCloud paneline iletir.
    Panel /api/deploy/webhook/<secret> endpoint'ini çağırır.
    """
    url = (
        EMARECLOUD_PANEL.rstrip('/') +
        f'/api/deploy/webhook/{WEBHOOK_SECRET}'
    )

    forward_headers = {
        'Content-Type':      'application/json',
        'Accept':            'application/json',
        'X-GitHub-Event':    headers.get('X-GitHub-Event', 'push'),
        'X-Hub-Signature-256': headers.get('X-Hub-Signature-256', ''),
        'X-Forwarded-By':    'emaregithup-webhook',
        'X-Source-Repo':     slug,
    }
    if EMARECLOUD_TOKEN:
        forward_headers['Authorization'] = f'Bearer {EMARECLOUD_TOKEN}'

    req = urllib.request.Request(
        url, data=body, headers=forward_headers, method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=FORWARD_TIMEOUT) as resp:
            response_body = resp.read().decode('utf-8')
            return {'ok': True, 'status': resp.status, 'body': response_body}
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', errors='replace')
        return {'ok': False, 'status': e.code, 'body': raw}
    except urllib.error.URLError as e:
        return {'ok': False, 'status': 0, 'body': str(e.reason)}
    except Exception as e:
        return {'ok': False, 'status': 0, 'body': str(e)}


# ──────────────────────────────────────────
# HTTP Handler
# ──────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # BaseHTTPServer'ın varsayılan log formatını sustur, kendi logumuz var
        pass

    def do_GET(self):
        """Health check endpoint."""
        if self.path == '/health':
            self._json_cevap(200, {
                'ok': True,
                'service': 'emaregithup-webhook',
                'panel': EMARECLOUD_PANEL,
            })
        else:
            self._json_cevap(404, {'error': 'Bulunamadı'})

    def do_POST(self):
        """GitHub webhook POST isteğini işler."""
        if self.path != '/github-webhook':
            self._json_cevap(404, {'error': 'Yanlış endpoint. /github-webhook kullanın.'})
            return

        # İçerik uzunluğunu al
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # GitHub event tipini al
        event = self.headers.get('X-GitHub-Event', 'unknown')
        signature = self.headers.get('X-Hub-Signature-256', '')
        delivery_id = self.headers.get('X-GitHub-Delivery', 'unknown')

        logger.info(f"[webhook] ← Event: {event} | Delivery: {delivery_id}")

        # Sadece push eventini işle
        if event == 'ping':
            logger.info("[webhook] Ping alındı — GitHub webhook bağlantısı başarılı ✓")
            self._json_cevap(200, {'ok': True, 'message': 'Emaregithup webhook hazır!'})
            return

        if event != 'push':
            logger.info(f"[webhook] {event} event yoksayıldı")
            self._json_cevap(200, {'ok': True, 'skipped': f'{event} yoksayıldı'})
            return

        # İmzayı doğrula
        if WEBHOOK_SECRET and not imza_dogrula(body, signature):
            logger.warning(f"[webhook] ⚠ Geçersiz imza! IP: {self.client_address[0]}")
            self._json_cevap(403, {'error': 'Geçersiz imza'})
            return

        # Repo bilgisini çıkar
        try:
            payload = json.loads(body.decode('utf-8'))
            repo_full = payload.get('repository', {}).get('full_name', '')
            slug = repo_full.split('/')[-1].lower() if '/' in repo_full else repo_full.lower()
            branch_ref = payload.get('ref', 'refs/heads/main')
            branch = branch_ref.replace('refs/heads/', '')
            pusher = payload.get('pusher', {}).get('name', '?')
            commits = payload.get('commits', [])
            commit_hash = payload.get('after', '')[:7]
        except Exception as e:
            logger.error(f"[webhook] JSON parse hatası: {e}")
            self._json_cevap(400, {'error': 'JSON parse hatası'})
            return

        logger.info(f"[webhook] {slug}@{branch} | pusher={pusher} | commit={commit_hash} | {len(commits)} commit")

        # EmareCloud paneline ilet
        forward_headers = {
            'X-GitHub-Event':      event,
            'X-Hub-Signature-256': signature,
        }
        sonuc = panele_ilet(slug, body, forward_headers)

        if sonuc['ok']:
            logger.info(f"[webhook] ✓ Panel yanıtı {sonuc['status']}: {sonuc['body'][:200]}")
            self._json_cevap(200, {'ok': True, 'forwarded': True, 'slug': slug})
        else:
            logger.error(f"[webhook] ✗ Panel hatası {sonuc['status']}: {sonuc['body'][:300]}")
            # Panel'e iletemesek de 200 döndür — GitHub yeniden denemesini engelle
            self._json_cevap(200, {
                'ok': False,
                'forwarded': False,
                'slug': slug,
                'panel_error': sonuc['body'][:300],
            })

    def _json_cevap(self, status: int, data: dict):
        """JSON response gönder."""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ──────────────────────────────────────────
# Sunucuyu Başlat
# ──────────────────────────────────────────
def basla(port: int = WEBHOOK_PORT):
    """Webhook sunucusunu başlatır."""
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  EmareGitHup — Webhook Alıcısı Başlatıldı")
    logger.info(f"  Dinleme  : http://0.0.0.0:{port}/github-webhook")
    logger.info(f"  Health   : http://0.0.0.0:{port}/health")
    logger.info(f"  Panel    : {EMARECLOUD_PANEL}")
    logger.info(f"  Secret   : {'*' * len(WEBHOOK_SECRET[:4])}...")
    logger.info("═══════════════════════════════════════════════════")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Webhook alıcısı durduruldu.")
        server.server_close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Emare GitHub Webhook Alıcısı')
    parser.add_argument('--port',   type=int, default=WEBHOOK_PORT, help='Dinleme portu')
    parser.add_argument('--panel',  default=EMARECLOUD_PANEL,       help='EmareCloud panel URL')
    parser.add_argument('--daemon', action='store_true',             help='Arka planda çalış')
    args = parser.parse_args()

    if args.panel:
        EMARECLOUD_PANEL = args.panel

    if args.daemon:
        import os
        pid = os.fork()
        if pid > 0:
            print(f"Webhook alıcısı arka planda başlatıldı (PID: {pid})")
            sys.exit(0)

    basla(args.port)
