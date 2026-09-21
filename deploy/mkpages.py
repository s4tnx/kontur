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


def page(slug, title, desc, body, nav, extra_ld=''):
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
  Сборка на участке входит в цену, гарантия 3 года, оплата по окончании работ.</p>
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
<b>Тёплый контур</b> добавляет утепление каменной ватой, пароизоляцию, внутреннюю обшивку вагонкой и плиту OSB-3 15 мм на пол.
<b>Под ключ</b> — это ещё электрика, водоснабжение и канализация, сантехника, освещение, чистовая отделка и покраска фасада в два слоя.</p>
<div class="tw"><table>
<thead><tr><th>Размер</th><th>Площадь</th><th>Холодный контур</th><th>Тёплый контур</th><th>Под ключ</th></tr></thead>
<tbody>{sizes_rows}</tbody>
</table></div>
<p>Цены указаны за дом с доставкой до 50 км и сборкой. Любой размер можно изменить с шагом 0,5 м —
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
Оплата — по окончании работ, после того как вы примете дом.</p>
<p><a class="btn" href="/#/house/{h['id']}">Собрать дом «{esc(nm)}» в калькуляторе</a></p>
{ld}
"""
    nav = f'<a href="karkasnye-doma.html">Все дома</a> {others} <a href="moduli-dlya-prozhivaniya.html">Модули</a>'
    return slug, page(slug, title, desc, body, nav)


def houses_hub(houses):
    slug = 'karkasnye-doma.html'
    title = 'Каркасные дома под ключ — 8 проектов от 6×4 до 12×10 м | Контур Дома'
    desc = ('Каркасные дома под ключ: восемь проектов от %s. Свой размер с шагом 0,5 м, расчёт сметы онлайн, '
            'сборка на участке за 3–14 дней, гарантия 3 года, оплата по окончании работ.'
            % rub(min(h['price'] for h in houses)))
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
<p><b>Тёплый контур</b> — плюс каменная вата, пароизоляция, вагонка внутри и OSB-3 15 мм на полу.
В таком доме можно жить круглый год: с утеплением 150 мм зимой в Подмосковье, 200–250 мм — на Урале и в Сибири.</p>
<p><b>Под ключ</b> — заезжаете с вещами: электрика, вода, канализация, сантехника, освещение,
чистовая отделка и покраска фасада уже сделаны.</p>
<h2>Почему каркас</h2>
<p>Дом собирается на заводе и на участке за 3–14 дней, не требует усадки, не боится зимнего монтажа
и стоит дешевле бруса при той же тёплой стене. Каркас — сухая строганая доска 50×150 камерной сушки,
утеплитель — каменная вата, снаружи ветро-влагозащита и вентилируемый фасад.</p>
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
            'сборка и доставка до 50 км включены, оплата по окончании работ.'
            % (rub(min(h['price'] for h in houses)), rub(min(s['price'] for m in mods for s in m['sizes']))))
    rows = ''.join(
        f"<tr><td>«{esc(h['name'])}» {fmt(h['w'])} × {fmt(h['d'])} м</td><td>{fmt(h['area'])} м²</td>"
        f"<td>{rub(h['price'])}</td><td>{rub(h['warm'])}</td><td>{rub(h['key'])}</td></tr>" for h in houses)
    mrows = ''.join(
        f"<tr><td>Модуль «{esc(m['name'])}» {fmt(s['w'])} × {fmt(s['d'])} м</td><td>{fmt(s['area'])} м²</td><td colspan=\"3\">{rub(s['price'])}</td></tr>"
        for m in mods for s in m['sizes'])
    body = f"""<p class="crumbs"><a href="/">Главная</a> / Цены</p>
<h1>Цены на дома и модули</h1>
<p class="lead">Полный прайс на {datetime.date.today().year} год. Цены окончательные: сборка на участке
и доставка до 50 км уже внутри, оплата — после того как вы примете работу.</p>
<div class="tw"><table>
<thead><tr><th>Проект</th><th>Площадь</th><th>Холодный контур</th><th>Тёплый контур</th><th>Под ключ</th></tr></thead>
<tbody>{rows}{mrows}</tbody></table></div>
<h2>Из чего складывается цена</h2>
<p>Базовая цена — за дом в указанном размере и комплектации. Дальше смета меняется от ваших решений:
фундамент (блоки, винтовые сваи или УШП), толщина утеплителя, фасад, кровля, комплект окон,
перегородки и двери, терраса, крыльцо, инженерия. Калькулятор показывает каждую строку отдельно,
поэтому видно, на чём складывается сумма и где можно сэкономить.</p>
<p>Доставка считается от производства — 300 ₽ за километр сверх 50 км. Промокоды на скидку
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
            'сборка на участке, гарантия 3 года, оплата по окончании работ. Работаем по Центральному федеральному округу.')
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
  <li><b>Без предоплаты за работу.</b> Оплата — по окончании работ, когда вы приняли дом и подписали акт.</li>
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


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'seo.json'
    dst = sys.argv[2] if len(sys.argv) > 2 else '.'
    d = json.load(io.open(src, encoding='utf-8'))
    pages = [houses_hub(d['houses']), mods_page(d['mods']), prices_page(d['houses'], d['mods']),
             projects_page(d['prj']), about_page()]
    pages += [house_page(h, d['houses']) for h in d['houses']]
    for slug, html in pages:
        io.open(os.path.join(dst, slug), 'w', encoding='utf-8', newline='\n').write(html)
    today = datetime.date.today().isoformat()
    urls = ['<url><loc>%s/</loc><changefreq>weekly</changefreq><priority>1.0</priority><lastmod>%s</lastmod></url>' % (DOMAIN, today)]
    for slug, _ in pages:
        pr = '0.9' if slug.startswith(('karkasnye', 'moduli', 'tseny')) else '0.8'
        urls.append('<url><loc>%s/%s</loc><changefreq>monthly</changefreq><priority>%s</priority><lastmod>%s</lastmod></url>' % (DOMAIN, slug, pr, today))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  ' + \
         '\n  '.join(urls) + '\n</urlset>\n'
    io.open(os.path.join(dst, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n').write(sm)
    print('готово: %d страниц + sitemap.xml' % len(pages))
    for slug, _ in pages:
        print('  ', slug)


main()
