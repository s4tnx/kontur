<?php
/* Контур Дома — перенос настоящих отзывов с другой площадки в базу сайта.

   Зачем: отзывы, оставленные клиентами на другом сайте, нельзя перенести кнопкой.
   Этот файл берёт их из таблицы CSV и кладёт в базу как настоящие отзывы: они
   появляются на странице «Отзывы» и с них считается оценка для поисковиков.

   1. Сделайте файл reviews.csv в Экселе или Блокноте, по одному отзыву в строке,
      поля через точку с запятой, кодировка UTF-8:

        имя;город;что построили;оценка;дата;текст отзыва
        Ирина Кузнецова;Тверь;Онега 6×8;5;2025-08-14;Собрали за восемь дней...

      Дата в виде 2025-08-14 или 14.08.2025. Оценка от 1 до 5.
      Первая строка с заголовками («имя;город;...») пропускается сама.

   2. Залейте reviews.csv и этот файл рядом с api.php (в папку сайта).
   3. Откройте https://ваш-домен/importreviews.php — увидите, что будет добавлено.
   4. Откройте https://ваш-домен/importreviews.php?go=1 — отзывы попадут в базу.
   5. УДАЛИТЕ оба файла с хостинга.

   Повторный запуск не задваивает: отзыв с тем же именем и текстом пропускается.
   Файл работает первые 30 минут после загрузки — если забыли удалить, он
   всё равно перестанет что-либо делать.

   Важно: переносите только свои настоящие отзывы. Придуманные отзывы и оценка,
   которой никто не ставил, — это недостоверная реклама, а для поисковиков
   повод снять разметку со всего сайта. */

header('Content-Type: text/plain; charset=utf-8');
header('X-Robots-Tag: noindex');

$db  = __DIR__ . '/kontur.sqlite';
$csv = __DIR__ . '/reviews.csv';
$age = time() - (int)@filemtime(__FILE__);
$go  = isset($_GET['go']);

if ($age > 1800) exit("Файл устарел (загружен " . round($age / 60) . " мин назад).\nЗалейте его заново и откройте сразу.\n");
if (!file_exists($db))  exit("Базы ещё нет: сначала откройте сайт и зарегистрируйтесь, потом запускайте перенос.\n");
if (!file_exists($csv)) exit("Рядом нет файла reviews.csv. Положите его в ту же папку, что и этот файл.\n");

try {
  $pdo = new PDO('sqlite:' . $db, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (Throwable $e) {
  exit('Не удалось открыть базу: ' . $e->getMessage() . "\n");
}
$pdo->exec('CREATE TABLE IF NOT EXISTS reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, city TEXT, obj TEXT,
    rating INTEGER DEFAULT 5, text TEXT, ok INTEGER DEFAULT 1, created INTEGER)');

/* дата в любом из двух привычных видов */
function when(string $s): int {
  $s = trim($s);
  if ($s === '') return time();
  if (preg_match('/^(\d{4})-(\d{2})-(\d{2})$/', $s, $m)) return mktime(12, 0, 0, (int)$m[2], (int)$m[3], (int)$m[1]);
  if (preg_match('/^(\d{2})\.(\d{2})\.(\d{4})$/', $s, $m)) return mktime(12, 0, 0, (int)$m[2], (int)$m[1], (int)$m[3]);
  $t = strtotime($s);
  return $t ?: time();
}

$fh = fopen($csv, 'r');
$first = fgets($fh);
/* Эксель иногда добавляет метку в начало файла — убираем */
$first = preg_replace('/^\xEF\xBB\xBF/', '', (string)$first);
rewind($fh);
if (stripos($first, 'имя;') === 0 || stripos($first, 'name;') === 0) fgets($fh);

$add = 0; $skip = 0; $bad = 0; $line = 0;
echo $go ? "ПЕРЕНОС ОТЗЫВОВ\n" : "ПРОВЕРКА ФАЙЛА (ничего не записываем)\n";
echo str_repeat('=', 60) . "\n\n";

$has = $pdo->prepare('SELECT COUNT(*) FROM reviews WHERE name=? AND text=?');
$ins = $pdo->prepare('INSERT INTO reviews(user_id,name,city,obj,rating,text,ok,created) VALUES(NULL,?,?,?,?,?,1,?)');

while (($row = fgetcsv($fh, 0, ';')) !== false) {
  $line++;
  if (!$row || count(array_filter($row, fn($v) => trim((string)$v) !== ''))  === 0) continue;
  $name = trim((string)($row[0] ?? ''));
  $city = trim((string)($row[1] ?? ''));
  $obj  = trim((string)($row[2] ?? ''));
  $rate = (int)($row[3] ?? 5);
  $date = (string)($row[4] ?? '');
  $text = trim((string)($row[5] ?? ''));
  if ($name === '' || mb_strlen($text) < 20) { $bad++; echo "строка $line: пропущена, нет имени или слишком короткий текст\n"; continue; }
  if ($rate < 1 || $rate > 5) $rate = 5;
  $has->execute([$name, $text]);
  if ((int)$has->fetchColumn() > 0) { $skip++; echo "строка $line: уже есть в базе ($name)\n"; continue; }
  if ($go) $ins->execute([mb_substr($name, 0, 60), mb_substr($city, 0, 40), mb_substr($obj, 0, 60), $rate, mb_substr($text, 0, 900), when($date)]);
  $add++;
  echo "строка $line: " . ($go ? 'добавлен' : 'будет добавлен') . " — $name, $city, $obj, оценка $rate\n";
}
fclose($fh);

$total = (int)$pdo->query('SELECT COUNT(*) FROM reviews WHERE ok=1')->fetchColumn();
echo "\n" . str_repeat('=', 60) . "\n";
echo ($go ? "Добавлено: $add\n" : "Готово к переносу: $add\n") . "Пропущено как повтор: $skip\nС ошибками: $bad\n";
echo "Всего настоящих отзывов в базе: $total\n\n";
if (!$go) {
  echo "Если список выглядит правильно, откройте этот же адрес с ?go=1 в конце:\n";
  echo "  https://" . ($_SERVER['HTTP_HOST'] ?? 'ваш-домен') . "/importreviews.php?go=1\n";
} else {
  echo "Отзывы появятся на странице «Отзывы» сразу. Оценка для поисковиков\n";
  echo "считается автоматически, когда настоящих отзывов наберётся хотя бы три.\n";
  echo "ТЕПЕРЬ УДАЛИТЕ с хостинга importreviews.php и reviews.csv.\n";
}
