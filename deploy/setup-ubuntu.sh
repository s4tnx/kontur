#!/usr/bin/env bash
# Контур Дома — установка сайта на чистую Ubuntu 22.04/24.04 (Яндекс Облако, Compute Cloud).
# Запускать на самой машине:
#   sudo bash setup-ubuntu.sh kontur-doma.ru      # с доменом
#   sudo bash setup-ubuntu.sh                     # пока без домена, по IP
set -euo pipefail

DOMAIN="${1:-_}"
SITE_DIR=/var/www/kontur
REPO=https://github.com/s4tnx/kontur.git

[ "$(id -u)" = 0 ] || { echo "Запустите через sudo"; exit 1; }

echo "==> Ставим nginx, PHP и git"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx php-fpm php-sqlite3 php-mbstring git

PHPVER=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')
echo "==> PHP $PHPVER"

echo "==> Забираем сайт из репозитория"
git config --global --add safe.directory "$SITE_DIR" 2>/dev/null || true
if [ -d "$SITE_DIR/.git" ]; then
  git -C "$SITE_DIR" pull --ff-only
else
  rm -rf "$SITE_DIR"
  git clone --depth 1 "$REPO" "$SITE_DIR"
fi

echo "==> Включаем серверный кабинет (API_URL)"
sed -i "s|const API_URL='';|const API_URL='/api.php';|" "$SITE_DIR/index.html"

echo "==> Права и папка для документов"
mkdir -p "$SITE_DIR/uploads"
printf 'Deny from all\n' > "$SITE_DIR/uploads/.htaccess"
chown -R www-data:www-data "$SITE_DIR"
find "$SITE_DIR" -type d -exec chmod 755 {} \;
find "$SITE_DIR" -type f -exec chmod 644 {} \;

echo "==> Лимиты загрузки файлов (документы до 20 МБ)"
cat > "/etc/php/$PHPVER/fpm/conf.d/99-kontur.ini" <<INI
upload_max_filesize = 25M
post_max_size = 26M
max_execution_time = 60
INI

echo "==> Настраиваем nginx"
sed -e "s/SERVER_NAME/$DOMAIN/" -e "s/phpPHPVER-fpm/php$PHPVER-fpm/" \
    "$SITE_DIR/deploy/kontur.nginx.conf" > /etc/nginx/sites-available/kontur
ln -sf /etc/nginx/sites-available/kontur /etc/nginx/sites-enabled/kontur
rm -f /etc/nginx/sites-enabled/default

systemctl restart "php$PHPVER-fpm"
nginx -t
systemctl reload nginx

echo
echo "Готово. Сайт открыт по http://$( [ "$DOMAIN" = "_" ] && curl -s -4 ifconfig.me || echo "$DOMAIN" )"
if [ "$DOMAIN" != "_" ]; then
  echo "Сертификат HTTPS:  sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d $DOMAIN"
fi
echo "Первый зарегистрированный на сайте аккаунт станет администратором."
