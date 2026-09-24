# -*- coding: utf-8 -*-
"""Контур Дома — сборка отдельных страниц для поисковиков.

Зачем: адреса разделов сайта идут через решётку (#/house/ladoga), и Яндекс с Google
считают весь сайт одной страницей. Этот скрипт делает настоящие страницы —
по одной на каждый дом, на модули, проекты, цены и компанию, — которые индексируются
и ведут посетителя в калькулятор.

Данные берутся из seo.json, который выгружается из самого сайта, чтобы цены и описания
не пришлось дублировать руками.

Запуск:  python deploy/mkpages.py seo.json .
"""
import io, json, sys, os, datetime

DOMAIN = 'https://konturhouse.ru'
PHONE = '+7 999 888-60-99'
PHONE_HREF = '+79998886099'

CSS = """*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:#0C0D0E;color:#ECE8E1;font:16px/1.6 "Onest","Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
header{position:sticky;top:0;z-index:5;background:rgba(12,13,14,.86);backdrop-filter:blur(12px);border-bottom:1px solid rgba(236,232,225,.12)}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:68px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo b{font-family:"Unbounded",Arial Black,sans-serif;font-weight:800;font-size:16px;letter-spacing:.06em}
.logo i{font-style:normal;font-size:11px;color:#8A9097;letter-spacing:.14em;text-transform:uppercase;border-left:1px solid rgba(236,232,225,.22);padding-left:10px}
.tel{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:14px;text-decoration:none;white-space:nowrap}
h1{font-family:"Unbounded",Arial Black,sans-serif;font-weight:600;font-size:clamp(28px,4.4vw,52px);line-height:1.06;letter-spacing:-.02em;margin:0 0 16px}
h2{font-family:"Unbounded",Arial Black,sans-serif;font-weight:600;font-size:clamp(22px,2.8vw,32px);margin:44px 0 14px}
h3{font-size:19px;margin:26px 0 8px}
p{margin:0 0 14px;color:#C9C6C0;max-width:70ch}
.lead{font-size:19px;color:#ECE8E1}
.crumbs{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;color:#8A9097;padding:22px 0 0}
.crumbs a{text-decoration:none}
.hero-img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:20px;margin:18px 0 26px;background:#1B1E21}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:22px 0}
.facts div{border:1px solid rgba(236,232,225,.12);border-radius:16px;padding:14px 16px;background:#141618}
.facts span{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8A9097;margin-bottom:4px}
.facts b{font-family:"Unbounded",Arial Black,sans-serif;font-size:19px;font-weight:600}
table{width:100%;border-collapse:collapse;margin:14px 0 8px;font-size:15px}
th,td{padding:12px 14px;text-align:right;border-bottom:1px solid rgba(236,232,225,.12);white-space:nowrap}
th:first-child,td:first-child{text-align:left;white-space:normal}
th{font-family:"IBM Plex Mono",ui-monospace,monospace;font-weight:400;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#8A9097}
.tw{overflow-x:auto;border:1px solid rgba(236,232,225,.12);border-radius:18px}
.btn{display:inline-flex;align-items:center;gap:10px;height:50px;padding:0 26px;border-radius:999px;background:#E7A35C;color:#1a120a;font-weight:600;text-decoration:none;margin:6px 8px 6px 0}
.btn.ghost{background:transparent;color:#ECE8E1;border:1px solid rgba(236,232,225,.3);font-weight:400}
ul{color:#C9C6C0;max-width:70ch}
li{margin-bottom:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin:18px 0}
.card{border:1px solid rgba(236,232,225,.12);border-radius:18px;overflow:hidden;background:#141618;text-decoration:none;display:block;transition:border-color .2s}
.card:hover{border-color:rgba(236,232,225,.3)}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#1B1E21}
.card .b{padding:14px 16px}
.card h3{margin:0 0 4px;font-size:17px}
.card p{font-size:13.5px;margin:0 0 8px}
.card b{font-family:"Unbounded",Arial Black,sans-serif;font-size:16px;font-weight:600}
footer{border-top:1px solid rgba(236,232,225,.12);margin-top:60px;padding:30px 0 50px;color:#8A9097;font-size:14px}
footer a{color:#ECE8E1}
.nav-all{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}
.nav-all a{font-size:13.5px;padding:8px 14px;border:1px solid rgba(236,232,225,.16);border-radius:999px;text-decoration:none;color:#C9C6C0}
.nav-all a:hover{border-color:#E7A35C;color:#E7A35C}
"""

PAGE_SIZE = """<p class="crumbs"><a href="/">Главная</a> / <a href="karkasnye-doma.html">Каркасные дома</a> / %(size)s м</p>
<h1>Каркасный дом %(size)s м под ключ</h1>
<p class="lead">%(note)s</p>
<div class="facts">
  <div><span>Размер</span><b>%(size)s м</b></div>
  <div><span>Площадь</span><b>%(area)s м²</b></div>
  <div><span>Проектов</span><b>%(n)d</b></div>
  <div><span>Цена от</span><b>%(lo)s</b></div>
</div>
<div class="cards">%(cards)s</div>
<h2>Сколько стоит дом %(size)s м</h2>
<div class="tw"><table>
<thead><tr><th>Проект</th><th>Холодный контур</th><th>Тёплый контур</th><th>Под ключ</th><th>Сборка</th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
<p>Цены за дом %(size)s м со сборкой на участке, доставка считается отдельно: 300 ₽ за километр. Разница между проектами —
в форме кровли, расположении террасы и комплекте окон: каркас, утепление и работы одинаковые.</p>
<h2>Что помещается в %(area)s м²</h2>
<p>Планировку можно не брать типовую: перегородки переставляются мышью прямо в калькуляторе,
и цена пересчитывается сразу — видно, сколько метров перегородок и сколько дверей добавилось.
Нужен размер между типовыми — впишите свой с шагом 0,5 м: площадь, комплект окон и смета
пересчитаются автоматически.</p>
<h2>Три комплектации</h2>
<p><b>Холодный контур</b> — каркас 50×150, наружная обшивка, ветро-влагозащита, кровля, окна и
входная дверь, черновой пол, фундамент и сборка. <b>Тёплый контур</b> добавляет плиточно-базальтовый утеплитель,
пароизоляцию, вагонку внутри и плиту OSB-3 15 мм на пол. <b>Под ключ</b> — плюс электрика, вода,
канализация, сантехника, освещение, чистовая отделка и покраска фасада.</p>
<p><a class="btn" href="/#/catalog/%(sid)s">Посмотреть все дома %(size)s м</a>
<a class="btn ghost" href="tel:%(phref)s">Позвонить %(phone)s</a></p>"""

PAGE_MOD = """<p class="crumbs"><a href="/">Главная</a> / <a href="moduli-dlya-prozhivaniya.html">Модули</a> / %(name)s</p>
<h1>Модуль «%(name)s»</h1>
<p class="lead">%(txt)s. Размеры %(sizes)s.</p>
<img class="hero-img" src="%(photo)s" alt="Модуль «%(name)s»" loading="lazy">
<div class="tw"><table>
<thead><tr><th>Размер</th><th>Площадь</th><th>Базовая цена</th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
<h2>Что входит в базовую цену</h2>
<ul>
  <li>Каркас из сухой строганой доски, обвязка на бетонных блоках</li>
  <li>Утепление 50 мм, ветро-влагозащита и пароизоляция</li>
  <li>Вагонка снаружи и внутри, класс ВС</li>
  <li>Пол из доски 25 мм</li>
  <li>Односкатная кровля из оцинкованного профлиста</li>
  <li>Деревянное окно 60×90 и вырезная дверь</li>
  <li>Сборка на вашем участке</li>
</ul>
<h2>Что можно поменять</h2>
<p>Утепление до 150 мм — и модулем можно пользоваться зимой. Снаружи вместо вагонки — имитация
бруса, блок-хаус, планкен, сайдинг или профлист, цвет по каталогу RAL. Кровля — двускатная,
с ондулином или металлочерепицей. Внутри — перегородки, санузел, электрика, панорамные окна
и двери. Всё это считается в конструкторе: видно цену каждой позиции.</p>
<h2>Собираем на месте</h2>
<p>Модуль не привозят готовым: бригада собирает его прямо на участке. Не нужен кран и широкий
проезд, а качество видно на каждом этапе. Сборка входит в стоимость, отдельно считается только
доставка материалов — 300 ₽ за километр от производства.</p>
<p><a class="btn" href="/#/modules/%(first)s">Собрать модуль «%(name)s»</a>
<a class="btn ghost" href="tel:%(phref)s">Позвонить %(phone)s</a></p>"""

