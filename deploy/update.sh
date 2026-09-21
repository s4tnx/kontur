#!/usr/bin/env bash
# Обновить сайт после нового коммита. База, документы и счётчик Метрики не теряются.
set -euo pipefail
SITE_DIR=/var/www/kontur
[ "$(id -u)" = 0 ] || { echo "Запустите через sudo"; exit 1; }
git config --global --add safe.directory "$SITE_DIR" 2>/dev/null || true
# запоминаем номер счётчика, который вписан в текущий index.html
YM=$(grep -o "const YM_ID='[0-9]*'" "$SITE_DIR/index.html" | head -1 | grep -o "[0-9]*" || true)
git -C "$SITE_DIR" checkout -- index.html
git -C "$SITE_DIR" pull --ff-only
sed -i "s|const API_URL='';|const API_URL='/api.php';|" "$SITE_DIR/index.html"
[ -n "$YM" ] && sed -i "s|const YM_ID='';|const YM_ID='$YM';|" "$SITE_DIR/index.html"
chown -R www-data:www-data "$SITE_DIR"
systemctl reload nginx
echo "Обновлено.${YM:+ Счётчик Метрики $YM сохранён.}"
