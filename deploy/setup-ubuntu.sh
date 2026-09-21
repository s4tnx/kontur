#!/usr/bin/env bash
# Контур Дома — установка сайта на чистую Ubuntu 22.04/24.04 (Яндекс Облако, Compute Cloud).
# Запускать на самой машине:
#   sudo bash setup-ubuntu.sh kontur-doma.ru                        # сайт, кабинет и бесплатный HTTPS
#   sudo bash setup-ubuntu.sh kontur-doma.ru 98765432 vy@mail.ru    # плюс счётчик Метрики и почта для сертификата
#   sudo bash setup-ubuntu.sh                                       # пока без домена, по IP
set -euo pipefail

DOMAIN="${1:-_}"
YM="${2:-}"
EMAIL="${3:-}"
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

# серверный кабинет включается сам: сайт при запуске спрашивает api.php, отвечает ли он

if [ -n "$YM" ]; then
  echo "==> Подключаем Яндекс Метрику, счётчик $YM"
  sed -i "s|const YM_ID='';|const YM_ID='$YM';|" "$SITE_DIR/index.html"
fi

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

# ---- HTTPS: бесплатный сертификат Let's Encrypt, продлевается сам ----
if [ "$DOMAIN" != "_" ]; then
  echo "==> Проверяем, ведёт ли домен на эту машину"
  MYIP=$(curl -s -4 ifconfig.me || true)
  DNSIP=$(getent ahostsv4 "$DOMAIN" 2>/dev/null | awk 'NR==1{print $1}' || true)
  if [ -n "$MYIP" ] && [ "$MYIP" = "$DNSIP" ]; then
    echo "==> Выпускаем сертификат для $DOMAIN"
    apt-get install -y -qq certbot python3-certbot-nginx
    WWW=""
    WWWIP=$(getent ahostsv4 "www.$DOMAIN" 2>/dev/null | awk 'NR==1{print $1}' || true)
    [ "$WWWIP" = "$MYIP" ] && WWW="-d www.$DOMAIN"
    CB_MAIL=(--register-unsafely-without-email)
    [ -n "$EMAIL" ] && CB_MAIL=(-m "$EMAIL")
    certbot --nginx -d "$DOMAIN" $WWW --agree-tos "${CB_MAIL[@]}" --non-interactive --redirect || \
      echo "!! Сертификат не выпустился. Повторите позже: sudo certbot --nginx -d $DOMAIN"
  else
    echo "!! Домен $DOMAIN пока не ведёт на этот сервер (в DNS ${DNSIP:-пусто}, у машины ${MYIP:-?})."
    echo "   Пропишите A-записи у регистратора, подождите час и выполните:"
    echo "   sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
  fi
fi

echo
if [ "$DOMAIN" = "_" ]; then
  echo "Готово. Сайт открыт по http://$(curl -s -4 ifconfig.me)"
else
  echo "Готово. Сайт открыт по https://$DOMAIN"
fi
echo "Первый зарегистрированный на сайте аккаунт станет администратором."