PAGE_DELIVERY = """<p class="crumbs"><a href="/">Главная</a> / Доставка и сборка</p>
<h1>Доставка и сборка по Центральному федеральному округу</h1>
<p class="lead">Сборка дома или модуля на вашем участке входит в цену. Отдельно считается только
доставка материалов — 300 ₽ за каждый километр от производства.</p>
<div class="tw"><table>
<thead><tr><th>Регион</th><th>Расстояние</th><th>Доставка, ориентировочно</th></tr></thead>
<tbody>%(rows)s</tbody></table></div>
<p>Расстояния в таблице — до областных центров, поэтому это ориентир, а не окончательная сумма.
Точную цифру менеджер называет по адресу участка: в калькуляторе есть поле, где можно указать
адрес и сразу увидеть доставку в смете.</p>
<h2>Как проходит сборка</h2>
<ul>
  <li><b>Выезд инженера.</b> Смотрим грунт, рельеф и подъезд, фиксируем цену в договоре. Бесплатно.</li>
  <li><b>Основание.</b> Блоки или винтовые сваи — 1–2 дня.</li>
  <li><b>Сборка.</b> Бригада привозит материалы и собирает дом на месте: от 3 дней для компактных проектов до 14 для больших.</li>
  <li><b>Приёмка.</b> Вы осматриваете дом, подписываете акт — и только тогда платите.</li>
</ul>
<h2>Что нужно от вас</h2>
<p>Ровная площадка под пятно застройки, подъезд для грузовой машины и электричество 220 В
поблизости — если его нет, привозим генератор. Разрешение на строительство для дома до 20 метров
по каждой стороне не требуется: достаточно уведомления, поможем его оформить.</p>
<p><a class="btn" href="/#/catalog">Посчитать дом с доставкой</a>
<a class="btn ghost" href="tel:%(phref)s">Уточнить по своему адресу</a></p>"""

PAGE_FAQ = """<p class="crumbs"><a href="/">Главная</a> / Вопросы</p>
<h1>Частые вопросы</h1>
<p class="lead">Собрали то, что спрашивают перед заказом. Если чего-то не хватает — позвоните,
ответим без «пришлите техзадание».</p>
%(items)s
<p><a class="btn" href="/#/catalog">Собрать свой дом</a>
<a class="btn ghost" href="tel:%(phref)s">Позвонить %(phone)s</a></p>
%(ld)s"""

ART_INS = """<p class="crumbs"><a href="/">Главная</a> / Утепление каркасного дома</p>
<h1>Утепление каркасного дома: сколько миллиметров нужно</h1>
<p class="lead">Короткий ответ: 100 мм — для дачи на тёплый сезон, 150 мм — для круглогодичной
жизни в средней полосе, 200 мм — для зимы с запасом, 250 мм — для Урала и Сибири.</p>
<h2>Что стоит за цифрами</h2>
<p>Утеплитель — плиточно-базальтовые плиты, их укладывают враспор между стойками каркаса. Чем толще
слой, тем выше сопротивление теплопередаче: 100 мм дают примерно R 2,6, 150 мм — R 3,9,
200 мм — R 5,3, 250 мм — R 6,6. Для средней полосы стена должна быть не ниже R 3,1 — то есть
150 мм это разумный минимум для дома, в котором живут зимой.</p>
<h2>Как меняется каркас</h2>
<p>Толщина утеплителя задаёт сечение стойки: под 100 мм ставят доску 50×100, под 150 — 50×150,
под 200 — 50×200, под 250 делают перекрёстный каркас, чтобы убрать мостики холода по стойкам.
Поэтому утепление — это не только утеплитель: вместе с ним дорожает и сам каркас, и это уже учтено
в калькуляторе.</p>
<h2>Что ещё влияет на тепло</h2>
<ul>
  <li><b>Пароизоляция изнутри и ветро-влагозащита снаружи.</b> Без них утеплитель намокает и перестаёт греть. Входят в цену.</li>
  <li><b>Окна.</b> Однокамерный стеклопакет дешевле, но зимой через него уходит заметно больше тепла, чем через двухкамерный.</li>
  <li><b>Пол и потолок.</b> Их утепляют не тоньше стен, иначе тепло уходит вниз и вверх.</li>
  <li><b>Фундамент.</b> На винтовых сваях пол холоднее, чем на утеплённой шведской плите.</li>
</ul>
<h2>Сколько это стоит</h2>
<p>Переход со 100 на 150 мм добавляет к смете примерно 850 ₽ за квадратный метр стены,
на 200 мм — 1 700 ₽, на 250 мм — 2 700 ₽. Для дома 6×8 м это ориентировочно 50, 100 и 160 тысяч
рублей. Точную цифру покажет калькулятор — он считает по реальной площади стен вашего дома.</p>
<p><a class="btn" href="/#/how">Посмотреть, как устроена стена</a>
<a class="btn ghost" href="karkasnye-doma.html">Выбрать проект</a></p>"""

ART_FOUND = """<p class="crumbs"><a href="/">Главная</a> / Фундамент для каркасного дома</p>
<h1>Фундамент для каркасного дома: блоки, сваи или плита</h1>
<p class="lead">Каркасный дом лёгкий, поэтому ему не нужен массивный фундамент. Выбор сводится
к трём вариантам, и решает не столько цена, сколько грунт на участке.</p>
<h2>Бетонные блоки</h2>
<p>Блоки 400×200×200 на подсыпке, сверху лаги 100×150. Самый доступный вариант, входит в базовую
цену дома. Подходит для плотного грунта без сильного пучения и для ровного участка. Дом стоит
на продуваемом подполье — пол нужно хорошо утеплить.</p>
<h2>Винтовые сваи</h2>
<p>Сваи Ø76, Ø89 или Ø108 длиной 2 или 2,5 метра завинчиваются ниже глубины промерзания.
Вариант для пучинистого и слабого грунта, для уклона и для участков, где нельзя копать.
Количество считается по пятну дома: шаг 2,5 м для одноэтажных, 2 м — для мансарды и двух этажей.
Свая с завинчиванием и оголовком стоит от 4 000 до 6 000 ₽, калькулятор сразу покажет, сколько
их нужно именно вашему дому.</p>
<h2>Утеплённая шведская плита</h2>
<p>Монолитная плита с утеплителем и уже уложенным контуром тёплого пола. Самый дорогой вариант
и самый комфортный: ровное основание, тёплый пол без досборки, никакого подполья. Имеет смысл,
если планируете жить круглый год и хотите водяной тёплый пол — при УШП он обходится заметно дешевле.</p>
<h2>Что выбрать</h2>
<ul>
  <li><b>Дача на сезон, плотный грунт</b> — блоки.</li>
  <li><b>Глина, торф, уклон, высокие грунтовые воды</b> — винтовые сваи.</li>
  <li><b>Постоянное жильё и тёплый пол</b> — УШП.</li>
</ul>
<p>Окончательное решение принимается после выезда инженера: он смотрит грунт и рельеф.
Выезд бесплатный, цена фиксируется в договоре уже после него.</p>
<p><a class="btn" href="/#/catalog">Посчитать дом с разным фундаментом</a>
<a class="btn ghost" href="tel:%(phref)s">Спросить про свой участок</a></p>"""

ART_WINTER = """<p class="crumbs"><a href="/">Главная</a> / Строительство зимой</p>
<h1>Можно ли строить каркасный дом зимой</h1>
<p class="lead">Да. Каркасная технология не требует мокрых процессов: нет бетона, который должен
набрать прочность, нет штукатурки, которой нужно сохнуть. Зимой мы работаем так же, как летом.</p>
<h2>Почему зима не мешает</h2>
<p>Каркас собирается из сухой строганой доски камерной сушки — её влажность не зависит от погоды.
Утеплитель приезжает в упаковке и укладывается в закрытый контур. Винтовые сваи завинчиваются
в мёрзлый грунт без проблем, а бетонные блоки ставятся на подготовленную подсыпку.</p>
<h2>Что реально меняется</h2>
<ul>
  <li><b>Короткий световой день.</b> Бригада работает меньше часов, поэтому срок может сдвинуться на день-два.</li>
  <li><b>Подъезд к участку.</b> Главное, чтобы техника доехала — это стоит проверить заранее.</li>
  <li><b>Отделка «под ключ».</b> Финишную покраску фасада лучше перенести на плюсовую температуру, внутренние работы идут как обычно.</li>
</ul>
<h2>Плюс зимнего заказа</h2>
<p>Зимой у бригад свободнее график: дом собирают быстрее, чем в разгар сезона, и к весне вы
въезжаете в готовый дом, а не встаёте в очередь на май. Сроки сборки — от 3 дней для компактных
проектов до 14 для больших, и они держатся круглый год.</p>
<p><a class="btn" href="karkasnye-doma.html">Выбрать проект</a>
<a class="btn ghost" href="tel:%(phref)s">Спросить про сроки</a></p>"""

