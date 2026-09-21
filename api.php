<?php
/* Контур Дома — простой сервер для кабинета: регистрация, вход, заявки, документы.
   Положите этот файл рядом с index.html на хостинге с PHP 7.4+ (нужны sqlite3 и json).
   В index.html впишите адрес: const API_URL='/api.php';
   Рядом появятся файлы: kontur.sqlite (база) и папка uploads (документы). */

declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') { http_response_code(204); exit; }

const DB_FILE   = __DIR__ . '/kontur.sqlite';
const UP_DIR    = __DIR__ . '/uploads';
const MAX_FILE  = 20 * 1024 * 1024;   // 20 МБ на файл
const TOKEN_TTL = 60 * 60 * 24 * 30;  // вход помнится 30 дней

/* На обычном хостинге (Apache: reg.ru, Timeweb и подобные) база и документы лежат в той же папке,
   что и сайт, поэтому их надо закрыть от прямого скачивания. Если своего .htaccess нет — создаём его.
   На сервере с nginx эти файлы просто не используются. */
function guardFiles(): void {
  $ht = __DIR__ . '/.htaccess';
  if (!file_exists($ht)) @file_put_contents($ht, <<<'HT'
# Контур Дома — защита базы и документов, адреса одностраничного сайта.
<IfModule mod_authz_core.c>
  <FilesMatch "^kontur\.sqlite">
    Require all denied
  </FilesMatch>
</IfModule>
<IfModule !mod_authz_core.c>
  <FilesMatch "^kontur\.sqlite">
    Order allow,deny
    Deny from all
  </FilesMatch>
</IfModule>
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{HTTP_HOST} ^www\.(.+)$ [NC]
  RewriteRule ^ https://%1%{REQUEST_URI} [R=301,L]
  RewriteRule ^uploads/ - [R=404,L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule ^ index.html [L]
</IfModule>
<IfModule mod_headers.c>
  <FilesMatch "\.html$">
    Header set Cache-Control "no-cache, must-revalidate"
  </FilesMatch>
  <FilesMatch "\.(jpg|jpeg|png|webp|svg|ico|woff2)$">
    Header set Cache-Control "public, max-age=604800"
  </FilesMatch>
</IfModule>
HT);
  $ui = __DIR__ . '/.user.ini';
  if (!file_exists($ui)) @file_put_contents($ui, "upload_max_filesize = 25M\npost_max_size = 26M\n");
}

function db(): PDO {
  static $pdo = null;
  if ($pdo) return $pdo;
  guardFiles();
  $pdo = new PDO('sqlite:' . DB_FILE, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
  $pdo->exec('PRAGMA journal_mode=WAL');
  $pdo->exec('CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, pass TEXT NOT NULL,
      name TEXT, phone TEXT, role TEXT NOT NULL DEFAULT "client", created INTEGER)');
  $pdo->exec('CREATE TABLE IF NOT EXISTS sessions(
      token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created INTEGER)');
  $pdo->exec('CREATE TABLE IF NOT EXISTS orders(
      id INTEGER PRIMARY KEY AUTOINCREMENT, no TEXT, user_id INTEGER, fio TEXT, phone TEXT, email TEXT,
      region TEXT, comment TEXT, items TEXT, total REAL, stage INTEGER DEFAULT 0,
      status TEXT DEFAULT "new", created INTEGER)');
  $pdo->exec('CREATE TABLE IF NOT EXISTS docs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, name TEXT, cat TEXT, size INTEGER,
      by_role TEXT, who TEXT, path TEXT, uploader INTEGER, created INTEGER)');
  $pdo->exec('CREATE TABLE IF NOT EXISTS msgs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, user_id INTEGER, role TEXT, who TEXT,
      text TEXT, files TEXT, item TEXT, created INTEGER)');
  $mc = array_column($pdo->query('PRAGMA table_info(msgs)')->fetchAll(PDO::FETCH_ASSOC), 'name');
  if (!in_array('item', $mc, true)) $pdo->exec('ALTER TABLE msgs ADD COLUMN item TEXT');
  /* промокод заявки — колонка появилась позже, добавляем в старые базы */
  $cols = array_column($pdo->query('PRAGMA table_info(orders)')->fetchAll(PDO::FETCH_ASSOC), 'name');
  if (!in_array('promo', $cols, true)) $pdo->exec('ALTER TABLE orders ADD COLUMN promo TEXT');
  return $pdo;
}

function out($data, int $code = 200): void { http_response_code($code); echo json_encode($data, JSON_UNESCAPED_UNICODE); exit; }
function fail(string $msg, int $code = 400): void { out(['error' => $msg], $code); }
function body(): array {
  $raw = file_get_contents('php://input');
  if ($raw === '' || $raw === false) return $_POST;
  $j = json_decode($raw, true);
  return is_array($j) ? $j : $_POST;
}
function bearer(): ?string {
  $h = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
  if (!$h && function_exists('apache_request_headers')) {
    foreach (apache_request_headers() as $k => $v) if (strtolower($k) === 'authorization') $h = $v;
  }
  if (preg_match('/Bearer\s+([A-Za-z0-9]+)/', $h, $m)) return $m[1];
  /* запасной путь: свой заголовок — его хостинги не срезают */
  $x = $_SERVER['HTTP_X_AUTH_TOKEN'] ?? '';
  if (!$x && function_exists('apache_request_headers')) {
    foreach (apache_request_headers() as $k => $v) if (strtolower($k) === 'x-auth-token') $x = $v;
  }
  if (preg_match('/^[A-Za-z0-9]+$/', (string)$x)) return (string)$x;
  return $_GET['token'] ?? null;
}
function me(): ?array {
  $t = bearer(); if (!$t) return null;
  $st = db()->prepare('SELECT u.*, s.created AS s_created FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?');
  $st->execute([$t]);
  $u = $st->fetch(PDO::FETCH_ASSOC);
  if (!$u) return null;
  if (time() - (int)$u['s_created'] > TOKEN_TTL) { db()->prepare('DELETE FROM sessions WHERE token=?')->execute([$t]); return null; }
  return $u;
}
function need(): array { $u = me(); if (!$u) fail('Нужно войти в аккаунт', 401); return $u; }
function staff(array $u): bool { return in_array($u['role'], ['manager', 'admin'], true); }
function pub(array $u): array { return ['id' => (int)$u['id'], 'email' => $u['email'], 'name' => $u['name'], 'phone' => $u['phone'], 'role' => $u['role']]; }
function orderRow(array $o): array {
  return ['id' => (int)$o['id'], 'no' => $o['no'], 'fio' => $o['fio'], 'phone' => $o['phone'], 'email' => $o['email'],
    'region' => $o['region'], 'comment' => $o['comment'], 'items' => json_decode($o['items'] ?: '[]', true),
    'total' => (float)$o['total'], 'stage' => (int)$o['stage'], 'status' => $o['status'], 'created' => (int)$o['created'] * 1000,
    'promo' => !empty($o['promo']) ? json_decode($o['promo'], true) : null];
}

$a = $_GET['a'] ?? '';

/* ---------- аккаунты ---------- */
if ($a === 'register') {
  $b = body();
  $email = strtolower(trim((string)($b['email'] ?? '')));
  $pass  = (string)($b['pass'] ?? '');
  $name  = trim((string)($b['name'] ?? ''));
  if (!filter_var($email, FILTER_VALIDATE_EMAIL)) fail('Проверьте адрес почты');
  if (strlen($pass) < 6) fail('Пароль должен быть не короче 6 символов');
  if ($name === '') fail('Укажите имя');
  $st = db()->prepare('SELECT id FROM users WHERE email=?'); $st->execute([$email]);
  if ($st->fetch()) fail('Аккаунт с этой почтой уже есть — войдите');
  $first = (int)db()->query('SELECT COUNT(*) FROM users')->fetchColumn() === 0; // первый аккаунт — администратор
  $st = db()->prepare('INSERT INTO users(email,pass,name,role,created) VALUES(?,?,?,?,?)');
  $st->execute([$email, password_hash($pass, PASSWORD_DEFAULT), $name, $first ? 'admin' : 'client', time()]);
  $id = (int)db()->lastInsertId();
  $token = bin2hex(random_bytes(24));
  db()->prepare('INSERT INTO sessions(token,user_id,created) VALUES(?,?,?)')->execute([$token, $id, time()]);
  $st = db()->prepare('SELECT * FROM users WHERE id=?'); $st->execute([$id]);
  out(['token' => $token, 'user' => pub($st->fetch(PDO::FETCH_ASSOC))]);
}

if ($a === 'login') {
  $b = body();
  $email = strtolower(trim((string)($b['email'] ?? '')));
  $pass  = (string)($b['pass'] ?? '');
  $st = db()->prepare('SELECT * FROM users WHERE email=?'); $st->execute([$email]);
  $u = $st->fetch(PDO::FETCH_ASSOC);
  if (!$u || !password_verify($pass, $u['pass'])) fail('Неверная почта или пароль', 401);
  $token = bin2hex(random_bytes(24));
  db()->prepare('INSERT INTO sessions(token,user_id,created) VALUES(?,?,?)')->execute([$token, (int)$u['id'], time()]);
  out(['token' => $token, 'user' => pub($u)]);
}

if ($a === 'me')     { $u = need(); out(['user' => pub($u)]); }
if ($a === 'logout') { $t = bearer(); if ($t) db()->prepare('DELETE FROM sessions WHERE token=?')->execute([$t]); out(['ok' => true]); }

if ($a === 'profile') {
  $u = need(); $b = body();
  $name  = trim((string)($b['name'] ?? $u['name']));
  $phone = trim((string)($b['phone'] ?? $u['phone']));
  db()->prepare('UPDATE users SET name=?, phone=? WHERE id=?')->execute([$name, $phone, (int)$u['id']]);
  out(['ok' => true]);
}

/* список сотрудников и выдача ролей — только администратору */
if ($a === 'staff') {
  $u = need(); if ($u['role'] !== 'admin') fail('Только для администратора', 403);
  $rows = db()->query('SELECT id,email,name,role,created FROM users ORDER BY created DESC')->fetchAll(PDO::FETCH_ASSOC);
  out(['users' => array_map(fn($r) => ['id' => (int)$r['id'], 'email' => $r['email'], 'name' => $r['name'], 'role' => $r['role']], $rows)]);
}
if ($a === 'role') {
  $u = need(); if ($u['role'] !== 'admin') fail('Только для администратора', 403);
  $b = body(); $email = strtolower(trim((string)($b['email'] ?? ''))); $role = (string)($b['role'] ?? 'client');
  if (!in_array($role, ['client', 'manager', 'admin'], true)) fail('Неизвестная роль');
  $st = db()->prepare('SELECT id FROM users WHERE email=?'); $st->execute([$email]);
  if (!$st->fetch()) fail('Такого аккаунта нет');
  db()->prepare('UPDATE users SET role=? WHERE email=?')->execute([$role, $email]);
  out(['ok' => true]);
}

/* ---------- заявки ---------- */
if ($a === 'orders') {
  $u = me();
  if (!$u) out(['orders' => []]);
  if (staff($u)) $rows = db()->query('SELECT * FROM orders ORDER BY created DESC')->fetchAll(PDO::FETCH_ASSOC);
  else { $st = db()->prepare('SELECT * FROM orders WHERE user_id=? ORDER BY created DESC'); $st->execute([(int)$u['id']]); $rows = $st->fetchAll(PDO::FETCH_ASSOC); }
  out(['orders' => array_map('orderRow', $rows)]);
}

if ($a === 'order') {
  $u = me(); $b = body();
  $items = $b['items'] ?? [];
  if (!is_array($items) || !count($items)) fail('Корзина пуста');
  $promo = (isset($b['promo']['code'], $b['promo']['pct']) && in_array((int)$b['promo']['pct'], [5, 10, 15, 20], true))
    ? json_encode(['code' => substr((string)$b['promo']['code'], 0, 40), 'pct' => (int)$b['promo']['pct']], JSON_UNESCAPED_UNICODE) : null;
  $st = db()->prepare('INSERT INTO orders(no,user_id,fio,phone,email,region,comment,items,total,stage,status,created,promo) VALUES(?,?,?,?,?,?,?,?,?,0,"new",?,?)');
  $st->execute([(string)($b['no'] ?? ''), $u ? (int)$u['id'] : null, (string)($b['fio'] ?? ''), (string)($b['phone'] ?? ''),
    $u ? $u['email'] : (string)($b['email'] ?? ''), (string)($b['region'] ?? ''), (string)($b['comment'] ?? ''),
    json_encode($items, JSON_UNESCAPED_UNICODE), (float)($b['total'] ?? 0), time(), $promo]);
  out(['id' => (int)db()->lastInsertId()]);
}

if ($a === 'status') {
  $u = need(); if (!staff($u)) fail('Только для сотрудников', 403);
  $b = body(); $id = (int)($b['id'] ?? 0);
  $st = db()->prepare('UPDATE orders SET status=?, stage=COALESCE(?,stage) WHERE id=?');
  $st->execute([(string)($b['status'] ?? 'new'), isset($b['stage']) ? (int)$b['stage'] : null, $id]);
  out(['ok' => true]);
}

/* ---------- документы ---------- */
function canOrder(array $u, int $orderId): bool {
  if (staff($u)) return true;
  $st = db()->prepare('SELECT user_id FROM orders WHERE id=?'); $st->execute([$orderId]);
  $row = $st->fetch(PDO::FETCH_ASSOC);
  return $row && (int)$row['user_id'] === (int)$u['id'];
}

if ($a === 'docs') {
  $u = need(); $orderId = (int)($_GET['order'] ?? 0);
  if (!canOrder($u, $orderId)) fail('Нет доступа к этой заявке', 403);
  $st = db()->prepare('SELECT * FROM docs WHERE order_id=? ORDER BY created ASC'); $st->execute([$orderId]);
  out(['docs' => array_map(fn($d) => ['id' => (int)$d['id'], 'name' => $d['name'], 'cat' => $d['cat'], 'size' => (int)$d['size'],
    'by' => $d['by_role'], 'who' => $d['who'], 'at' => (int)$d['created'] * 1000], $st->fetchAll(PDO::FETCH_ASSOC))]);
}

if ($a === 'doc') {
  $u = need();
  $orderId = (int)($_POST['order'] ?? 0);
  if (!canOrder($u, $orderId)) fail('Нет доступа к этой заявке', 403);
  if (!isset($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) fail('Файл не получен');
  if ($_FILES['file']['size'] > MAX_FILE) fail('Файл больше 20 МБ');
  if (!is_dir(UP_DIR)) mkdir(UP_DIR, 0775, true);
  if (!file_exists(UP_DIR . '/.htaccess')) @file_put_contents(UP_DIR . '/.htaccess',
    "<IfModule mod_authz_core.c>\nRequire all denied\n</IfModule>\n" .
    "<IfModule !mod_authz_core.c>\nOrder allow,deny\nDeny from all\n</IfModule>\n");
  $safe = preg_replace('/[^\w.\-]+/u', '_', (string)$_FILES['file']['name']);
  $path = UP_DIR . '/' . $orderId . '-' . bin2hex(random_bytes(6)) . '-' . $safe;
  if (!move_uploaded_file($_FILES['file']['tmp_name'], $path)) fail('Не удалось сохранить файл', 500);
  $st = db()->prepare('INSERT INTO docs(order_id,name,cat,size,by_role,who,path,uploader,created) VALUES(?,?,?,?,?,?,?,?,?)');
  $st->execute([$orderId, (string)$_FILES['file']['name'], (string)($_POST['cat'] ?? 'Другое'), (int)$_FILES['file']['size'],
    staff($u) ? 'manager' : 'client', (string)$u['name'], basename($path), (int)$u['id'], time()]);
  out(['id' => (int)db()->lastInsertId()]);
}

if ($a === 'file') {
  $u = need(); $id = (int)($_GET['id'] ?? 0);
  $st = db()->prepare('SELECT * FROM docs WHERE id=?'); $st->execute([$id]);
  $d = $st->fetch(PDO::FETCH_ASSOC);
  if (!$d || !canOrder($u, (int)$d['order_id'])) fail('Нет доступа к файлу', 403);
  $path = UP_DIR . '/' . basename($d['path']);
  if (!is_file($path)) fail('Файл не найден', 404);
  header('Content-Type: application/octet-stream');
  header('Content-Length: ' . filesize($path));
  header('Content-Disposition: attachment; filename="' . rawurlencode($d['name']) . '"');
  readfile($path);
  exit;
}

if ($a === 'docdel') {
  $u = need(); $b = body(); $id = (int)($b['id'] ?? 0);
  $st = db()->prepare('SELECT * FROM docs WHERE id=?'); $st->execute([$id]);
  $d = $st->fetch(PDO::FETCH_ASSOC);
  if (!$d) fail('Файл не найден', 404);
  if (!staff($u) && (int)$d['uploader'] !== (int)$u['id']) fail('Можно удалять только свои файлы', 403);
  @unlink(UP_DIR . '/' . basename($d['path']));
  db()->prepare('DELETE FROM docs WHERE id=?')->execute([$id]);
  out(['ok' => true]);
}

/* переписка по заявке: менеджер и клиент, с фото во вложении */
if ($a === 'msgs') {
  $u = need(); $orderId = (int)($_GET['order'] ?? 0);
  if (!canOrder($u, $orderId)) fail('Нет доступа к этой заявке', 403);
  $st = db()->prepare('SELECT * FROM msgs WHERE order_id=? ORDER BY created ASC'); $st->execute([$orderId]);
  out(['msgs' => array_map(fn($m) => ['id' => (int)$m['id'], 'role' => $m['role'], 'who' => $m['who'],
    'text' => $m['text'], 'files' => json_decode($m['files'] ?: '[]', true),
    'item' => !empty($m['item']) ? json_decode($m['item'], true) : null,
    'at' => (int)$m['created'] * 1000], $st->fetchAll(PDO::FETCH_ASSOC))]);
}

if ($a === 'msg') {
  $u = need(); $b = body(); $orderId = (int)($b['order'] ?? 0);
  if (!canOrder($u, $orderId)) fail('Нет доступа к этой заявке', 403);
  $text = trim((string)($b['text'] ?? ''));
  $files = array_slice(array_filter((array)($b['files'] ?? []), fn($f) => is_string($f) && strlen($f) < 1200000), 0, 3);
  if ($text === '' && !count($files) && empty($b['item'])) fail('Пустое сообщение');
  $item = isset($b['item']) && is_array($b['item']) ? json_encode($b['item'], JSON_UNESCAPED_UNICODE) : null;
  $st = db()->prepare('INSERT INTO msgs(order_id,user_id,role,who,text,files,item,created) VALUES(?,?,?,?,?,?,?,?)');
  $st->execute([$orderId, (int)$u['id'], staff($u) ? 'manager' : 'client', (string)$u['name'],
    mb_substr($text, 0, 4000), json_encode($files, JSON_UNESCAPED_UNICODE), $item, time()]);
  out(['id' => (int)db()->lastInsertId()]);
}

/* вместе с заявкой удаляем и переписку */
/* удалить заявку: сотрудник — любую, клиент — свою, пока она не дошла до договора */
if ($a === 'orderdel') {
  $u = need(); $b = body(); $id = (int)($b['id'] ?? 0);
  $st = db()->prepare('SELECT * FROM orders WHERE id=?'); $st->execute([$id]);
  $o = $st->fetch(PDO::FETCH_ASSOC);
  if (!$o) fail('Заявка не найдена', 404);
  if (!staff($u)) {
    if ((int)$o['user_id'] !== (int)$u['id']) fail('Это не ваша заявка', 403);
    if (!in_array($o['status'], ['new', 'call', 'visit'], true)) fail('Заявка уже в работе — удалить её может менеджер', 403);
  }
  $st = db()->prepare('SELECT path FROM docs WHERE order_id=?'); $st->execute([$id]);
  foreach ($st->fetchAll(PDO::FETCH_COLUMN) as $path) @unlink(UP_DIR . '/' . basename((string)$path));
  db()->prepare('DELETE FROM docs WHERE order_id=?')->execute([$id]);
  db()->prepare('DELETE FROM msgs WHERE order_id=?')->execute([$id]);
  db()->prepare('DELETE FROM orders WHERE id=?')->execute([$id]);
  out(['ok' => true]);
}

/* непрочитанные: времена сообщений «другой стороны» по каждой заявке.
   Клиент получает сообщения менеджеров по своим заявкам, сотрудник — сообщения клиентов по всем. */
if ($a === 'unread') {
  $u = me();
  if (!$u) out(['orders' => []]);
  $from = staff($u) ? 'client' : 'manager';
  if (staff($u)) {
    $st = db()->prepare('SELECT o.no AS no, m.created AS c FROM msgs m JOIN orders o ON o.id = m.order_id
                         WHERE m.role = ? ORDER BY m.created');
    $st->execute([$from]);
  } else {
    $st = db()->prepare('SELECT o.no AS no, m.created AS c FROM msgs m JOIN orders o ON o.id = m.order_id
                         WHERE m.role = ? AND o.user_id = ? ORDER BY m.created');
    $st->execute([$from, (int)$u['id']]);
  }
  $by = [];
  foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) $by[(string)$r['no']][] = ((int)$r['c']) * 1000;
  $res = [];
  foreach ($by as $no => $times) $res[] = ['no' => (string)$no, 't' => array_slice($times, -100)];
  out(['orders' => $res]);
}

/* короткая сводка о состоянии: сколько аккаунтов и заявок в базе.
   Нужна, чтобы понять, работает ли кабинет на сервере. Личных данных не отдаёт. */
if ($a === 'ping') {
  $n = function (string $tbl): int {
    try { return (int)db()->query('SELECT COUNT(*) FROM ' . $tbl)->fetchColumn(); } catch (Throwable $e) { return -1; }
  };
  out(['ok' => true, 'php' => PHP_VERSION, 'users' => $n('users'), 'orders' => $n('orders'),
       'msgs' => $n('msgs'), 'docs' => $n('docs'), 'write' => is_writable(__DIR__), 'db' => file_exists(DB_FILE),
       'hdrAuth' => !empty($_SERVER['HTTP_AUTHORIZATION']) || !empty($_SERVER['REDIRECT_HTTP_AUTHORIZATION']),
       'hdrX' => !empty($_SERVER['HTTP_X_AUTH_TOKEN']), 'token' => (bool)bearer()]);
}

fail('Неизвестный запрос', 404);
