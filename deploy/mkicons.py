# -*- coding: utf-8 -*-
"""Иконки приложения для установки сайта на телефон.

Рисуем тот же домик, что в логотипе, белым по чёрному, и пакуем в PNG без сторонних библиотек.
   python deploy/mkicons.py .
Получаются icon-192.png, icon-512.png и icon-maskable-512.png
(у последней домик мельче: Android обрезает края под форму иконки).
"""
import zlib, struct, math, io, sys, os

BG = (12, 13, 14)        # --bg
FG = (255, 255, 255)     # белый

# контуры логотипа в системе координат 34×30
SEGS = [((2, 28), (2, 13)), ((2, 13), (17, 2)), ((17, 2), (32, 13)), ((32, 13), (32, 28)),
        ((8, 28), (8, 16)), ((8, 16), (17, 9.5)), ((17, 9.5), (26, 16)), ((26, 16), (26, 28)),
        ((14, 28), (14, 21)), ((14, 21), (20, 21)), ((20, 21), (20, 28))]


def draw(n, fill=0.78, stroke=1.6):
    """fill — какую долю холста занимает домик (для maskable меньше)."""
    s = n * fill / 34.0
    ox = (n - 34 * s) / 2
    oy = (n - 30 * s) / 2
    hw = stroke * s / 2
    segs = [((a[0] * s + ox, a[1] * s + oy), (b[0] * s + ox, b[1] * s + oy)) for a, b in SEGS]
    rows = []
    for y in range(n):
        row = bytearray([0])
        py = y + 0.5
        for x in range(n):
            px = x + 0.5
            best = 1e9
            for (ax, ay), (bx, by) in segs:
                dx, dy = bx - ax, by - ay
                L2 = dx * dx + dy * dy
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
                d = math.hypot(px - (ax + dx * t), py - (ay + dy * t))
                if d < best:
                    best = d
            cov = max(0.0, min(1.0, hw + 0.5 - best))
            row += bytes((round(BG[0] + (FG[0] - BG[0]) * cov),
                          round(BG[1] + (FG[1] - BG[1]) * cov),
                          round(BG[2] + (FG[2] - BG[2]) * cov), 255))
        rows.append(bytes(row))
    return b''.join(rows)


def png(n, raw):
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    for name, n, fill in [('icon-192.png', 192, 0.78), ('icon-512.png', 512, 0.78),
                          ('icon-maskable-512.png', 512, 0.56)]:
        data = png(n, draw(n, fill))
        io.open(os.path.join(out, name), 'wb').write(data)
        print('%-24s %d×%d, %d КБ' % (name, n, n, len(data) // 1024))


main()