ART_PRICE = """<p class="crumbs"><a href="/">Главная</a> / Сколько стоит каркасный дом</p>
<h1>Сколько стоит каркасный дом под ключ</h1>
<p class="lead">От %(lo)s за компактный дом в холодном контуре и примерно вдвое больше за тот же
дом под ключ. Разброс объясняется не «жадностью подрядчика», а тем, что входит в цену.</p>
<h2>Три уровня готовности</h2>
<p><b>Холодный контур</b> — каркас, наружная обшивка, ветро-влагозащита, кровля, окна и входная
дверь, черновой пол, фундамент и сборка. Дом закрыт и защищён от погоды, отделку делаете потом.</p>
<p><b>Тёплый контур</b> — плюс плиточно-базальтовый утеплитель, пароизоляция, вагонка внутри и плита OSB-3 15 мм
на полу. В таком доме можно жить, осталась чистовая отделка и инженерия.</p>
<p><b>Под ключ</b> — плюс электрика, водоснабжение и канализация, сантехника, освещение,
чистовая отделка и покраска фасада в два слоя. Заезжаете с вещами.</p>
<h2>На что ещё смотреть в смете</h2>
<ul>
  <li><b>Фундамент.</b> Блоки входят в цену, сваи и УШП считаются отдельно.</li>
  <li><b>Утепление.</b> 100 мм в базе, 150–250 мм — доплата за утеплитель и за более толстый каркас.</li>
  <li><b>Окна.</b> Панорамные и порталы стоят в разы дороже обычных — самая недооценённая строка сметы.</li>
  <li><b>Терраса и крыльцо.</b> Считаются по квадратным метрам и легко добавляют сотню тысяч.</li>
  <li><b>Доставка.</b> 300 ₽ за каждый километр от производства.</li>
</ul>
<h2>Как не попасть на «плюс 30%% в процессе»</h2>
<p>Главный признак честной цены — смета, разложенная по строкам, а не одна цифра «дом под ключ».
Наш калькулятор показывает каждую позицию: сколько свай, сколько метров перегородок, сколько
стоит каждое окно. Цена фиксируется в договоре после выезда инженера и дальше не меняется,
а основная оплата — после приёмки: аванс 10–30%% в первый день работ, остальное — когда вы приняли дом.</p>
<p><a class="btn" href="tseny.html">Посмотреть прайс</a>
<a class="btn ghost" href="/#/catalog">Собрать свой дом</a></p>"""

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 34 34'%3E"
        "%3Crect width='34' height='34' rx='7' fill='%230C0D0E'/%3E"
        "%3Cg transform='translate(0,3)' fill='none' stroke='%23E7A35C' stroke-width='1.9' "
        "stroke-linecap='round' stroke-linejoin='round'%3E"
        "%3Cpath d='M2 28V13L17 2l15 11v15'/%3E%3Cpath d='M8 28V16l9-6.5 9 6.5v12'/%3E%3Cpath d='M14 28v-7h6v7'/%3E"
        "%3C/g%3E%3C/svg%3E")


def rub(n):
    return '{:,.0f}'.format(round(n)).replace(',', ' ') + ' ₽'


def fmt(v):
    s = ('%g' % v).replace('.', ',')
    return s


def cut(s, n=120):
    """Обрезаем описание по границе слова, чтобы не было «окно 1. Х»."""
    s = ' '.join(str(s).split())
    if len(s) <= n:
        return s.rstrip(' .,;:—-')
    return s[:n].rsplit(' ', 1)[0].rstrip(' .,;:—-')


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


BRAND = ' | Контур Дома'


def fit_title(s, lim=70):
    """Поисковик обрезает длинный заголовок — убираем бренд, если не помещается."""
    s = ' '.join(str(s).split())
    if len(s) <= lim:
        return s
    if s.endswith(BRAND):
        short = s[:-len(BRAND)]
        if len(short) <= lim:
            return short
        return cut(short, lim)
    return cut(s, lim)


# откуда пришёл посетитель (метки рекламы, поиск) — тот же ключ, что у основного сайта:
# заявка, оставленная потом на главной, уйдёт с источником
SRC_JS = ("<script>(function(){try{var q=new URLSearchParams(location.search),s={},n=0;"
  "['utm_source','utm_medium','utm_campaign','utm_content','utm_term','yclid','gclid'].forEach(function(k){var v=q.get(k);if(v){s[k]=v.slice(0,200);n++}});"
  "var ref='';try{if(document.referrer){var r=new URL(document.referrer);if(r.host!==location.host)ref=r.host.replace(/^www\./,'')}}catch(e){}"
  "var land=location.pathname.slice(0,80),old=null;try{old=JSON.parse(localStorage.getItem('kontur.src')||'null')}catch(e){}"
  "var fresh=old&&Date.now()-(old.at||0)<2592e6,v=null;"
  "if(n){s.land=land;s.at=Date.now();if(ref)s.ref=ref;v=s}"
  "else if(ref&&!(fresh&&(old.utm_source||old.yclid)))v={ref:ref,land:land,at:Date.now()};"
  "else if(!fresh)v={land:land,at:Date.now()};"
  "if(v)localStorage.setItem('kontur.src',JSON.stringify(v))}catch(e){}})()</script>")


def page(slug, title, desc, body, nav, extra_ld=''):
    title = fit_title(title)
    desc = cut(desc, 178) + '.' if len(desc) > 178 else desc
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{DOMAIN}/{slug}">
<meta name="theme-color" content="#0C0D0E">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Контур Дома">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{DOMAIN}/{slug}">
<meta property="og:locale" content="ru_RU">
<link rel="icon" type="image/svg+xml" href="{ICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600;800&family=Onest:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>{CSS}</style>
{SRC_JS}
{extra_ld}
</head>
<body>
<header><div class="wrap">
  <a class="logo" href="/"><svg width="30" height="27" viewBox="0 0 34 30" fill="none" stroke="#E7A35C" stroke-width="1.6"><path d="M2 28V13L17 2l15 11v15"/><path d="M8 28V16l9-6.5 9 6.5v12"/><path d="M14 28v-7h6v7"/></svg><b>КОНТУР</b><i>дома</i></a>
  <a class="tel" href="tel:{PHONE_HREF}">{PHONE}</a>
</div></header>
<main class="wrap">
{body}
<div class="nav-all">{nav}</div>
</main>
<footer><div class="wrap">
  <p>«Контур Дома» — каркасные дома и утеплённые модули под ключ. Работаем по всему Центральному федеральному округу.
  Сборка на участке входит в цену, гарантия 3 года, оплата частями: аванс 10–30%, остальное после приёмки.</p>
  <p><a href="tel:{PHONE_HREF}">{PHONE}</a> · <a href="/">Калькулятор и каталог</a></p>
