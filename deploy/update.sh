#!/usr/bin/env bash
# Обновить сайт после нового коммита. База и документы не трогаются.
set -euo pipefail
SITE_DIR=/var/www/kontur
[ "$(id -u)" = 0 ] || { echo "Запустите через sudo"; exit 1; }
git config --global --add safe.directory "$SITE_DIR" 2>/dev/null || true
git -C "$SITE_DIR" checkout -- index.html
git -C "$SITE_DIR" pull --ff-only
sed -i "s|const API_URL='';|const API_URL='/api.php';|" "$SITE_DIR/index.html"
chown -R www-data:www-data "$SITE_DIR"
systemctl reload nginx
echo "Обновлено."
