<?php
/* Контур Хаус — проверка хостинга перед установкой.
   Загрузите этот файл в папку сайта, откройте https://ваш-домен/check.php,
   прочитайте ответ — и УДАЛИТЕ файл. */
header('Content-Type: text/plain; charset=utf-8');

$ok = true;
function line(string $name, bool $good, string $note = ''): void {
  global $ok;
  if (!$good) $ok = false;
  echo str_pad($name, 34, '.') . ' ' . ($good ? 'ЕСТЬ' : 'НЕТ') . ($note ? '  — ' . $note : '') . "\n";
}

echo "ПРОВЕРКА ХОСТИНГА ДЛЯ «КОНТУР ДОМА»\n";
echo str_repeat('=', 52) . "\n\n";
echo 'Версия PHP: ' . PHP_VERSION . (version_compare(PHP_VERSION, '7.4', '>=') ? '  (подходит)' : '  — НУЖНА 7.4 ИЛИ НОВЕЕ') . "\n\n";
if (version_compare(PHP_VERSION, '7.4', '<')) $ok = false;

line('Расширение pdo_sqlite', extension_loaded('pdo_sqlite'), 'без него кабинет не работает');
line('Расширение sqlite3', extension_loaded('sqlite3'));
line('Расширение mbstring', extension_loaded('mbstring'));
line('Расширение json', extension_loaded('json'));
line('Папка сайта доступна на запись', is_writable(__DIR__), 'здесь создаётся база и папка uploads');

echo "\nПробная запись в базу: ";
try {
  $f = __DIR__ . '/_check.sqlite';
  $pdo = new PDO('sqlite:' . $f, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
  $pdo->exec('CREATE TABLE IF NOT EXISTS t(a TEXT)');
  $pdo->exec("INSERT INTO t VALUES('ok')");
  $v = $pdo->query('SELECT a FROM t LIMIT 1')->fetchColumn();
  $pdo = null;
  @unlink($f); @unlink($f . '-wal'); @unlink($f . '-shm');
  echo ($v === 'ok' ? "РАБОТАЕТ\n" : "странный ответ\n");
  if ($v !== 'ok') $ok = false;
} catch (Throwable $e) {
  $ok = false;
  echo 'ОШИБКА — ' . $e->getMessage() . "\n";
}

echo "\nРазмер загружаемого файла: " . ini_get('upload_max_filesize')
   . ' (нужно 20M или больше, правится файлом .user.ini)' . "\n";

echo "\n" . str_repeat('=', 52) . "\n";
echo $ok
  ? "ВСЁ ГОТОВО. Заливайте index.html и api.php, впишите в index.html\nconst API_URL='/api.php'; — и кабинет заработает.\n"
  : "ЧЕГО-ТО НЕ ХВАТАЕТ. Покажите этот ответ разработчику: если нет sqlite,\nкабинет нужно перевести на MySQL.\n";
echo "\nПосле проверки удалите этот файл с хостинга.\n";