</div></footer>
</body>
</html>
"""


def house_page(h, all_houses):
    slug = 'dom-%s.html' % h['id']
    nm = h['name']
    size = '%s×%s' % (fmt(h['w']), fmt(h['d']))
    title = f"Каркасный дом «{nm}» {size} м под ключ — цена от {rub(h['price'])} | Контур Дома"
    desc = (f"Каркасный дом «{nm}» {size} м, {fmt(h['area'])} м². {cut(h['lead'], 95)}. "
            f"Холодный контур от {rub(h['price'])}, под ключ {rub(h['key'])}, сборка {h['days']} дн.")
    rooms = ', '.join('%s %s×%s м' % (r['n'].lower(), fmt(r['w']), fmt(r['d'])) for r in h['plan'])
    wins = ', '.join('%s — %d шт' % (w['n'].lower(), w['c']) for w in h['wins'])
    img = f'<img class="hero-img" src="{h["photo"]}" alt="Каркасный дом «{esc(nm)}» {size} м" loading="lazy">' if h['photo'] else ''

    sizes_rows = ''.join(
        f"<tr><td>{fmt(s['w'])} × {fmt(s['d'])} м</td><td>{fmt(s['area'])} м²</td>"
        f"<td>{rub(s['price'])}</td><td>{rub(s['warm'])}</td><td>{rub(s['key'])}</td></tr>"
        for s in h['sizes'])

    ld = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Product","name":"Каркасный дом «{nm}» {size} м",
 "description":"{esc(h['lead'])}","category":"Каркасные дома",
 "brand":{{"@type":"Brand","name":"Контур Дома"}},
 "offers":{{"@type":"AggregateOffer","priceCurrency":"RUB","lowPrice":"{h['price']}","highPrice":"{h['key']}",
  "offerCount":"{len(h['sizes'])}","availability":"https://schema.org/InStock"}}}}
</script>"""

    others = ' '.join(f'<a href="dom-{o["id"]}.html">{o["name"]} {fmt(o["w"])}×{fmt(o["d"])}</a>'
                      for o in all_houses if o['id'] != h['id'])

    body = f"""<p class="crumbs"><a href="/">Главная</a> / <a href="karkasnye-doma.html">Каркасные дома</a> / {esc(nm)}</p>
<h1>Каркасный дом «{esc(nm)}» {size} м</h1>
<p class="lead">{esc(h['lead'])}.</p>
{img}
<div class="facts">
  <div><span>Размер</span><b>{size} м</b></div>
  <div><span>Площадь</span><b>{fmt(h['area'])} м²</b></div>
  <div><span>Этажей</span><b>{esc(h['floorsLabel'] or ('%s' % fmt(h['floors'])))}</b></div>
  <div><span>Спален</span><b>{h['beds']}</b></div>
  <div><span>Сборка</span><b>{h['days']} дн.</b></div>
  <div><span>Цена от</span><b>{rub(h['price'])}</b></div>
</div>
<p><a class="btn" href="/#/house/{h['id']}">Рассчитать в калькуляторе</a>
<a class="btn ghost" href="tel:{PHONE_HREF}">Позвонить {PHONE}</a></p>

<h2>Что входит в цену</h2>
<p>Дом «{esc(nm)}» строится в трёх комплектациях. <b>Холодный контур</b> — каркас 50×150 из сухой строганой доски,
наружная обшивка, ветро-влагозащита, кровля, окна и входная дверь, черновой пол, фундамент и сборка на участке.
<b>Тёплый контур</b> добавляет утепление плиточно-базальтовым утеплителем, пароизоляцию, внутреннюю обшивку вагонкой и плиту OSB-3 15 мм на пол.
<b>Под ключ</b> — это ещё электрика, водоснабжение и канализация, сантехника, освещение, чистовая отделка и покраска фасада в два слоя.</p>
<div class="tw"><table>
<thead><tr><th>Размер</th><th>Площадь</th><th>Холодный контур</th><th>Тёплый контур</th><th>Под ключ</th></tr></thead>
<tbody>{sizes_rows}</tbody>
</table></div>
<p>Цены указаны за дом со сборкой на участке, доставка — 300 ₽ за километр от производства. Любой размер можно изменить с шагом 0,5 м —
площадь, планировка и смета пересчитаются в калькуляторе.</p>

<h2>Планировка и характеристики</h2>
<p>В базовой планировке: {esc(rooms)}.{' Терраса %s м² под общей кровлей.' % fmt(h['terrace']) if h['terrace'] else ''}
Перегородки можно переставить, нарисовать свои или заказать планировку с нуля — цена пересчитается автоматически.</p>
<ul>
  <li><b>Окна:</b> {esc(wins) if wins else 'по проекту'}. Профиль ПВХ двухкамерный, на выбор деревянные, однокамерные ПВХ и тёплый алюминий</li>
  <li><b>Фундамент:</b> {esc(h['base'])}, возможны винтовые сваи и УШП</li>
  <li><b>Фасад:</b> имитация бруса 16 мм, на выбор вагонка, блок-хаус, планкен, сайдинг, профлист, фиброцемент</li>
  <li><b>Кровля:</b> профлист, ондулин, металлочерепица, мягкая черепица или фальц</li>
  {'<li><b>Потолки:</b> %s</li>' % esc(h['ceil']) if h['ceil'] else ''}
  <li><b>Срок:</b> {h['weeks']} недель от договора, сборка на участке {h['days']} дн.</li>
</ul>

<h2>Как заказать</h2>
<p>Откройте дом в калькуляторе, выберите размер, комплектацию и отделку — смета соберётся сразу, с точностью до рубля.
Оттуда же отправляется заявка: она попадёт к менеджеру вместе с вашей планировкой, и дальше вы общаетесь в личном кабинете.
Оплата частями: аванс 10–30% в первый день работ, остальное — после того как вы примете дом.</p>
<p><a class="btn" href="/#/house/{h['id']}">Собрать дом «{esc(nm)}» в калькуляторе</a></p>
{ld}
"""
    nav = f'<a href="karkasnye-doma.html">Все дома</a> {others} <a href="moduli-dlya-prozhivaniya.html">Модули</a>'
    return slug, page(slug, title, desc, body, nav)


def min_house(houses):
    """Самый доступный дом: минимум по всем размерам всех проектов, холодный контур."""
    return min(s['price'] for h in houses for s in (h.get('sizes') or [{'price': h['price']}]))


def houses_hub(houses):
    slug = 'karkasnye-doma.html'
    title = 'Каркасные дома под ключ — 8 проектов от 6×4 до 12×10 м | Контур Дома'
    desc = ('Каркасные дома под ключ: восемь проектов от %s. Свой размер с шагом 0,5 м, расчёт сметы онлайн, '
            'сборка на участке за 3–14 дней, гарантия 3 года, оплата частями, остаток после приёмки.'
            % rub(min_house(houses)))
    cards = ''.join(
        f"""<a class="card" href="dom-{h['id']}.html">
  <img src="{h['photo']}" alt="Каркасный дом «{esc(h['name'])}»" loading="lazy">
  <div class="b"><h3>{esc(h['name'])} {fmt(h['w'])}×{fmt(h['d'])} м</h3>
  <p>{fmt(h['area'])} м², {h['beds']} спал., сборка {h['days']} дн.</p>
  <b>от {rub(h['price'])}</b></div></a>""" for h in houses)
    body = f"""<p class="crumbs"><a href="/">Главная</a> / Каркасные дома</p>
<h1>Каркасные дома под ключ</h1>
<p class="lead">Восемь готовых проектов от 6×4 до 12×10 м. Любой можно построить в своём размере —
шаг 0,5 м, площадь и цена пересчитываются сразу.</p>
<div class="cards">{cards}</div>
<h2>Три комплектации</h2>
<p><b>Холодный контур</b> — каркас, обшивка, кровля, окна и дверь, черновой пол, фундамент и сборка.
Дом стоит закрытым, отделку делаете сами или позже заказываете у нас.</p>
<p><b>Тёплый контур</b> — плюс плиточно-базальтовый утеплитель, пароизоляция, вагонка внутри и OSB-3 15 мм на полу.
В таком доме можно жить круглый год: с утеплением 150 мм зимой в Подмосковье, 200–250 мм — на Урале и в Сибири.</p>
<p><b>Под ключ</b> — заезжаете с вещами: электрика, вода, канализация, сантехника, освещение,
чистовая отделка и покраска фасада уже сделаны.</p>
<h2>Почему каркас</h2>
<p>Дом собирается на заводе и на участке за 3–14 дней, не требует усадки, не боится зимнего монтажа
и стоит дешевле бруса при той же тёплой стене. Каркас — сухая строганая доска 50×150 камерной сушки,
утеплитель — плиточно-базальтовые плиты, снаружи ветро-влагозащита и вентилируемый фасад.</p>
<p><a class="btn" href="/#/catalog">Открыть каталог с калькулятором</a></p>"""
    nav = ' '.join(f'<a href="dom-{h["id"]}.html">{h["name"]}</a>' for h in houses)
    return slug, page(slug, title, desc, body, nav + ' <a href="moduli-dlya-prozhivaniya.html">Модули</a>')


