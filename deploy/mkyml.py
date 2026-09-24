# -*- coding: utf-8 -*-
"""Каталог товаров и услуг для Яндекс Бизнеса (формат YML).

Зачем: в карточке организации на Яндекс Картах есть раздел «Товары и услуги».
Его можно заполнить руками, а можно загрузить файлом — этот скрипт собирает файл
из тех же данных, что и сайт, чтобы цены не расходились.

Запуск:  python deploy/mkyml.py deploy/seo.json .
Получается yandex-business.yml — его загружают в Яндекс Бизнесе:
О компании → Товары и услуги → Загрузить XLS/YML.
"""
import io, json, sys, os, datetime

DOMAIN = 'https://konturhouse.ru'
SHOP = 'Контур Хаус'

CATS = [(1, 'Каркасные дома'), (2, 'Модули для проживания'), (3, 'Услуги')]

PKG = ('В цену входит сборка на вашем участке. Оплата частями: аванс 10–30%, остальное после приёмки, '
       'гарантия 3 года. Доставка по Центральному федеральному округу, 300 ₽ за километр.')

SERVICES = [
    ('svc-custom', 'Каркасный дом по вашим размерам', 650000, '#/custom', 'hero.jpg',
     'Дом любого габарита от 3×3 до 18×24 м: вы задаёте размеры и планировку, мы считаем смету '
     'и собираем на участке. Расчёт в калькуляторе на сайте занимает пять минут, цена фиксируется в договоре. '
     'Цена указана как ориентир за небольшой дом в холодном контуре. ' + PKG),
    ('svc-warm', 'Утепление дома до тёплого контура', 250000, 'uteplenie-karkasnogo-doma.html', 'h6x6.jpg',
     'Плиточно-базальтовый утеплитель 100–250 мм по кругу: пол, стены, потолок. Пароизоляция с проклейкой стыков, '
     'внутренняя обшивка вагонкой, плита OSB-3 15 мм на пол. Подходит и для домов, построенных раньше. '
     'Цена зависит от площади, указана от. ' + PKG),
    ('svc-bath', 'Баня каркасная под ключ', 420000, 'nashi-proekty.html', 'pr5.jpg',
     'Каркасная баня на участке: парная, моечная и комната отдыха. Печь, дымоход и обшивка липой или осиной. '
     'Собираем одной бригадой вместе с домом, так выходит дешевле, чем заказывать у разных подрядчиков. ' + PKG),
    ('svc-delivery', 'Доставка и сборка на участке', 300, 'dostavka-i-sborka.html', 'h6x8.jpg',
     'Доставка материалов по Центральному федеральному округу: 300 ₽ за километр от производства. '
     'Сборка на вашем участке входит в стоимость дома или модуля, отдельно платить за работу не нужно. '
     'Дом собирается за 3–14 дней в зависимости от размера, модуль — за 1–3 дня.'),
]


def plural(n, forms):
    """3 дня, 5 дней, 21 день."""
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11: return forms[0]
    if 2 <= n10 <= 4 and not (12 <= n100 <= 14): return forms[1]
    return forms[2]


