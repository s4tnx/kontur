<?php
/* Контур Хаус — сброс пароля аккаунта, если он забыт.

   1. Залейте этот файл рядом с api.php (в папку сайта).
   2. Откройте https://ваш-домен/resetpass.php — увидите список аккаунтов.
   3. Откройте https://ваш-домен/resetpass.php?email=ваша@почта&pass=НовыйПароль123
   4. УДАЛИТЕ файл с хостинга.

   Для безопасности файл работает только 30 минут после загрузки. */

header('Content-Type: text/plain; charset=utf-8');
header('X-Robots-Tag: noindex');

$db  = __DIR__ . '/kontur.sqlite';
$age = time() - (int)@filemtime(__FILE__);

if ($age > 1800) {
  exit("Файл устарел (загружен " . round($age / 60) . " мин назад).\nЗалейте его заново и откройте сразу — он работает первые 30 минут.\n");
}
if (!file_exists($db)) exit("Базы ещё нет: сначала зарегистрируйтесь на сайте.\n");

try {
  $pdo = new PDO('sqlite:' . $db, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (Throwable $e) {
  exit('Не удалось открыть базу: ' . $e->getMessage() . "\n");
}

$email = trim((string)($_GET['email'] ?? ''));
$pass  = (string)($_GET['pass'] ?? '');

if ($email === '' || $pass === '') {
  echo "СБРОС ПАРОЛЯ\n" . str_repeat('=', 52) . "\n\nАккаунты в базе:\n";
  foreach ($pdo->query('SELECT email, name, role FROM users ORDER BY id') as $r) {
    echo '  ' . str_pad($r['email'], 32) . $r['role'] . '   (' . $r['name'] . ")\n";
  }
  echo "\nОткройте этот же адрес так:\n";
  echo "  resetpass.php?email=ваша@почта&pass=НовыйПароль123\n";
  echo "\nПароль — не короче 6 символов, без пробелов и знаков & ? #\n";
  echo "После смены удалите файл с хостинга.\n";
  exit;
}
if (mb_strlen($pass) < 6) exit("Пароль слишком короткий — нужно хотя бы 6 символов.\n");

$st = $pdo->prepare('UPDATE users SET pass = ? WHERE lower(email) = lower(?)');
$st->execute([password_hash($pass, PASSWORD_DEFAULT), $email]);

if ($st->rowCount()) {
  /* выкидываем старые сессии этого аккаунта — вход только с новым паролем */
  $q = $pdo->prepare('DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE lower(email) = lower(?))');
  $q->execute([$email]);
  echo "Готово: у аккаунта $email новый пароль.\n";
  echo "Зайдите на сайт и войдите с ним.\n\nТЕПЕРЬ УДАЛИТЕ ЭТОТ ФАЙЛ С ХОСТИНГА.\n";
} else {
  echo "Аккаунт $email в базе не найден. Откройте resetpass.php без параметров и проверьте список.\n";
}