def mods_page(mods):
    slug = 'moduli-dlya-prozhivaniya.html'
    lo = min(s['price'] for m in mods for s in m['sizes'])
    title = 'Модули для проживания — утеплённые бытовки от %s | Контур Дома' % rub(lo)
    desc = ('Утеплённые модули для дачи, стройки и постоянной жизни: пять линеек от 5×2 до 6×6 м. '
            'Собираем на вашем участке, сборка входит в цену, гарантия 3 года.')
    cards = ''.join(
        f"""<a class="card" href="/#/modules/{m['sizes'][0]['id']}">
  <img src="{m['photo']}" alt="Модуль «{esc(m['name'])}»" loading="lazy">
  <div class="b"><h3>Модуль «{esc(m['name'])}»</h3><p>{esc(m['txt'])}</p>
  <b>от {rub(min(s['price'] for s in m['sizes']))}</b></div></a>""" for m in mods)
    rows = ''.join(
        f"<tr><td>«{esc(m['name'])}»</td><td>{fmt(s['w'])} × {fmt(s['d'])} м</td><td>{fmt(s['area'])} м²</td><td>{rub(s['price'])}</td></tr>"
        for m in mods for s in m['sizes'])
    body = f"""<p class="crumbs"><a href="/">Главная</a> / Модули для проживания</p>
<h1>Модули для проживания</h1>
<p class="lead">Утеплённые бытовки для дачи, стройки и постоянной жизни. Пять линеек от 5×2 до 6×6 м,
любой размер можно задать свой.</p>
<div class="cards">{cards}</div>
<h2>Цены по размерам</h2>
<div class="tw"><table>
<thead><tr><th>Модель</th><th>Размер</th><th>Площадь</th><th>Базовая цена</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p>В базовую цену входит каркас, утепление 50 мм, вагонка снаружи и внутри, пол из доски, односкатная кровля
из оцинкованного профлиста, окно и вырезная дверь. Всё остальное настраивается: утепление до 150 мм,
имитация бруса или блок-хаус, двускатная кровля, панорамные окна, перегородки и санузел.</p>
<h2>Собираем на вашем участке</h2>
<p>Модуль не привозят готовым — его собирает наша бригада прямо на месте, поэтому нет ограничений
по проезду и крану, а качество видно на каждом этапе. Сборка входит в стоимость, отдельно считается
только доставка материалов — 300 ₽ за километр.</p>
<p><a class="btn" href="/#/catalog/modules">Собрать модуль и узнать цену</a></p>"""
    return slug, page(slug, title, desc, body,
                      '<a href="karkasnye-doma.html">Каркасные дома</a> <a href="nashi-proekty.html">Наши проекты</a> <a href="tseny.html">Цены</a>')


def prices_page(houses, mods):
    slug = 'tseny.html'
    title = 'Цены на каркасные дома и модули 2026 — прайс | Контур Дома'
    desc = ('Актуальные цены: каркасные дома от %s, модули от %s. Три комплектации, '
            'сборка на участке включена, доставка 300 ₽ за км, аванс 10–30%%, остальное после приёмки.'
            % (rub(min_house(houses)), rub(min(s['price'] for m in mods for s in m['sizes']))))
    rows = ''.join(
        f"<tr><td>«{esc(h['name'])}» {fmt(h['w'])} × {fmt(h['d'])} м</td><td>{fmt(h['area'])} м²</td>"
        f"<td>{rub(h['price'])}</td><td>{rub(h['warm'])}</td><td>{rub(h['key'])}</td></tr>" for h in houses)
    mrows = ''.join(
        f"<tr><td>Модуль «{esc(m['name'])}» {fmt(s['w'])} × {fmt(s['d'])} м</td><td>{fmt(s['area'])} м²</td><td colspan=\"3\">{rub(s['price'])}</td></tr>"
        for m in mods for s in m['sizes'])
    body = f"""<p class="crumbs"><a href="/">Главная</a> / Цены</p>
<h1>Цены на дома и модули</h1>
<p class="lead">Полный прайс на {datetime.date.today().year} год. Сборка на участке уже внутри цены,
доставка считается отдельно — 300 ₽ за километр. Оплата — после того как вы примете работу.</p>
<div class="tw"><table>
<thead><tr><th>Проект</th><th>Площадь</th><th>Холодный контур</th><th>Тёплый контур</th><th>Под ключ</th></tr></thead>
<tbody>{rows}{mrows}</tbody></table></div>
<h2>Из чего складывается цена</h2>
<p>Базовая цена — за дом в указанном размере и комплектации. Дальше смета меняется от ваших решений:
фундамент (блоки, винтовые сваи или УШП), толщина утеплителя, фасад, кровля, комплект окон,
перегородки и двери, терраса, крыльцо, инженерия. Калькулятор показывает каждую строку отдельно,
поэтому видно, на чём складывается сумма и где можно сэкономить.</p>
<p>Доставка считается от производства — 300 ₽ за каждый километр. Промокоды на скидку
от 5 до 20% выдаются ветеранам, людям с инвалидностью, пенсионерам и многодетным семьям.</p>
<p><a class="btn" href="/#/prices">Открыть калькулятор</a></p>"""
    return slug, page(slug, title, desc, body,
                      '<a href="karkasnye-doma.html">Каркасные дома</a> <a href="moduli-dlya-prozhivaniya.html">Модули</a> <a href="o-kompanii.html">О компании</a>')


def projects_page(prj):
    slug = 'nashi-proekty.html'
    title = 'Наши работы — построенные дома и модули | Контур Дома'
    desc = 'Фотографии построенных домов и модулей: что именно мы собираем на участках клиентов. Понравился объект — считаем такой же в калькуляторе.'
    cards = ''.join(
        f"""<a class="card" href="/#/projects">
  <img src="{p['img']}" alt="{esc(p['name'])}" loading="lazy">
  <div class="b"><h3>{esc(p['name'])}</h3><p>{esc(p['txt'])}</p>
  <b>{esc(p['mod'].replace('x', '×') + ' м' if p['mod'] else 'каркасный дом')}</b></div></a>""" for p in prj)
    body = f"""<p class="crumbs"><a href="/">Главная</a> / Наши проекты</p>
<h1>Что мы построили</h1>
<p class="lead">Фотографии с наших объектов — дома и модули, которые уже стоят у заказчиков.</p>
<div class="cards">{cards}</div>
<p>Понравился объект — откройте его в калькуляторе: размер, отделку и оснащение можно поменять под себя,
а готовую смету с фотографией отправить менеджеру.</p>
<p><a class="btn" href="/#/projects">Открыть галерею с расчётом</a></p>"""
    return slug, page(slug, title, desc, body,
                      '<a href="karkasnye-doma.html">Каркасные дома</a> <a href="moduli-dlya-prozhivaniya.html">Модули</a> <a href="o-kompanii.html">О компании</a>')


def about_page():
    slug = 'o-kompanii.html'
    title = 'О компании «Контур Дома» — каркасные дома в ЦФО'
    desc = ('«Контур Дома» строит каркасные дома и модули пятый год. Прозрачная смета до рубля, '
            'сборка на участке, гарантия 3 года, оплата частями. Работаем по Центральному федеральному округу.')
    body = f"""<p class="crumbs"><a href="/">Главная</a> / О компании</p>
<h1>О компании «Контур Дома»</h1>
<p class="lead">Строим каркасные дома и утеплённые модули пятый год. Основатель — Никита Соловьёв.</p>
<p>Мы начинали с простой мысли: частный дом должен быть доступным и понятным. Не «договоритесь на месте»,
а честная смета, в которой видно каждую строку — от количества свай до метров вагонки. Поэтому весь расчёт
вынесен на сайт: вы сами собираете дом в калькуляторе и видите цену до копейки ещё до звонка.</p>
<h2>Как мы работаем</h2>
<ul>
  <li><b>Прозрачно.</b> Смета собирается построчно, цена фиксируется в договоре после выезда на участок.</li>
  <li><b>Гибко.</b> Любой проект строится в своём размере, планировку можно нарисовать самому.</li>
  <li><b>Основная оплата — после приёмки.</b> Аванс 10–30% в первый день работ, остальное — когда вы приняли дом и подписали акт.</li>
  <li><b>С гарантией.</b> 3 года на каркас, отделку и инженерию.</li>
</ul>
<h2>География</h2>
<p>Работаем по всему Центральному федеральному округу: Москва и область, Тверская, Ярославская,
Владимирская, Калужская, Тульская, Рязанская, Смоленская, Брянская, Орловская, Курская, Белгородская,
Липецкая, Тамбовская, Воронежская, Костромская и Ивановская области. Доставка считается от производства —
300 ₽ за километр, точную сумму менеджер называет по адресу участка.</p>
<h2>Льготы</h2>
<p>Промокоды на скидку от 5 до 20% выдаём ветеранам, людям с инвалидностью, пенсионерам и многодетным
семьям — и в других случаях, обсудим индивидуально.</p>
<p><a class="btn" href="/#/about">Подробнее на сайте</a> <a class="btn ghost" href="tel:{PHONE_HREF}">Позвонить {PHONE}</a></p>"""
    return slug, page(slug, title, desc, body,
                      '<a href="karkasnye-doma.html">Каркасные дома</a> <a href="moduli-dlya-prozhivaniya.html">Модули</a> <a href="tseny.html">Цены</a> <a href="nashi-proekty.html">Наши проекты</a>')