def lc(s):
    return s[:1].lower() + s[1:] if s else s


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def offer(oid, cat, name, price, url, pic, desc):
    return ('    <offer id="%s" available="true">\n'
            '      <name>%s</name>\n'
            '      <url>%s/%s</url>\n'
            '      <price>%d</price>\n'
            '      <currencyId>RUR</currencyId>\n'
            '      <categoryId>%d</categoryId>\n'
            '      <picture>%s/%s</picture>\n'
            '      <vendor>%s</vendor>\n'
            '      <description>%s</description>\n'
            '    </offer>\n') % (esc(oid), esc(name), DOMAIN, esc(url), round(price), cat,
                                 DOMAIN, esc(pic), esc(SHOP), esc(desc))


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'deploy/seo.json'
    out = sys.argv[2] if len(sys.argv) > 2 else '.'
    d = json.load(io.open(src, encoding='utf-8'))
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    body = []

    for h in d['houses']:
        sizes = h.get('sizes') or []
        cheap = min(sizes, key=lambda s: s['price']) if sizes else {'w': h['w'], 'd': h['d'], 'area': h['area'], 'price': h['price']}
        floors = 'одноэтажный' if h['floors'] == 1 else ('с мансардой' if h['floors'] == 1.5 else 'двухэтажный')
        desc = ('%s Дом %s, %s м²: %d %s, санузел. %s Собирается за %d %s. '
                'Цена указана за холодный контур в размере %s×%s м, тёплый контур и «под ключ» считаются в калькуляторе на сайте. %s') % (
            h['lead'].rstrip('.') + '.', floors, str(cheap['area']).replace('.', ','), h['beds'],
            'спальня' if h['beds'] == 1 else 'спальни', ('Фундамент: %s.' % lc(h['base'])) if h.get('base') else '',
            h['days'], plural(h['days'], ['день', 'дня', 'дней']),
            str(cheap['w']).replace('.', ','), str(cheap['d']).replace('.', ','), PKG)
        name = 'Каркасный дом «%s» %s×%s м, %s м²' % (
            h['name'], str(cheap['w']).replace('.', ','), str(cheap['d']).replace('.', ','),
            str(cheap['area']).replace('.', ','))
        body.append(offer('dom-' + h['id'], 1, name, cheap['price'], 'dom-%s.html' % h['id'], h['photo'], desc))

    for m in d['mods']:
        sizes = m.get('sizes') or []
        if not sizes:
            continue
        cheap = min(sizes, key=lambda s: s['price'])
        big = max(sizes, key=lambda s: s['price'])
        desc = ('%s. Модуль %s×%s м, %s м². Каркас из сухой строганой доски, утепление 50–150 мм, '
                'вагонка внутри, окна и утеплённая дверь. Собираем прямо на вашем участке за 1–3 дня. '
                'Размеры от %s×%s до %s×%s м, цена от %s до %s ₽. %s') % (
            m['txt'], str(cheap['w']).replace('.', ','), str(cheap['d']).replace('.', ','),
            str(cheap['area']).replace('.', ','),
            str(cheap['w']).replace('.', ','), str(cheap['d']).replace('.', ','),
            str(big['w']).replace('.', ','), str(big['d']).replace('.', ','),
            format(cheap['price'], ',d').replace(',', ' '), format(big['price'], ',d').replace(',', ' '), PKG)
        name = 'Модуль для проживания «%s» %s×%s м' % (
            m['name'], str(cheap['w']).replace('.', ','), str(cheap['d']).replace('.', ','))
        body.append(offer('modul-' + m['id'], 2, name, cheap['price'], 'modul-%s.html' % m['id'], m['photo'], desc))

    for oid, name, price, url, pic, desc in SERVICES:
        body.append(offer(oid, 3, name, price, url, pic, desc))

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<!DOCTYPE yml_catalog SYSTEM "shops.dtd">\n'
           '<yml_catalog date="%s">\n'
           '  <shop>\n'
           '    <name>%s</name>\n'
           '    <company>%s</company>\n'
           '    <url>%s/</url>\n'
           '    <currencies><currency id="RUR" rate="1"/></currencies>\n'
           '    <categories>\n%s    </categories>\n'
           '    <offers>\n%s    </offers>\n'
           '  </shop>\n'
           '</yml_catalog>\n') % (
        now, esc(SHOP), esc(SHOP), DOMAIN,
        ''.join('      <category id="%d">%s</category>\n' % (i, esc(n)) for i, n in CATS),
        ''.join(body))

    path = os.path.join(out, 'yandex-business.yml')
    io.open(path, 'w', encoding='utf-8', newline=chr(10)).write(xml)
    print('%s: %d предложений, %d КБ' % (path, len(body), len(xml.encode('utf-8')) // 1024))


main()
