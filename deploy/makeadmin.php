<?php
/* Контур Хаус — аварийный доступ к панели.
   Показывает, какие аккаунты есть в базе и какие у них роли, и может выдать роль администратора.

   1. Залейте этот файл рядом с api.php (в папку сайта).
   2. Откройте https://ваш-домен/makeadmin.php — увидите список аккаунтов.
   3. Откройте https://ваш-домен/makeadmin.php?email=ваша@почта — аккаунт станет администратором.
   4. УДАЛИТЕ файл с хостинга.

   Для безопасности файл работает только 30 минут после загрузки: если забыли удалить,
   он всё равно перестанет что-либо делать. */

header('Content-Type: text/plain; charset=utf-8');
header('X-Robots-Tag: noindex');

$db = __DIR__ . '/kontur.sqlite';
$age = time() - (int)@filemtime(__FILE__);

if ($age > 1800) {
  exit("Файл устарел (загружен " . round($age / 60) . " мин назад).\nЗалейте его заново и откройте сразу — он работает первые 30 минут.\n");
}
if (!file_exists($db)) {
  exit("Базы ещё нет: сначала зарегистрируйтесь на сайте, потом откройте этот файл.\n");
}

try {
  $pdo = new PDO('sqlite:' . $db, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (Throwable $e) {
  exit('Не удалось открыть базу: ' . $e->getMessage() . "\n");
}

$email = trim((string)($_GET['email'] ?? ''));

if ($email === '') {
  echo "АККАУНТЫ В БАЗЕ\n" . str_repeat('=', 52) . "\n\n";
  $rows = $pdo->query('SELECT id, email, name, role, created FROM users ORDER BY id')->fetchAll(PDO::FETCH_ASSOC);
  if (!$rows) {
    echo "Пока ни одного аккаунта — зарегистрируйтесь на сайте.\n";
  } else {
    foreach ($rows as $r) {
      $role = ['client' => 'клиент', 'manager' => 'менеджер', 'admin' => 'АДМИНИСТРАТОР'][$r['role']] ?? $r['role'];
      echo '  ' . str_pad($r['email'], 32) . $role . '   (' . $r['name'] . ', ' . date('d.m.Y H:i', (int)$r['created']) . ")\n";
    }
  }
  $n = (int)$pdo->query('SELECT COUNT(*) FROM orders')->fetchColumn();
  echo "\nЗаявок в базе: $n\n";
  echo "\nЧтобы выдать роль администратора, откройте этот же адрес так:\n";
  echo "  makeadmin.php?email=ваша@почта\n\nПосле этого удалите файл с хостинга.\n";
  exit;
}

$st = $pdo->prepare('UPDATE users SET role = "admin" WHERE lower(email) = lower(?)');
$st->execute([$email]);
if ($st->rowCount()) {
  echo "Готово: $email теперь администратор.\n";
  echo "Зайдите на сайт, при необходимости выйдите и войдите заново — откроется панель менеджера.\n\n";
  echo "ТЕПЕРЬ УДАЛИТЕ ЭТОТ ФАЙЛ С ХОСТИНГА.\n";
} else {
  echo "Аккаунт $email в базе не найден. Откройте makeadmin.php без параметров и проверьте список.\n";
}