# ---------- страницы под размер: «каркасный дом 6 на 8» ----------
SIZE_NOTE = {
 '6x4': 'Самый компактный размер: дачный домик на одну спальню и кухню-гостиную, встаёт даже на узкий участок.',
 '6x5': 'Классика выходного дня: спальня, кухня-гостиная и душевая помещаются без тесноты.',
 '6x6': 'Квадрат на 36 м² — комната, кухня и санузел либо одна большая студия с панорамным окном.',
 '6x7': 'Две спальни и общая комната: размер для семьи с ребёнком.',
 '6x8': 'Вытянутый дом на 48 м²: две спальни, кухня-гостиная и полноценный санузел.',
 '8x8': 'Первый «настоящий» дом: 64 м², три спальни или две спальни с большой гостиной.',
 '10x10': 'Сто метров для постоянной жизни: спальни, гостиная, кухня, санузел и гардероб.',
 '12x10': 'Дом для большой семьи: 120 м², можно выделить кабинет, детскую и гостевую.',
}


def size_pages(houses):
    """По одной странице на каждый типовой размер — это самые частые запросы."""
    order, seen = [], set()
    for h in houses:
        for s in h['sizes']:
            if s['id'] not in seen:
                seen.add(s['id'])
                order.append(s)
    order.sort(key=lambda s: s['w'] * s['d'])
    out = []
    for s in order:
        sid = s['id']
        size = '%s×%s' % (fmt(s['w']), fmt(s['d']))
        fit = [(h, x) for h in houses for x in h['sizes'] if x['id'] == sid]
        if not fit:
            continue
        lo = min(x['price'] for _, x in fit)
        slug = 'karkasnyy-dom-%s.html' % sid
        title = 'Каркасный дом %s м под ключ — цена от %s | Контур Дома' % (size, rub(lo))
        desc = ('Каркасный дом %s м (%s м²) под ключ: %d проекта на выбор, цены от %s. '
                'Планировка на ваш вкус, сборка на участке, оплата частями.'
                % (size, fmt(s['area']), len(fit), rub(lo)))
        rows = ''.join(
            '<tr><td><a href="dom-%s.html">«%s»</a></td><td>%s</td><td>%s</td><td>%s</td><td>%d дн.</td></tr>'
            % (h['id'], esc(h['name']), rub(x['price']), rub(x['warm']), rub(x['key']), h['days'])
            for h, x in fit)
        cards = ''.join(
            '<a class="card" href="dom-%s.html"><img src="%s" alt="Каркасный дом «%s» %s м" loading="lazy">'
            '<div class="b"><h3>«%s» %s м</h3><p>%s</p><b>от %s</b></div></a>'
            % (h['id'], h['photo'], esc(h['name']), size, esc(h['name']), size,
               esc(cut(h['lead'], 80)), rub(x['price']))
            for h, x in fit)
        body = PAGE_SIZE % {
            'size': size, 'sid': sid, 'area': fmt(s['area']), 'n': len(fit), 'lo': rub(lo),
            'note': SIZE_NOTE.get(sid, 'Площадь %s м² — считаем в трёх комплектациях.' % fmt(s['area'])),
            'cards': cards, 'rows': rows, 'phone': PHONE, 'phref': PHONE_HREF}
        nav = ' '.join('<a href="karkasnyy-dom-%s.html">%s×%s м</a>' % (o['id'], fmt(o['w']), fmt(o['d']))
                       for o in order if o['id'] != sid)
        out.append((slug, page(slug, title, desc, body,
                               '<a href="karkasnye-doma.html">Все дома</a> ' + nav)))
    return out


# ---------- страницы модулей ----------
def mod_pages(mods):
    out = []
    for m in mods:
        slug = 'modul-%s.html' % m['id']
        lo = min(s['price'] for s in m['sizes'])
        sizes = ', '.join('%s×%s м' % (fmt(s['w']), fmt(s['d'])) for s in m['sizes'])
        title = 'Модуль «%s» %s — утеплённая бытовка от %s | Контур Дома' % (m['name'], sizes, rub(lo))
        desc = ('Модуль «%s»: %s. Размеры %s, цена от %s. Собираем на вашем участке, '
                'сборка входит в цену, гарантия 3 года.' % (m['name'], m['txt'].lower(), sizes, rub(lo)))
        rows = ''.join('<tr><td>%s × %s м</td><td>%s м²</td><td>%s</td></tr>'
                       % (fmt(s['w']), fmt(s['d']), fmt(s['area']), rub(s['price'])) for s in m['sizes'])
        others = ' '.join('<a href="modul-%s.html">«%s»</a>' % (o['id'], o['name'])
                          for o in mods if o['id'] != m['id'])
        body = PAGE_MOD % {'name': esc(m['name']), 'txt': esc(m['txt']), 'sizes': sizes,
                           'photo': m['photo'], 'rows': rows, 'first': m['sizes'][0]['id'],
                           'phone': PHONE, 'phref': PHONE_HREF}
        out.append((slug, page(slug, title, desc, body,
                               '<a href="moduli-dlya-prozhivaniya.html">Все модули</a> ' + others +
                               ' <a href="karkasnye-doma.html">Каркасные дома</a>')))
    return out


# ---------- доставка по регионам ----------
REGIONS = [('Москва и Московская область', 50), ('Тверская область', 170), ('Ярославская область', 265),
           ('Владимирская область', 185), ('Калужская область', 190), ('Тульская область', 185),
           ('Рязанская область', 200), ('Смоленская область', 370), ('Брянская область', 380),
           ('Орловская область', 360), ('Курская область', 460), ('Белгородская область', 620),
           ('Липецкая область', 430), ('Тамбовская область', 460), ('Воронежская область', 520),
           ('Костромская область', 340), ('Ивановская область', 290)]


def delivery_page(cities=None):
    slug = 'dostavka-i-sborka.html'
    title = 'Доставка и сборка каркасных домов по ЦФО — расчёт по километрам | Контур Дома'
    desc = ('Строим и доставляем по всему Центральному федеральному округу. Сборка на участке входит '
            'в цену, доставка — 300 ₽ за километр от производства. Таблица по областям.')
    if cities:
        rows = ''.join('<tr><td><a href="karkasnyy-dom-%s.html">%s</a></td><td>%d км</td><td>%s</td></tr>'
                       % (c['slug'], esc(c['region']), c['km'], deliv_txt(c['km'])) for c in cities)
    else:
        rows = ''.join('<tr><td>%s</td><td>≈ %d км</td><td>≈ %s</td></tr>'
                       % (esc(n), km, rub(km * 300)) for n, km in REGIONS)
    body = PAGE_DELIVERY % {'rows': rows, 'phone': PHONE, 'phref': PHONE_HREF}
    nav = ('<a href="karkasnye-doma.html">Каркасные дома</a> <a href="moduli-dlya-prozhivaniya.html">Модули</a> '
           '<a href="tseny.html">Цены</a> <a href="voprosy.html">Вопросы</a>')
    return slug, page(slug, title, desc, body, nav)


# ---------- страницы городов ----------
FREE_KM, RATE = 0, 300           # 300 ₽ за каждый километр с самого начала, как в калькуляторе


def deliv(km):
    return int(round(max(0, km - FREE_KM) * RATE, -2))


def deliv_txt(km):
    d = deliv(km)
    return rub(d) if d else 'бесплатно'


def acc(n):
    """Куда: в Калугу, в Тулу, в Тверь, в Иваново."""
    return n[:-1] + 'у' if n.endswith('а') else n


def rgen(region):
    """Тверская область → Тверской области."""
    return region.replace('ская область', 'ской области').replace('цкая область', 'цкой области')


def hours_txt(h):
    """2,5 часа · 5 часов · 1 час — половинами, как говорят про дорогу."""
    v = max(0.5, round(h * 2) / 2)
    if v != int(v):
        return '%s часа' % fmt(v)
    n = int(v)
    return '%d %s' % (n, 'час' if n % 10 == 1 and n % 100 != 11 else
                      'часа' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'часов')


CLIM = {
    'north': ('Зима здесь длиннее и холоднее, чем в Подмосковье.',
              'Для круглогодичной жизни советуем утеплитель 200 мм: дом держит тепло в сильные морозы и меньше тратит на отопление. '
              '150 мм — минимум для зимы, 100 мм — только для летней дачи.'),
    'center': ('Климат средней полосы, как в Подмосковье.',
               'Для круглогодичной жизни хватает утеплителя 150 мм, 200 мм — с запасом на морозные зимы и экономию на отоплении. '
               '100 мм — для летней дачи.'),
    'south': ('Зима здесь мягче, чем в Подмосковье.',
              'Для круглогодичной жизни достаточно утеплителя 150 мм, 200 мм берут, чтобы меньше платить за отопление. '
              '100 мм подходит для дома, в который приезжают с весны до осени.'),
}

