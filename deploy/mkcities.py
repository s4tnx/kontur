# -*- coding: utf-8 -*-
"""Расстояния по дорогам от производства до городов ЦФО — для страниц «Каркасный дом в …».

Запускается редко, только когда меняется список городов или точка отгрузки:
   python deploy/mkcities.py deploy/cities.json
Считает маршрут тем же сервисом, что и калькулятор на сайте (OSRM по картам OpenStreetMap),
и сохраняет километры и время в пути в cities.json. Генератор страниц mkpages.py
берёт готовые цифры оттуда и в интернет не ходит.

Координаты точки отгрузки — те же, что GEO_FROM в index.html. На сайте они не публикуются:
на страницы попадают только километры и часы.
"""
import io, json, sys, time, urllib.request, urllib.parse

GEO_FROM = (37.4227, 55.6206)   # долгота, широта — как в index.html

# slug, город в именительном, в предложном («в Твери»), в родительном («из Твери»), область,
# климат: south — юг ЦФО, center — середина, north — север и восток ЦФО
CITIES = [
    ('moskva',    'Москва',    'Москве',    'Москвы',    'Москва и Московская область', 'center'),
    ('tver',      'Тверь',     'Твери',     'Твери',     'Тверская область',            'north'),
    ('kaluga',    'Калуга',    'Калуге',    'Калуги',    'Калужская область',           'center'),
    ('tula',      'Тула',      'Туле',      'Тулы',      'Тульская область',            'center'),
    ('ryazan',    'Рязань',    'Рязани',    'Рязани',    'Рязанская область',           'center'),
    ('vladimir',  'Владимир',  'Владимире', 'Владимира', 'Владимирская область',        'center'),
    ('yaroslavl', 'Ярославль', 'Ярославле', 'Ярославля', 'Ярославская область',         'north'),
    ('smolensk',  'Смоленск',  'Смоленске', 'Смоленска', 'Смоленская область',          'center'),
    ('kostroma',  'Кострома',  'Костроме',  'Костромы',  'Костромская область',         'north'),
    ('ivanovo',   'Иваново',   'Иванове',   'Иванова',   'Ивановская область',          'north'),
    ('bryansk',   'Брянск',    'Брянске',   'Брянска',   'Брянская область',            'center'),
    ('orel',      'Орёл',      'Орле',      'Орла',      'Орловская область',           'center'),
    ('kursk',     'Курск',     'Курске',    'Курска',    'Курская область',             'south'),
    ('belgorod',  'Белгород',  'Белгороде', 'Белгорода', 'Белгородская область',        'south'),
    ('lipetsk',   'Липецк',    'Липецке',   'Липецка',   'Липецкая область',            'center'),
    ('tambov',    'Тамбов',    'Тамбове',   'Тамбова',   'Тамбовская область',          'center'),
    ('voronezh',  'Воронеж',   'Воронеже',  'Воронежа',  'Воронежская область',         'south'),
]

UA = {'User-Agent': 'konturhouse.ru city distances (site build script)'}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'deploy/cities.json'
    res = []
    for slug, name, prep, gen, region, clim in CITIES:
        q = urllib.parse.quote('%s, %s, Россия' % (name, region if slug != 'moskva' else 'Москва'))
        g = get('https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&accept-language=ru&countrycodes=ru&q=' + q)
        time.sleep(1.1)   # правила Nominatim: не чаще раза в секунду
        if not g:
            raise SystemExit('не нашёл город: ' + name)
        lon, lat = float(g[0]['lon']), float(g[0]['lat'])
        r = get('https://router.project-osrm.org/route/v1/driving/%s,%s;%s,%s?overview=false'
                % (GEO_FROM[0], GEO_FROM[1], lon, lat))
        time.sleep(0.5)
        if r.get('code') != 'Ok':
            raise SystemExit('не построил маршрут: ' + name)
        km = max(1, round(r['routes'][0]['distance'] / 1000))
        hrs = r['routes'][0]['duration'] / 3600
        res.append({'slug': slug, 'name': name, 'prep': prep, 'gen': gen, 'region': region,
                    'clim': clim, 'km': km, 'hours': round(hrs, 1)})
        print('%-10s %4d км  %.1f ч' % (name, km, hrs))
    io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
    print('сохранено:', out)


main()