CITY_SIZES = ['6x5', '6x6', '6x8', '8x8', '10x10']


def city_rows(c, houses):
    """Для каждого размера — самый доступный проект, цена с доставкой именно в этот город."""
    d = deliv(c['km'])
    rows, lo = [], None
    for sid in CITY_SIZES:
        best = None
        for h in houses:
            for s in h['sizes']:
                if s['id'] == sid and (best is None or s['price'] < best[1]['price']):
                    best = (h, s)
        if not best:
            continue
        h, s = best
        lo = s['price'] if lo is None else min(lo, s['price'])
        rows.append('<tr><td><a href="dom-%s.html">«%s» %s×%s м</a><br><small>%s м²</small></td>'
                    '<td>%s</td><td>%s</td><td><b>%s</b></td></tr>'
                    % (h['id'], esc(h['name']), fmt(s['w']), fmt(s['d']), fmt(s['area']),
                       rub(s['price']), rub(s['warm']), rub(s['warm'] + d)))
    return ''.join(rows), lo


def city_pages(cities, houses, mods):
    out = []
    mod_lo = min(s['price'] for m in mods for s in m['sizes'])
    nav_all = ' '.join('<a href="karkasnyy-dom-%s.html">%s</a>' % (x['slug'], esc(x['name'])) for x in cities)
    for c in cities:
        slug = 'karkasnyy-dom-%s.html' % c['slug']
        msk = c['slug'] == 'moskva'
        where = 'в Москве и Подмосковье' if msk else 'в %s' % c['prep']
        area = 'Москве и Московской области' if msk else '%s и %s' % (c['prep'], rgen(c['region']))
        to = 'по Москве и области' if msk else 'в ' + acc(c['name'])
        d, dt = deliv(c['km']), deliv_txt(c['km'])
        rows, lo = city_rows(c, houses)
        clim_head, clim_txt = CLIM[c['clim']]
        if msk:
            road = ('Доставка считается как 300 ₽ за каждый километр от производства: по Москве это около %s, '
                    'до участка в 120 км по области — %s. Точную сумму калькулятор посчитает по адресу участка.'
                    % (dt, rub(deliv(120))))
        else:
            road = ('От нашего производства до %s — %d км по дорогам, около %s на машине. '
                    'Доставка материалов считается как 300 ₽ за каждый километр: до %s это %s. '
                    'Если участок дальше или ближе центра города, сумма пересчитается по точному адресу.'
                    % (c['gen'], c['km'], hours_txt(c['hours']), c['gen'], dt))
        qa = [
            ('Сколько стоит доставка %s?' % to,
             ('300 ₽ за каждый километр от производства: по Москве около %s, по области — по расстоянию до участка. Точную сумму называем по адресу.' % dt if msk else
              'До %s %d км по дорогам, доставка материалов — %s. Считаем 300 ₽ за каждый километр, '
              'точную сумму называем по адресу участка.' % (c['gen'], c['km'], dt))),
            ('Сколько времени займёт стройка %s?' % where,
             'Сборка на участке занимает от 3 до 14 дней в зависимости от размера дома, модуль собирается за 1–3 дня. '
             'Срок от расстояния не зависит: %s дом собирается так же быстро, как под Москвой.' % where),
            ('Какое утепление нужно для %s?' % ('Подмосковья' if msk else rgen(c['region'])),
             clim_head + ' ' + clim_txt),
            ('Когда нужно платить?',
             'Частями: аванс 10–30% в первый день работ, остальное — после сборки и приёмки дома. Порядок оплаты прописан в договоре.'),
        ]
        faq = ''.join('<h3>%s</h3>\n<p>%s</p>\n' % (esc(q), esc(a)) for q, a in qa)
        ld = ('<script type="application/ld+json">\n{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[\n %s\n]}\n</script>'
              % ',\n '.join('{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}' % (esc(q), esc(a)) for q, a in qa))
        facts = ''.join('<div><b>%s</b><span>%s</span></div>' % (a, b) for a, b in (
            ('%d км' % c['km'], 'от производства по дорогам') if not msk else ('300 ₽', 'за километр доставки'),
            (hours_txt(c['hours']), 'в пути на машине') if not msk else ('3–14 дней', 'сборка на участке'),
            (dt, 'доставка материалов') if not msk else ('3 года', 'гарантия'),
            ('10–30%', 'аванс, остальное после приёмки')))
        body = f"""<p class="crumbs"><a href="/">Главная</a> / <a href="dostavka-i-sborka.html">Доставка</a> / {esc('Москва и область' if msk else c['name'])}</p>
<h1>Каркасный дом под ключ {esc(where)}</h1>
<p class="lead">Строим каркасные дома и утеплённые модули в {esc(area)}. Сборка на вашем участке входит в цену,
аванс 10–30%, остальное — после приёмки готового дома, гарантия 3 года.</p>
<div class="facts">{facts}</div>
<h2>Доставка {esc(to)}</h2>
<p>{esc(road)}</p>
<h2>Сколько стоит дом с доставкой {esc('по Москве' if msk else 'в ' + acc(c['name']))}</h2>
<p>Самый доступный проект в каждом размере. В последней колонке тёплый контур вместе с доставкой {esc('по Москве' if msk else 'до ' + c['gen'])}:
утеплитель, пароизоляция, вагонка внутри и пол под чистовое покрытие.</p>
<div class="tw"><table>
<thead><tr><th>Дом</th><th>Холодный контур</th><th>Тёплый контур</th><th>Тёплый + доставка</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p>Утеплённый модуль для жизни или гостей — от {rub(mod_lo)}, с доставкой {esc('по Москве' if msk else 'в ' + acc(c['name']))} от {rub(mod_lo + d)}.
Точную смету со своими окнами, отделкой и планировкой можно собрать в <a href="/">калькуляторе</a> — адрес участка
вписывается там же, доставка посчитается по дорогам.</p>
<h2>Утепление под климат</h2>
<p>{esc(clim_head)} {esc(clim_txt)} Подробнее — в статье <a href="uteplenie-karkasnogo-doma.html">«Сколько миллиметров утеплителя нужно»</a>.</p>
<h2>Как проходит стройка</h2>
<ul>
  <li><b>Расчёт.</b> Собираете дом в калькуляторе или присылаете свой план — цена фиксируется в договоре.</li>
  <li><b>Выезд инженера.</b> Смотрим грунт, рельеф и подъезд к участку.</li>
  <li><b>Основание.</b> Бетонные блоки, винтовые сваи или утеплённая плита — по грунту.</li>
  <li><b>Сборка.</b> 3–14 дней для дома, 1–3 дня для модуля. Срок от расстояния не зависит.</li>
  <li><b>Приёмка и оплата.</b> Осматриваете дом, подписываете акт — и только после этого платите.</li>
</ul>
<h2>Частые вопросы</h2>
{faq}
<p><a class="btn" href="/#/catalog">Выбрать дом и посчитать</a>
<a class="btn ghost" href="tel:{PHONE_HREF}">Позвонить {PHONE}</a></p>
<h2>Где ещё строим</h2>"""
        title = 'Каркасный дом под ключ %s — цены с доставкой%s' % (where, BRAND)
        desc = ('Каркасные дома и модули %s: дом от %s, модуль от %s, %s. Сборка за 3–14 дней, основная оплата после приёмки.'
                % (where, rub(lo), rub(mod_lo),
                   'доставка 300 ₽ за км' if msk else 'доставка %s (%d км)' % (dt, c['km'])))
        out.append((slug, page(slug, title, desc, body, nav_all +
                               ' <a href="dostavka-i-sborka.html">Доставка</a> <a href="karkasnye-doma.html">Все дома</a>', ld)))
    return out


# ---------- вопросы и ответы с разметкой FAQPage ----------
QA = [
 ('Можно ли жить в каркасном доме зимой?',
  'Да, если выбрать утепление от 150 мм. В базовую цену входит плиточно-базальтовый утеплитель 100 мм — это дача на тёплый сезон. Для зимы в средней полосе берут 200 мм, для Урала и Сибири — 250 мм с перекрёстным каркасом.'),
 ('Строите ли вы зимой?',
  'Да. Каркасная технология не требует мокрых процессов, а винтовые сваи завинчиваются в мёрзлый грунт. Зимой у бригад свободнее график, поэтому дом часто собирают быстрее, чем летом.'),
 ('Можно ли изменить планировку и размер?',
  'Да. Внутренние перегородки переставляются без изменения цены каркаса, а размер задаётся свой с шагом 0,5 метра — площадь, комплект окон и смета пересчитываются автоматически.'),
 ('Когда нужно платить?',
  'Оплата частями: в первый день работ — аванс от 10 до 30% стоимости, остальное — после того как вы примете готовый дом и подпишете акт.'),
 ('Сколько стоит каркасный дом под ключ?',
  'От {MIN_HOUSE} за компактный дом в холодном контуре. Тот же дом под ключ обходится примерно вдвое дороже: в цену входят электрика, вода, сантехника, освещение и чистовая отделка. Полный прайс есть на странице цен.'),
 ('Нужно ли разрешение на строительство?',
  'Для жилого дома до 20 метров по каждой стороне разрешение не требуется — достаточно уведомления о планируемом строительстве. Поможем его оформить.'),
 ('Какая гарантия?',
  'Три года на каркас, отделку и инженерию. Гарантия прописывается в договоре.'),
 ('Входит ли сборка в стоимость?',
  'Да. И дом, и модуль собирает наша бригада на вашем участке — сборка входит в цену. Отдельно считается только доставка: 300 ₽ за каждый километр от производства.'),
 ('Куда вы доставляете?',
  'По всему Центральному федеральному округу: Москва и область, Тверская, Ярославская, Владимирская, Калужская, Тульская, Рязанская, Смоленская, Брянская, Орловская, Курская, Белгородская, Липецкая, Тамбовская, Воронежская, Костромская и Ивановская области.'),
 ('Подходит ли дом под ипотеку?',
  'Да, каркасные дома кредитуют банки, работающие с ИЖС по договору подряда. Поможем собрать документы для заявки.'),
 ('Чем каркасный дом лучше бруса?',
  'Он дешевле при той же тёплой стене, не даёт усадки, собирается за считанные дни и строится круглый год. Брус выигрывает видом стены изнутри — но это повторяется имитацией бруса или блок-хаусом.'),
 ('Есть ли скидки?',
  'Промокоды на скидку от 5 до 20% выдаются по льготам: ветеранам, людям с инвалидностью, пенсионерам и многодетным семьям. В других случаях условия обсуждаем индивидуально.'),
]


def faq_page(houses=None):
    slug = 'voprosy.html'
    title = 'Вопросы о каркасных домах — отвечаем честно | Контур Дома'
    desc = ('Можно ли жить зимой, сколько стоит под ключ, нужно ли разрешение, когда платить, '
            'куда доставляем — ответы на частые вопросы о каркасных домах и модулях.')
    mh = rub(min_house(houses)) if houses else ''
    qa = [(q, a.replace('{MIN_HOUSE}', mh)) for q, a in QA]
    items = ''.join('<h3>%s</h3>\n<p>%s</p>\n' % (esc(q), esc(a)) for q, a in qa)
    ld_items = ',\n '.join(
        '{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}' % (esc(q), esc(a))
        for q, a in qa)
    ld = ('<script type="application/ld+json">\n{"@context":"https://schema.org","@type":"FAQPage",'
          '"mainEntity":[\n %s\n]}\n</script>' % ld_items)
    body = PAGE_FAQ % {'items': items, 'ld': ld, 'phone': PHONE, 'phref': PHONE_HREF}
    nav = ('<a href="karkasnye-doma.html">Каркасные дома</a> <a href="moduli-dlya-prozhivaniya.html">Модули</a> '
           '<a href="tseny.html">Цены</a> <a href="dostavka-i-sborka.html">Доставка</a> '
           '<a href="o-kompanii.html">О компании</a>')
    return slug, page(slug, title, desc, body, nav)


# ---------- статьи под длинный хвост ----------
def article_pages(houses):
    lo = rub(min_house(houses))
    nav = ('<a href="karkasnye-doma.html">Каркасные дома</a> <a href="moduli-dlya-prozhivaniya.html">Модули</a> '
           '<a href="tseny.html">Цены</a> <a href="dostavka-i-sborka.html">Доставка</a> '
           '<a href="voprosy.html">Вопросы</a>')
    arts = [
      ('uteplenie-karkasnogo-doma.html',
       'Утепление каркасного дома: 100, 150, 200 или 250 мм | Контур Дома',
       'Сколько миллиметров утеплителя нужно каркасному дому: 100 мм для дачи, 150 для круглогодичной жизни, '
       '200–250 для холодных регионов. Как от этого меняются каркас и цена.',
       ART_INS % {'phref': PHONE_HREF}),
      ('fundament-dlya-karkasnogo-doma.html',
       'Фундамент для каркасного дома: блоки, винтовые сваи или УШП | Контур Дома',
       'Какой фундамент нужен каркасному дому: бетонные блоки, винтовые сваи или утеплённая шведская плита. '
       'Как выбрать по грунту и сколько это стоит.',
       ART_FOUND % {'phref': PHONE_HREF}),
      ('karkasnyy-dom-zimoy.html',
       'Можно ли строить каркасный дом зимой — сроки и особенности | Контур Дома',
       'Каркасный дом строится зимой так же, как летом: нет мокрых процессов, сваи завинчиваются в мёрзлый '
       'грунт. Что реально меняется и почему зимой бригады свободнее.',
       ART_WINTER % {'phref': PHONE_HREF}),
      ('skolko-stoit-karkasnyy-dom.html',
       'Сколько стоит каркасный дом под ключ — из чего складывается цена',
       'Каркасный дом под ключ: от %s за холодный контур. Что входит в каждую комплектацию, '
       'на чём чаще всего вырастает смета и как этого избежать.' % lo,
       ART_PRICE % {'lo': lo, 'phref': PHONE_HREF}),
    ]
    return [(s, page(s, ti, de, bo, nav)) for s, ti, de, bo in arts]


def err404_page():
    slug = '404.html'
    body = """<h1 style="margin-top:60px">Такой страницы нет</h1>
<p class="lead">Возможно, адрес набран с опечаткой или страница переехала. Вот что есть на сайте:</p>
<div class="nav-all" style="margin:26px 0 40px">
  <a href="/">Калькулятор и каталог</a>
  <a href="karkasnye-doma.html">Каркасные дома</a>
  <a href="moduli-dlya-prozhivaniya.html">Модули</a>
  <a href="tseny.html">Цены</a>
  <a href="nashi-proekty.html">Наши проекты</a>
  <a href="dostavka-i-sborka.html">Доставка</a>
  <a href="voprosy.html">Вопросы</a>
  <a href="o-kompanii.html">О компании</a>
</div>
<p><a class="btn" href="/">На главную</a>
<a class="btn ghost" href="tel:%(phref)s">Позвонить %(phone)s</a></p>""" % {'phref': PHONE_HREF, 'phone': PHONE}
    return slug, page(slug, 'Страница не найдена | Контур Дома',
                      'Такой страницы на сайте нет. Каталог каркасных домов, модули, цены и калькулятор — по ссылкам ниже.',
                      body, '')


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'seo.json'
    dst = sys.argv[2] if len(sys.argv) > 2 else '.'
    d = json.load(io.open(src, encoding='utf-8'))
    cpath = os.path.join(os.path.dirname(os.path.abspath(src)), 'cities.json')
    cities = json.load(io.open(cpath, encoding='utf-8')) if os.path.exists(cpath) else []
    pages = [houses_hub(d['houses']), mods_page(d['mods']), prices_page(d['houses'], d['mods']),
             projects_page(d['prj']), about_page(), delivery_page(cities), faq_page(d['houses']), err404_page()]
    pages += [house_page(h, d['houses']) for h in d['houses']]
    pages += size_pages(d['houses'])
    pages += mod_pages(d['mods'])
    pages += article_pages(d['houses'])
    if cities:
        pages += city_pages(cities, d['houses'], d['mods'])
    for slug, html in pages:
        io.open(os.path.join(dst, slug), 'w', encoding='utf-8', newline='\n').write(html)
    today = datetime.date.today().isoformat()
    urls = ['<url><loc>%s/</loc><changefreq>weekly</changefreq><priority>1.0</priority><lastmod>%s</lastmod></url>' % (DOMAIN, today)]
    for slug, _ in pages:
        if slug == '404.html':
            continue
        pr = '0.9' if slug.startswith(('karkasnye', 'moduli-dlya', 'tseny', 'karkasnyy-dom')) else '0.8'
        urls.append('<url><loc>%s/%s</loc><changefreq>monthly</changefreq><priority>%s</priority><lastmod>%s</lastmod></url>' % (DOMAIN, slug, pr, today))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  ' + \
         '\n  '.join(urls) + '\n</urlset>\n'
    io.open(os.path.join(dst, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n').write(sm)
    print('готово: %d страниц + sitemap.xml' % len(pages))
    for slug, _ in pages:
        print('  ', slug)


main()
