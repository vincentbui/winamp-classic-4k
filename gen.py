#!/usr/bin/env python3
"""Classic HD - generator for a Winamp freeform (.wal) skin that recreates the
Classic 275x116 layout with natively drawn hi-res artwork.
usage: gen.py <scale> <outdir> [default|purple]"""
import os, sys, zipfile, shutil
from PIL import Image, ImageDraw, ImageFont

S = float(sys.argv[1])
S = int(S) if S == int(S) else S   # 2, 3, 4 ... or fractional like 1.5
OUT = sys.argv[2]
THEME = sys.argv[3] if len(sys.argv) > 3 else "default"
if THEME not in ("default", "purple"):
    sys.exit(f"error: unknown theme {THEME!r} (expected 'default' or 'purple')")
AA = 4
K = S * AA
NAME = f"Classic HD x{S}" if THEME == "default" else f"Classic HD Purple x{S}"
ROOT = os.path.join(OUT, NAME)
IMG = os.path.join(ROOT, "img")
XML = os.path.join(ROOT, "xml")
shutil.rmtree(ROOT, ignore_errors=True)
os.makedirs(IMG); os.makedirs(XML)

FONT = None
for p in ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    if os.path.exists(p):
        FONT = p; break
assert FONT
_fc = {}
def font(size):
    px = max(4, round(size * K))
    if px not in _fc: _fc[px] = ImageFont.truetype(FONT, px)
    return _fc[px]

# ---------------------------------------------------------------- palette
BODY1, BODY2 = (66, 68, 90), (30, 31, 46)
TB1, TB2 = (46, 48, 68), (22, 23, 35)
HI, LO, EDGE = (136, 140, 168), (9, 9, 16), (4, 4, 8)
GOLD, GOLD_D = (222, 178, 96), (96, 70, 30)
BTN1, BTN2 = (206, 212, 226), (118, 126, 150)
BTNH1, BTNH2 = (232, 237, 250), (146, 154, 180)
BTNP1, BTNP2 = (104, 112, 136), (150, 157, 178)
BHI, BLO = (246, 249, 255), (54, 58, 78)
INK = (18, 21, 36)
LABEL = (168, 174, 198)
GREEN = (0, 232, 0)
BLACK = (0, 0, 0)
# chrome colours that are not part of the main bevel palette
SIDE = (44, 46, 62)          # window frame sides / list column background
WINBG = (38, 40, 56)         # wasabi window background
TTEXT = (208, 213, 230)      # title / list text
BLO_P = (196, 202, 220)      # pressed-button low edge
LEDBG = (20, 24, 34)         # led bezel
CHLBL = (96, 104, 132)       # display channel letters (OAIDV)
TICK = (30, 34, 50)          # seek ticks
DIVID = (30, 34, 48)         # display divider
DIM = (74, 82, 108)          # inactive mono/stereo indicator
DIMTXT = (110, 116, 140)     # wasabi.button.dimmedText
SELINACT = (40, 44, 96)      # inactive list selection
if THEME == "purple":
    # Only the chrome changes: body, title bars, frames, bevels and menu/window
    # colours become the violet-grey of the Classic base skin. Buttons, slider
    # handles, LEDs and text keep the default colours.
    BODY1, BODY2 = (57, 57, 90), (20, 20, 31)   # sampled from the Classic base skin
    TB1, TB2 = (62, 60, 96), (38, 37, 60)
    HI = (117, 116, 139)
    SIDE = (41, 40, 64)
    WINBG = (56, 55, 87)          # menu / window background in the Classic screenshot
    CHLBL = (100, 98, 136)
    TICK = (34, 33, 54)
    DIVID = (34, 33, 52)
    DIM = (80, 78, 112)
    DIMTXT = (116, 114, 146)
    SELINACT = (52, 48, 104)
def rgb(t): return ",".join(map(str, t))

IMAGES = {}   # id -> (file, w, h) in classic units

class Cv:
    def __init__(s, w, h, bg=(0, 0, 0, 0)):
        s.w, s.h = w, h
        s.im = Image.new("RGBA", (round(w * K), round(h * K)), bg)
        s.d = ImageDraw.Draw(s.im)
    def rect(s, x, y, w, h, fill):
        if w <= 0 or h <= 0: return
        s.d.rectangle([round(x * K), round(y * K), round((x + w) * K) - 1, round((y + h) * K) - 1], fill=fill)
    def vgrad(s, x, y, w, h, c1, c2):
        x0, x1 = round(x * K), round((x + w) * K) - 1
        y0, y1 = round(y * K), round((y + h) * K)
        n = max(1, y1 - y0 - 1)
        for i, yy in enumerate(range(y0, y1)):
            t = i / n
            s.d.line([x0, yy, x1, yy], fill=tuple(round(a + (b - a) * t) for a, b in zip(c1, c2)))
    def hstops(s, x, y, w, h, stops):
        x0, x1 = round(x * K), round((x + w) * K)
        y0, y1 = round(y * K), round((y + h) * K) - 1
        n = max(1, x1 - x0 - 1)
        for i, xx in enumerate(range(x0, x1)):
            s.d.line([xx, y0, xx, y1], fill=mix(stops, i / n))
    def vstops(s, x, y, w, h, stops):
        x0, x1 = round(x * K), round((x + w) * K) - 1
        y0, y1 = round(y * K), round((y + h) * K)
        n = max(1, y1 - y0 - 1)
        for i, yy in enumerate(range(y0, y1)):
            s.d.line([x0, yy, x1, yy], fill=mix(stops, i / n))
    def poly(s, pts, fill):
        s.d.polygon([(px * K, py * K) for px, py in pts], fill=fill)
    def rrect(s, x, y, w, h, r, fill):
        s.d.rounded_rectangle([x * K, y * K, (x + w) * K - 1, (y + h) * K - 1], radius=r * K, fill=fill)
    def ellipse(s, x, y, w, h, fill):
        s.d.ellipse([x * K, y * K, (x + w) * K - 1, (y + h) * K - 1], fill=fill)
    def line(s, x0, y0, x1, y1, fill, t=1.0):
        s.d.line([x0 * K, y0 * K, x1 * K, y1 * K], fill=fill, width=max(1, round(t * K)))
    def text(s, x, y, txt, size, fill, anchor="lt"):
        s.d.text((x * K, y * K), txt, font=font(size), fill=fill, anchor=anchor)
    def tw(s, txt, size):
        return font(size).getlength(txt) / K
    def raised(s, x, y, w, h, c1, c2, hi=BHI, lo=BLO, t=0.75, border=EDGE, bt=0.5):
        if border:
            s.rect(x, y, w, h, border); x += bt; y += bt; w -= 2 * bt; h -= 2 * bt
        s.vgrad(x, y, w, h, c1, c2)
        s.rect(x, y, w, t, hi); s.rect(x, y, t, h, hi)
        s.rect(x, y + h - t, w, t, lo); s.rect(x + w - t, y, t, h, lo)
    def inset(s, x, y, w, h, fill=BLACK, t=0.75):
        s.rect(x - t, y - t, w + 2 * t, h + 2 * t, HI)
        s.rect(x - t, y - t, w + t, h + t, LO)
        s.rect(x, y, w, h, fill)
    def save(s, key, size=None):
        im = s.im.resize(size or (round(s.w * S), round(s.h * S)), Image.LANCZOS)
        fn = key + ".png"
        im.save(os.path.join(IMG, fn), optimize=True)
        IMAGES[key] = (fn, s.w, s.h, im)
        return im

def mix(stops, t):
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            u = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * u) for a, b in zip(c0, c1))
    return stops[-1][1]

def n(v): return str(round(v * S))

# ---------------------------------------------------------------- shared art
def titlebar(c, x, w, title=None, h=14, tx=None, stripes=True, size=7.6):
    """draws a title band; returns nothing"""
    c.vgrad(x, 0, w, h, TB1, TB2)
    c.rect(x, h - 0.6, w, 0.6, LO)
    ys = (h / 2 - 2.6, h / 2 + 1.2)
    spans = [(x + 3, x + w - 3)]
    if title:
        tw = c.tw(title, size)
        if tx is None: tx = x + (w - tw) / 2
        c.text(tx, h / 2 + 0.3, title, size, TTEXT, "lm")
        spans = [(x + 20, tx - 5), (tx + tw + 5, x + w - 36)]
    if stripes:
        for a, b in spans:
            if b - a < 2: continue
            for yy in ys:
                c.rect(a, yy, b - a, 0.9, GOLD)
                c.rect(a, yy + 0.9, b - a, 0.6, GOLD_D)

def outer_bevel(c, w, h, t=0.75):
    c.rect(0, 0, w, t, HI); c.rect(0, 0, t, h, HI)
    c.rect(0, h - t, w, t, LO); c.rect(w - t, 0, t, h, LO)

def button(key, w, h, draw_icon, states=("", ".h", ".p")):
    for st in states:
        c = Cv(w, h)
        if st == ".p":
            c.raised(0, 0, w, h, BTNP1, BTNP2, hi=BLO, lo=BLO_P); off = 0.6
        elif st == ".h":
            c.raised(0, 0, w, h, BTNH1, BTNH2); off = 0
        else:
            c.raised(0, 0, w, h, BTN1, BTN2); off = 0
        draw_icon(c, off)
        c.save(key + st)

def led_button(key, w, h, label, size, lx=3.2, lw=3.6, lh=4):
    for st, on in (("", False), (".h", False), (".p", False), (".on", True)):
        c = Cv(w, h)
        if st == ".p":
            c.raised(0, 0, w, h, BTNP1, BTNP2, hi=BLO, lo=BLO_P); off = 0.6
        elif st == ".h":
            c.raised(0, 0, w, h, BTNH1, BTNH2); off = 0
        else:
            c.raised(0, 0, w, h, BTN1, BTN2); off = 0
        lx = (w - (lw + 2 + c.tw(label, size))) / 2   # centre LED + label as one group
        ly = (h - lh) / 2 + off
        c.rect(lx - 0.5 + off, ly - 0.5, lw + 1, lh + 1, LEDBG)
        c.vgrad(lx + off, ly, lw, lh, (150, 255, 150) if on else (52, 78, 56), (0, 214, 0) if on else (26, 42, 30))
        c.text(lx + lw + 2 + off, h / 2 + 0.2 + off, label, size, INK, "lm")
        c.save(key + st)

def text_button(key, w, h, label, size=6.2):
    button(key, w, h, lambda c, o: c.text(w / 2 + o, h / 2 + 0.2 + o, label, size, INK, "mm"))

def small_button(key, kind):
    def ic(c, o):
        if kind == "menu":
            c.poly([(2.4 + o, 3.2 + o), (6.6 + o, 3.2 + o), (4.5 + o, 6.2 + o)], INK)
        elif kind == "min":
            c.rect(2.4 + o, 5.6 + o, 4.2, 1.2, INK)
        elif kind == "shade":
            c.rect(2.4 + o, 2.4 + o, 4.2, 1.2, INK)
        elif kind == "restore":
            c.rect(2.4 + o, 2.4 + o, 4.2, 4.2, INK); c.rect(3.2 + o, 3.6 + o, 2.6, 2.2, BTN2)
        elif kind == "close":
            c.line(2.6 + o, 2.6 + o, 6.4 + o, 6.4 + o, INK, 1.1); c.line(6.4 + o, 2.6 + o, 2.6 + o, 6.4 + o, INK, 1.1)
        elif kind == "prev":
            c.rect(2.2 + o, 2.6 + o, 1, 3.8, INK); c.poly([(6.8 + o, 2.4 + o), (6.8 + o, 6.6 + o), (3.4 + o, 4.5 + o)], INK)
        elif kind == "next":
            c.rect(5.8 + o, 2.6 + o, 1, 3.8, INK); c.poly([(2.2 + o, 2.4 + o), (2.2 + o, 6.6 + o), (5.6 + o, 4.5 + o)], INK)
        elif kind == "play":
            c.poly([(3 + o, 2.2 + o), (3 + o, 6.8 + o), (6.8 + o, 4.5 + o)], INK)
        elif kind == "pause":
            c.rect(2.6 + o, 2.6 + o, 1.4, 3.8, INK); c.rect(5 + o, 2.6 + o, 1.4, 3.8, INK)
        elif kind == "stop":
            c.rect(2.7 + o, 2.7 + o, 3.6, 3.6, INK)
        elif kind == "eject":
            c.poly([(2.4 + o, 5 + o), (6.6 + o, 5 + o), (4.5 + o, 2.2 + o)], INK); c.rect(2.4 + o, 5.7 + o, 4.2, 1, INK)
    button(key, 9, 9, ic)

def body_sheen(c, w=275, h=116):
    """Classic's body shading runs left-to-right, not top-to-bottom: dark at the
    left edge, brightest about 62% across, then falling off again to the right."""
    right = tuple(round(a + (b - a) * 0.6) for a, b in zip(BODY2, BODY1))
    c.hstops(0, 0, w, h, [(0, BODY2), (0.62, BODY1), (1, right)])

# ---------------------------------------------------------------- main window
def main_bg():
    c = Cv(275, 116)
    body_sheen(c)
    titlebar(c, 0, 275, "WINAMP")
    outer_bevel(c, 275, 116)
    # display panel
    c.inset(9, 22, 93, 43)
    for i, ch in enumerate("OAIDV"):
        c.text(14.5, 26.5 + i * 8.2, ch, 5.2, CHLBL, "mm")
    c.rect(19.6, 23, 0.5, 41, DIVID)
    # song title, kbps, khz
    c.inset(110, 22.5, 156, 14)
    c.inset(110, 41, 26, 10); c.text(138.5, 46.3, "kbps", 6.2, LABEL, "lm")
    c.inset(162, 41, 14, 10); c.text(178.5, 46.3, "kHz", 6.2, LABEL, "lm")
    # volume / balance grooves
    c.rrect(106.6, 59.6, 64.8, 6.3, 3.1, HI); c.rrect(106.6, 59.6, 64.4, 5.9, 3.0, LO); c.rrect(107, 60, 64, 5.5, 2.7, (10, 10, 16))
    c.rrect(179.6, 59.6, 35.8, 6.3, 3.1, HI); c.rrect(179.6, 59.6, 35.4, 5.9, 3.0, LO); c.rrect(180, 60, 35, 5.5, 2.7, (10, 10, 16))
    # seek groove
    c.inset(16, 73, 248, 8, (8, 8, 14))
    for i in range(0, 248, 4):
        c.rect(16.8 + i, 76.6, 1.6, 0.8, TICK)
    c.save("main.bg")

def shade_bg():
    c = Cv(275, 14)
    titlebar(c, 0, 275, None, stripes=False)
    c.vgrad(0, 0, 275, 14, TB1, TB2)
    outer_bevel(c, 275, 14)
    c.text(16, 7.2, "WINAMP", 7.4, TTEXT, "lm")
    c.inset(51, 2.6, 73, 8.8)
    c.inset(128, 2.6, 34, 8.8)
    c.save("shade.bg")

def transport():
    def prev(c, o):
        c.rect(6.4 + o, 5 + o, 1.8, 8, INK); c.poly([(16.6 + o, 4.6 + o), (16.6 + o, 13.4 + o), (9.2 + o, 9 + o)], INK)
    def play(c, o):
        c.poly([(8.2 + o, 4.2 + o), (8.2 + o, 13.8 + o), (16.4 + o, 9 + o)], INK)
    def pause(c, o):
        c.rect(7.4 + o, 5 + o, 3, 8, INK); c.rect(12.6 + o, 5 + o, 3, 8, INK)
    def stop(c, o):
        c.rect(7.5 + o, 5 + o, 8, 8, INK)
    def nxt(c, o):
        c.rect(14.8 + o, 5 + o, 1.8, 8, INK); c.poly([(6.4 + o, 4.6 + o), (6.4 + o, 13.4 + o), (13.8 + o, 9 + o)], INK)
    def eject(c, o):
        c.poly([(6 + o, 9.2 + o), (16 + o, 9.2 + o), (11 + o, 3.8 + o)], INK); c.rect(6 + o, 10.6 + o, 10, 2, INK)
    button("btn.prev", 23, 18, prev); button("btn.play", 23, 18, play); button("btn.pause", 23, 18, pause)
    button("btn.stop", 23, 18, stop); button("btn.next", 23, 18, nxt); button("btn.eject", 22, 16, eject)
    led_button("btn.shuffle", 44, 15, "SHUFFLE", 5.8)
    led_button("btn.repeat", 40, 15, "REPEAT", 5.8)
    led_button("btn.eq", 23, 12, "EQ", 6.2, lx=3)
    led_button("btn.pl", 23, 12, "PL", 6.2, lx=3)
    for k in ("menu", "min", "shade", "restore", "close", "prev", "next", "play", "pause", "stop", "eject"):
        small_button("sb." + k, k)
    # bolt / about
    for st, col in (("", GOLD), (".h", (255, 224, 150)), (".p", (160, 120, 60))):
        c = Cv(13, 15)
        c.poly([(9.6, 0.5), (2.2, 8.6), (6.0, 8.6), (3.6, 14.6), (10.9, 6.0), (7.3, 6.0)], col)   # pointed top, no flat cut
        c.save("btn.bolt" + st)

def thumbs():
    for st, (a, b) in (("", (BTN1, BTN2)), (".h", (BTNH1, BTNH2)), (".p", (BTNP2, BTNP1))):
        c = Cv(14, 11); c.raised(0, 0, 14, 11, a, b)
        [c.rect(xx, 2.8, 1.0, 5.4, INK) for xx in (4.1, 6.5, 8.9)]; c.save("thumb.vol" + st)
        # seek handle: gold with a recessed slot, like Classic's position bar
        g1, g2 = {"": ((236, 206, 128), (176, 136, 62)), ".h": ((250, 226, 156), (196, 156, 80)), ".p": ((168, 130, 60), (214, 182, 104))}[st]
        c = Cv(29, 10); c.raised(0, 0, 29, 10, g1, g2, hi=(255, 240, 186), lo=(92, 66, 26))
        c.rrect(4, 3, 21, 4, 1.2, (96, 70, 28)); c.rrect(4.6, 3.6, 19.8, 2.8, 0.8, g1 if st != ".p" else g2)
        c.save("thumb.seek" + st)
        c = Cv(11, 11); c.raised(0, 0, 11, 11, a, b)
        [c.rect(2.8, yy, 5.4, 1.0, INK) for yy in (2.9, 5.0, 7.1)]; c.save("thumb.eq" + st)

def status():
    c = Cv(9, 9); c.poly([(1.5, 0.6), (1.5, 8.4), (8, 4.5)], GREEN); c.save("st.play")
    c = Cv(9, 9); c.rect(1.4, 1, 2.4, 7, GREEN); c.rect(5.2, 1, 2.4, 7, GREEN); c.save("st.pause")
    c = Cv(9, 9); c.rect(1.5, 1.5, 6, 6, GREEN); c.save("st.stop")

SEG = {0: "abcdef", 1: "bc", 2: "abged", 3: "abgcd", 4: "fgbc", 5: "afgcd", 6: "afgedc", 7: "abc", 8: "abcdefg", 9: "abfgcd"}
CW, CH = 12, 13   # bitmap font cell (classic units)
# Original Winamp Classic digit shapes (numbers.bmp inside winamp.exe, 9x13 px, 1 px strokes),
# redrawn as vector squares so they stay sharp at any scale.
CLASSIC_DIGITS = [
    " #######         # #######  ####### #       # #######  ####### ########  #######  ####### ",
    "#       #        #        #        ##       ##        #                ##       ##       #",
    "#       #        #        #        ##       ##        #                ##       ##       #",
    "#       #        #        #        ##       ##        #                ##       ##       #",
    "#       #        #        #        ##       ##        #                ##       ##       #",
    "#       #        #        #        ##       ##        #                ##       ##       #",
    "#       #        # #######  #######  ######## ####### ########         # #######  ########",
    "#       #        ##                #        #        ##       #        ##       #        #",
    "#       #        ##                #        #        ##       #        ##       #        #",
    "#       #        ##                #        #        ##       #        ##       #        #",
    "#       #        ##                #        #        ##       #        ##       #        #",
    "#       #        ##                #        #        ##       #        ##       #        #",
    " #######         # #######  #######         # #######  #######         # #######  ####### ",
]
assert all(len(r) == 90 for r in CLASSIC_DIGITS), [len(r) for r in CLASSIC_DIGITS]
def numfont():
    c = Cv(CW * 31, CH * 3)
    for dgt in range(10):
        ox = dgt * CW + 1
        for py, row in enumerate(CLASSIC_DIGITS):
            for px, ch in enumerate(row[dgt * 9:dgt * 9 + 9]):
                if ch == "#": c.rect(ox + px, CH + py, 1, 1, GREEN)
    ox = 12 * CW                      # ':' (left aligned in its cell)
    c.rect(ox + 2, CH + 4, 1, 1, GREEN); c.rect(ox + 2, CH + 8, 1, 1, GREEN)
    c.rect(15 * CW + 2, CH + 6, 7, 1, GREEN)   # '-'
    c.save("numfont", (31 * int(n(CW)), 3 * int(n(CH))))   # exact cell grid, also at fractional scales

# ---------------------------------------------------------------- equalizer
EQX = [21] + [78 + 18 * i for i in range(10)]
EQL = ["PREAMP", "60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
def eq_bg():
    c = Cv(275, 116)
    body_sheen(c)
    titlebar(c, 0, 275, "WINAMP EQUALIZER")
    outer_bevel(c, 275, 116)
    for x, lab in zip(EQX, EQL):
        c.inset(x + 4.5, 38, 5, 63, (8, 8, 14))
        c.text(x + 7, 107.5, lab, 5.2, LABEL, "mm")
    for yy, lab in ((40.5, "+12 dB"), (69.5, "0 dB"), (98.5, "-12 dB")):
        c.text(70, yy, lab, 5.2, LABEL, "rm")
        c.rect(72, yy - 0.3, 3, 0.6, LABEL)
    c.save("eq.bg")

# ---------------------------------------------------------------- resizable frames
TOP_H, SIDE_W = 20, 10
TITLES = {}
def streak():
    c = Cv(8, TOP_H)
    for yy in (TOP_H / 2 - 2.6, TOP_H / 2 + 1.2):
        c.rect(0, yy, 8, 0.9, GOLD); c.rect(0, yy + 0.9, 8, 0.6, GOLD_D)
    c.save("streak")
def frame(prefix, title, hb):
    # title bar pieces are plain: the centred title + stripes are laid out at run time (see title_group)
    TITLES[prefix] = title
    c = Cv(8, TOP_H); c.vgrad(0, 0, 8, TOP_H, TB1, TB2); c.rect(0, TOP_H - 0.6, 8, 0.6, LO)
    c.rect(0, 0, 8, 0.75, HI); c.rect(0, 0, 0.75, TOP_H, HI); c.save(prefix + ".tl")
    c = Cv(8, TOP_H); c.vgrad(0, 0, 8, TOP_H, TB1, TB2); c.rect(0, TOP_H - 0.6, 8, 0.6, LO)
    c.rect(0, 0, 8, 0.75, HI); c.save(prefix + ".t")
    c = Cv(24, TOP_H); c.vgrad(0, 0, 24, TOP_H, TB1, TB2); c.rect(0, TOP_H - 0.6, 24, 0.6, LO)
    c.rect(0, 0, 24, 0.75, HI); c.rect(24 - 0.75, 0, 0.75, TOP_H, LO); c.save(prefix + ".tr")
    # sides
    side = SIDE
    c = Cv(SIDE_W, 8); c.rect(0, 0, SIDE_W, 8, side); c.rect(0, 0, 0.75, 8, HI); c.rect(SIDE_W - 0.6, 0, 0.6, 8, LO); c.save(prefix + ".l")
    c = Cv(SIDE_W, 8); c.rect(0, 0, SIDE_W, 8, side); c.rect(SIDE_W - 0.75, 0, 0.75, 8, LO); c.rect(0, 0, 0.6, 8, HI); c.save(prefix + ".r")
    # bottom
    # Classic shades the bottom bar left-to-right like the body: dark at both ends,
    # bright around the middle. The centre piece carries the whole sheen and is
    # stretched across the window; the corner pieces use the end colours.
    dark_l, dark_r = BODY2, tuple(round(a + (b - a) * 0.15) for a, b in zip(BODY2, BODY1))
    sheen = [(0, dark_l), (0.42, BODY1), (0.58, BODY1), (1, dark_r)]
    def bottom(w, left=False, right=False, centre=False):
        c = Cv(w, hb)
        if centre: c.hstops(0, 0, w, hb, sheen)
        else: c.rect(0, 0, w, hb, dark_l if left else dark_r)
        a = SIDE_W if left else 0; b = w - (SIDE_W if right else 0)
        c.rect(a, 0, b - a, 0.6, HI)
        c.rect(0, hb - 0.75, w, 0.75, LO)
        if left: c.rect(0, 0, 0.75, hb, HI)
        if right:
            c.rect(w - 0.75, 0, 0.75, hb, LO)
            for i in range(3):
                o = 3 + i * 3
                c.line(w - 2.2, hb - 2.2 - o, w - 2.2 - o, hb - 2.2, HI, 0.8)
                c.line(w - 2.2, hb - 1.4 - o, w - 1.4 - o, hb - 2.2, LO, 0.6)
        return c
    bottom(SIDE_W, left=True).save(prefix + ".bl")
    bottom(64, centre=True).save(prefix + ".b")
    bottom(22, right=True).save(prefix + ".br")

def misc():
    c = Cv(8, 8, (0, 0, 0, 255)); c.save("black")
    c = Cv(88, 16); c.inset(1, 1, 86, 14); c.save("pl.info")

# ---------------------------------------------------------------- classic-style value fills
# Classic colours the WHOLE bar by the slider value. Done without scripts: a ghost slider
# with a huge gradient "thumb" slides behind a groove-sized group that clips it, so the
# groove shows one (near-)uniform colour that follows the value.
VAL_STOPS = [(0, (36, 186, 60)), (0.4, (196, 214, 40)), (0.72, (232, 150, 36)), (1, (230, 56, 32))]
EQ_STOPS = [(0, (36, 186, 60)), (0.5, (196, 214, 40)), (0.72, (232, 150, 36)), (1, (230, 56, 32))]
FILL_LEN = 160
def fills():
    N = 48
    c = Cv(FILL_LEN, 61.8)      # horizontal travel: left = max value, right = min value
    c.hstops(0, 0, FILL_LEN, 61.8, [(i / N, mix(EQ_STOPS, 1 - i / N)) for i in range(N + 1)]); c.save("fill.eq")
    c = Cv(62.8, FILL_LEN)      # vertical travel
    c.vstops(0, 0, 62.8, FILL_LEN, [(i / N, mix(VAL_STOPS, VOL_DIR(i / N))) for i in range(N + 1)]); c.save("fill.vol")
    c = Cv(33.8, FILL_LEN)
    c.vstops(0, 0, 33.8, FILL_LEN, [(i / N, mix(VAL_STOPS, abs(i / N - 0.5) * 2)) for i in range(N + 1)]); c.save("fill.bal")
VOL_DIR = lambda u: u   # verified live: image top shows at max volume... flipped from first attempt
fills()

def bar_mask(key, x, y, w, h, r):
    """main.bg crop with a rounded hole: laid over the moving colour fill to round its ends."""
    bg = IMAGES["main.bg"][3]
    px, py, pw, ph = round(x * S), round(y * S), round(w * S), round(h * S)
    im = bg.crop((px, py, px + pw, py + ph)).copy()
    a = Image.new("L", (pw * 4, ph * 4), 255)
    ImageDraw.Draw(a).rounded_rectangle([0, 0, pw * 4 - 1, ph * 4 - 1], radius=r * S * 4, fill=0)
    im.putalpha(a.resize((pw, ph), Image.LANCZOS))
    fn = key + ".png"; im.save(os.path.join(IMG, fn), optimize=True); IMAGES[key] = (fn, w, h, im)

# ---------------------------------------------------------------- build art
# small 5x6 digits in the style of Classic's text.bmp, for kbps / kHz
SMALL_DIGITS = {
    0: ["#####", "#...#", "#...#", "#...#", "#...#", "#####"], 1: ["..#..", ".##..", "..#..", "..#..", "..#..", ".###."],
    2: ["#####", "....#", "#####", "#....", "#....", "#####"], 3: ["#####", "....#", ".####", "....#", "....#", "#####"],
    4: ["#...#", "#...#", "#####", "....#", "....#", "....#"], 5: ["#####", "#....", "#####", "....#", "....#", "#####"],
    6: ["#####", "#....", "#####", "#...#", "#...#", "#####"], 7: ["#####", "....#", "....#", "....#", "....#", "....#"],
    8: ["#####", "#...#", "#####", "#...#", "#...#", "#####"], 9: ["#####", "#...#", "#####", "....#", "....#", "#####"]}
SW, SH = 6, 6
# playlist time: the big-clock digit shapes on a 6x11 grid (same construction, 1-unit strokes)
PW, PH = 7, 11
def plnum():
    c = Cv(PW * 31, PH * 3)
    sx = [0, 1, 3, 5, 7, 8]; sy = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12]
    for dgt in range(10):
        for y in range(11):
            for x in range(6):
                if CLASSIC_DIGITS[sy[y]][dgt * 9 + sx[x]] == "#": c.rect(dgt * PW + x, PH + y, 1, 1, GREEN)
    def cell(i): return i * PW
    c.rect(cell(11) + 2, PH + 9, 1.4, 1.4, GREEN)                                   # .
    c.rect(cell(12) + 2.3, PH + 3, 1.4, 1.4, GREEN); c.rect(cell(12) + 2.3, PH + 7, 1.4, 1.4, GREEN)   # :
    c.rect(cell(15) + 1, PH + 5, 4, 1, GREEN)                                        # -
    c.rect(cell(19) + 1, PH + 5, 4, 1, GREEN); c.rect(cell(19) + 2.5, PH + 3.5, 1, 4, GREEN)           # +
    c.poly([(cell(21) + 4.4, PH + 0.5), (cell(21) + 5.4, PH + 0.5), (cell(21) + 1.6, PH + 10.5), (cell(21) + 0.6, PH + 10.5)], GREEN)  # /
    c.save("plnum", (31 * int(n(PW)), 3 * int(n(PH))))   # exact cell grid, also at fractional scales
def smallnum():
    c = Cv(SW * 31, SH * 3)
    for dgt, rows in SMALL_DIGITS.items():
        for py, row in enumerate(rows):
            for px, ch in enumerate(row):
                if ch == "#": c.rect(dgt * SW + px, SH + py, 1, 1, GREEN)
    # extra glyphs for the playlist time: . : - + /
    c.rect(11 * SW + 2, SH + 5, 1, 1, GREEN)
    c.rect(12 * SW + 2, SH + 1, 1, 1, GREEN); c.rect(12 * SW + 2, SH + 4, 1, 1, GREEN)
    c.rect(15 * SW + 1, SH + 3, 3, 1, GREEN)
    c.rect(19 * SW + 1, SH + 3, 3, 1, GREEN); c.rect(19 * SW + 2, SH + 2, 1, 3, GREEN)
    c.poly([(21 * SW + 3.2, SH), (21 * SW + 4.2, SH), (21 * SW + 1.8, SH + 6), (21 * SW + 0.8, SH + 6)], GREEN)
    c.save("smallnum", (31 * int(n(SW)), 3 * int(n(SH))))   # exact cell grid, also at fractional scales
def channels():
    for key, (m, st) in {"none": (DIM, DIM), "mono": (GREEN, DIM), "stereo": (DIM, GREEN), "surround": (GREEN, GREEN)}.items():
        c = Cv(56, 10)
        c.text(0, 5.2, "mono", 6.4, m, "lm"); c.text(24, 5.2, "stereo", 6.4, st, "lm")
        c.save("ch." + key)
main_bg(); shade_bg(); transport(); thumbs(); status(); numfont(); plnum(); smallnum(); channels(); eq_bg(); misc()
bar_mask("mask.vol", 107.6, 60.6, 62.8, 4.3, 2.1); bar_mask("mask.bal", 180.6, 60.6, 33.8, 4.3, 2.1)
for st_key, lab, w in (("eq.on", "ON", 26), ("eq.auto", "AUTO", 34)):
    led_button(st_key, w, 12, lab, 6)
text_button("eq.presets", 44, 12, "PRESETS", 6)
for lab in ("ADD", "REM", "SEL", "MISC", "LIST", "FULL", "1X", "2X", "PREV", "NEXT", "MENU"):
    text_button("tb." + lab.lower(), 28, 16, lab)
streak()
frame("pl", "WINAMP PLAYLIST", 30)
frame("ml", "WINAMP LIBRARY", 12)
frame("vid", "WINAMP VIDEO", 30)
frame("vis", "VISUALIZATION", 30)

# ---------------------------------------------------------------- XML
def w(path, txt):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(txt)

el = ["<elements>"]
for key, (fn, cw_, ch_, im) in sorted(IMAGES.items()):
    el.append(f'  <bitmap id="chd.{key}" file="img/{fn}" x="0" y="0" w="{im.size[0]}" h="{im.size[1]}"/>')
el.append(f'  <bitmapfont id="chd.numfont" file="chd.numfont" charwidth="{n(CW)}" charheight="{n(CH)}" hspacing="0" vspacing="0"/>')
el.append(f'  <bitmapfont id="chd.plnum" file="chd.plnum" charwidth="{n(PW)}" charheight="{n(PH)}" hspacing="0" vspacing="0"/>')
el.append(f'  <bitmapfont id="chd.smallnum" file="chd.smallnum" charwidth="{n(SW)}" charheight="{n(SH)}" hspacing="0" vspacing="0"/>')
for _k in ("none", "mono", "stereo", "surround"):   # ids expected by the stock songinfo script
    _im = IMAGES["ch." + _k][3]
    el.append(f'  <bitmap id="player.songinfo.{_k}" file="img/ch.{_k}.png" x="0" y="0" w="{_im.size[0]}" h="{_im.size[1]}"/>')
el.append(f"""
  <color id="chd.text" value="0,232,0"/>
  <color id="chd.titletext" value="{rgb(TTEXT)}"/>
  <color id="chd.label" value="{rgb(LABEL)}"/>

  <color id="wasabi.list.text" value="0,232,0"/>
  <color id="wasabi.list.background" value="0,0,0"/>
  <color id="wasabi.list.text.alternate" value="0,232,0"/>
  <color id="wasabi.list.background.alternate" value="10,12,18"/>
  <color id="wasabi.list.text.selected" value="255,255,255"/>
  <color id="wasabi.list.text.selected.background" value="0,0,198"/>
  <color id="studio.list.item.selected" value="0,0,198"/>
  <color id="studio.list.item.focused" value="0,0,198"/>
  <color id="wasabi.list.text.current" value="255,255,255"/>
  <color id="wasabi.list.text.selected.inactive" value="255,255,255"/>
  <color id="wasabi.list.text.selected.background.inactive" value="{rgb(SELINACT)}"/>
  <color id="wasabi.list.column.background" value="{rgb(SIDE)}"/>
  <color id="wasabi.list.column.text" value="{rgb(TTEXT)}"/>
  <color id="wasabi.list.column.frame.top" value="{rgb(HI)}"/>
  <color id="wasabi.list.column.frame.middle" value="{rgb(SIDE)}"/>
  <color id="wasabi.list.column.frame.bottom" value="{rgb(LO)}"/>
  <color id="wasabi.list.column.empty" value="{rgb(SIDE)}"/>
  <color id="wasabi.window.background" value="{rgb(WINBG)}"/>
  <color id="wasabi.window.text" value="{rgb(TTEXT)}"/>
  <color id="wasabi.border.sunken" value="{rgb(HI)}"/>
  <color id="wasabi.scrollbar.foreground" value="{rgb(BTN2)}"/>
  <color id="wasabi.scrollbar.background" value="0,0,0"/>
  <color id="wasabi.scrollbar.foreground.inverted" value="0,0,0"/>
  <color id="wasabi.scrollbar.background.inverted" value="0,0,0"/>
  <color id="wasabi.button.text" value="{rgb(INK)}"/>
  <color id="wasabi.button.hiliteText" value="{rgb(INK)}"/>
  <color id="wasabi.button.dimmedText" value="{rgb(DIMTXT)}"/>
</elements>
""")
w("xml/elements.xml", "\n".join(el))

def btn(id_, x, y, img, action=None, param=None, tip=None, relx=False, rely=False, extra=""):
    a = f' action="{action}"' if action else ""
    p = f' param="{param}"' if param else ""
    t = f' tooltip="{tip}"' if tip else ""
    rx = ' relatx="1"' if relx else ""
    ry = ' relaty="1"' if rely else ""
    return (f'  <button id="{id_}"{a}{p} x="{n(x)}" y="{n(y)}"{rx}{ry} image="chd.{img}" downImage="chd.{img}.p" '
            f'hoverImage="chd.{img}.h"{t} rectrgn="1"{extra}/>')

def tgl(id_, x, y, img, cfg, tip):
    return (f'  <togglebutton id="{id_}" x="{n(x)}" y="{n(y)}" image="chd.{img}" downImage="chd.{img}.p" hoverImage="chd.{img}.h" '
            f'activeImage="chd.{img}.on" cfgattrib="{cfg}" tooltip="{tip}" rectrgn="1"/>')

def slider(id_, x, y, w_, h_, thumb, action, param=None, tip="", vert=False):
    p = f' param="{param}"' if param else ""
    o = ' orientation="vertical"' if vert else ""
    return (f'  <slider id="{id_}" action="{action}"{p} x="{n(x)}" y="{n(y)}" w="{n(w_)}" h="{n(h_)}"{o} thumb="chd.thumb.{thumb}" '
            f'downThumb="chd.thumb.{thumb}.p" hoverThumb="chd.thumb.{thumb}.h" tooltip="{tip}"/>')

def fill_group(gid, action, param, wu, hu, img, vert):
    wpx, hpx = round(wu * S), round(hu * S)
    iw, ih = IMAGES[img][3].size
    p = f' param="{param}"' if param else ""
    if vert:
        sl = f'<slider id="{gid}.s" action="{action}"{p} orientation="vertical" x="0" y="{hpx - ih}" w="{wpx}" h="{2 * ih - hpx}" thumb="chd.{img}" ghost="1"/>'
    else:
        sl = f'<slider id="{gid}.s" action="{action}"{p} x="{wpx - iw}" y="0" w="{2 * iw - wpx}" h="{hpx}" thumb="chd.{img}" ghost="1"/>'
    return f'<groupdef id="{gid}" w="{wpx}" h="{hpx}">\n  {sl}\n</groupdef>\n'
def fill_use(gid, xu, yu, wu, hu):
    return f'  <group id="{gid}" x="{n(xu)}" y="{n(yu)}" w="{round(wu * S)}" h="{round(hu * S)}" ghost="1"/>'

PLG = "{45F3F7C1-A6F3-4EE6-A15E-125E92FC3F8D}"
bands = " ".join(f'ColorBand{i}="{r},{g},{b}"' for i, (r, g, b) in enumerate(
    [mix([(0, (24, 200, 30)), (0.6, (222, 214, 40)), (1, (232, 50, 24))], i / 15) for i in range(16)], 1))
osc = " ".join(f'colorosc{i}="{v}"' for i, v in enumerate(("255,255,255", "214,214,222", "181,189,189", "160,170,175", "148,156,165"), 1))
FS_T, FS_S = round(8.4 * S), round(7.2 * S)
TFS = float(os.environ.get("CHD_TFS", 12.6))   # song title size in classic units

FB = int(os.environ.get("CHD_FB", 0)) or n(SH); FF = int(os.environ.get("CHD_FF", 0)) or n(SH)
songinfo_def = f"""<groupdef id="chd.songinfo" w="{n(170)}" h="{n(12)}">
  <text id="Bitrate" display="" default="" x="{n(4.5)}" y="{n(3)}" w="{n(30)}" h="{n(SH)}" font="chd.smallnum" fontsize="{FB}" align="center" valign="top" color="chd.text"/>
  <text id="Frequency" display="" default="" x="{n(55.5)}" y="{n(3)}" w="{n(20)}" h="{n(SH)}" font="chd.smallnum" fontsize="{FF}" align="right" valign="top" color="chd.text"/>
  <layer id="channels" x="{n(112)}" y="{n(1)}" image="player.songinfo.none"/>
  <script id="songinfo.script" file="scripts/songinfo.maki"/>
</groupdef>
"""
main = songinfo_def + fill_group("chd.volfill", "VOLUME", None, 62.8, 4.3, "fill.vol", True) + fill_group("chd.balfill", "PAN", None, 33.8, 4.3, "fill.bal", True) + f"""<container id="main" name="Main Window" default_x="0" default_y="0" default_visible="1">

<layout id="normal" background="chd.main.bg" droptarget="pldr" linkwidth="shade">
  <layer id="titlegrip" x="{n(18)}" y="0" w="{n(222)}" h="{n(14)}" move="1" rectrgn="1" dblclickaction="SWITCH" dblclickparam="shade"/>
{btn("sysmenu", 6, 3, "sb.menu", "SYSMENU", tip="Main Menu")}
{btn("minimize", 244, 3, "sb.min", "MINIMIZE", tip="Minimize")}
{btn("winshade", 254, 3, "sb.shade", "SWITCH", "shade", "Windowshade Mode")}
{btn("close", 264, 3, "sb.close", "CLOSE", tip="Close")}

  <status id="status" x="{n(24)}" y="{n(28)}" w="{n(9)}" h="{n(9)}" stopBitmap="chd.st.stop" playBitmap="chd.st.play" pauseBitmap="chd.st.pause"/>
  <text id="timer" display="time" x="{n(36)}" y="{n(26)}" w="{n(64)}" h="{n(13)}" font="chd.numfont" fontsize="{n(13)}" align="right" timecolonwidth="{n(6)}" color="chd.text"/>
  <vis id="vis" x="{n(24)}" y="{n(44)}" w="{n(76)}" h="{n(18)}" {bands} colorbandpeak="150,150,150" {osc}/>

  <Songticker id="songticker" showlen="1" x="{n(111.5)}" y="{n(22.5)}" w="{n(153)}" h="{n(14)}" font="Arial Unicode MS" altfont="Arial" fontsize="{round(TFS * S)}" bold="0" antialias="1" ticker="1" tickerstep="{max(1, round(S))}" rightpadding="-{n(133)}" align="left" valign="center" color="chd.text" rightclickaction="trackmenu" dblclickaction="trackinfo"/>
  <group id="chd.songinfo" x="{n(100)}" y="{n(40)}"/>

{fill_use("chd.volfill", 107.6, 60.6, 62.8, 4.3)}
{fill_use("chd.balfill", 180.6, 60.6, 33.8, 4.3)}
  <layer x="{n(107.6)}" y="{n(60.6)}" image="chd.mask.vol" ghost="1"/>
  <layer x="{n(180.6)}" y="{n(60.6)}" image="chd.mask.bal" ghost="1"/>
{slider("volume", 107, 57, 64, 11, "vol", "VOLUME", tip="Volume")}
{slider("balance", 180, 57, 35, 11, "vol", "PAN", tip="Balance")}
  <button id="eq" action="TOGGLE" param="equalizer" x="{n(219)}" y="{n(57)}" image="chd.btn.eq" downImage="chd.btn.eq.p" hoverImage="chd.btn.eq.h" activeImage="chd.btn.eq.on" tooltip="Equalizer" rectrgn="1"/>
  <button id="pl" action="TOGGLE" param="guid:pl" x="{n(243)}" y="{n(57)}" image="chd.btn.pl" downImage="chd.btn.pl.p" hoverImage="chd.btn.pl.h" activeImage="chd.btn.pl.on" tooltip="Playlist Editor" rectrgn="1"/>

{slider("seeker", 16, 72, 248, 10, "seek", "SEEK", tip="Seek")}

{btn("prev", 16, 88, "btn.prev", "PREV", tip="Previous")}
{btn("play", 39, 88, "btn.play", "PLAY", tip="Play")}
{btn("pause", 62, 88, "btn.pause", "PAUSE", tip="Pause")}
{btn("stop", 85, 88, "btn.stop", "STOP", tip="Stop")}
{btn("next", 108, 88, "btn.next", "NEXT", tip="Next")}
{btn("eject", 136, 89, "btn.eject", "EJECT", tip="Open file(s)")}
{tgl("shuffle", 164, 89.5, "btn.shuffle", PLG + ";Shuffle", "Toggle Shuffle")}
{tgl("repeat", 210, 89.5, "btn.repeat", PLG + ";Repeat", "Toggle Repeat")}
{btn("about", 255, 89.5, "btn.bolt", "TOGGLE", "guid:{{D6201408-476A-4308-BF1B-7BACA1124B12}}", "About Winamp")}
</layout>

<layout id="shade" background="chd.shade.bg" droptarget="pldr">
  <layer id="shadegrip" x="{n(16)}" y="0" w="{n(34)}" h="{n(14)}" move="1" rectrgn="1" dblclickaction="SWITCH" dblclickparam="normal"/>
{btn("sysmenu", 6, 2.5, "sb.menu", "SYSMENU", tip="Main Menu")}
  <vis id="shadevis" x="{n(52)}" y="{n(3.2)}" w="{n(71)}" h="{n(7.6)}" mode="1" {bands} colorbandpeak="150,150,150" {osc}/>
  <text id="timer" display="time" x="{n(125)}" y="{n(4)}" w="{n(40)}" h="{n(SH)}" font="chd.smallnum" fontsize="{n(SH)}" align="center" valign="top" color="chd.text"/>
{btn("prev", 168, 2.5, "sb.prev", "PREV", tip="Previous")}
{btn("play", 178, 2.5, "sb.play", "PLAY", tip="Play")}
{btn("pause", 188, 2.5, "sb.pause", "PAUSE", tip="Pause")}
{btn("stop", 198, 2.5, "sb.stop", "STOP", tip="Stop")}
{btn("next", 208, 2.5, "sb.next", "NEXT", tip="Next")}
{btn("eject", 220, 2.5, "sb.eject", "EJECT", tip="Open file(s)")}
{btn("minimize", 244, 2.5, "sb.min", "MINIMIZE", tip="Minimize")}
{btn("winshade", 254, 2.5, "sb.restore", "SWITCH", "normal", "Normal Mode")}
{btn("close", 264, 2.5, "sb.close", "CLOSE", tip="Close")}
</layout>

</container>
"""
w("xml/player.xml", main)

eqs = "\n".join(slider("preamp" if i == 0 else f"eq{i}", x + 1.5, 38, 11, 63, "eq", "EQ_BAND",
                       "preamp" if i == 0 else str(i), "Preamp" if i == 0 else EQL[i] + " Hz", vert=True)
                for i, x in enumerate(EQX))
eqfill_defs = "".join(fill_group(f"chd.eqfill.{i}", "EQ_BAND", "preamp" if i == 0 else str(i), 3.8, 61.8, "fill.eq", False) for i in range(11))
eqfill_uses = "\n".join(fill_use(f"chd.eqfill.{i}", x + 5.1, 38.6, 3.8, 61.8) for i, x in enumerate(EQX))
eq = eqfill_defs + f"""<container id="equalizer" name="Equalizer" default_x="0" default_y="{n(116)}" default_visible="1">
<layout id="normal" background="chd.eq.bg">
  <layer id="titlegrip" x="0" y="0" w="{n(260)}" h="{n(14)}" move="1" rectrgn="1"/>
{btn("close", 264, 3, "sb.close", "CLOSE", tip="Close")}
  <button id="eqonoff" action="EQ_TOGGLE" x="{n(14)}" y="{n(18)}" image="chd.eq.on" downImage="chd.eq.on.p" hoverImage="chd.eq.on.h" activeImage="chd.eq.on.on" tooltip="Equalizer On/Off" rectrgn="1"/>
  <button id="eqauto" action="EQ_AUTO" x="{n(42)}" y="{n(18)}" image="chd.eq.auto" downImage="chd.eq.auto.p" hoverImage="chd.eq.auto.h" activeImage="chd.eq.auto.on" tooltip="Auto-load presets" rectrgn="1"/>
{btn("eqpresets", 217, 18, "eq.presets", "MENU", "presets", "Presets")}
{eqfill_uses}
{eqs}
</layout>
</container>
"""
w("xml/eq.xml", eq)

STREAK_DEFS = f"""<groupdef id="chd.streak.l">
  <layer id="titlebar.center.active" x="0" y="0" w="{n(-5)}" h="{n(TOP_H)}" relatw="1" image="chd.streak" ghost="1"/>
</groupdef>
<groupdef id="chd.streak.r">
  <layer id="titlebar.center.active" x="{n(5)}" y="0" w="{n(-5)}" h="{n(TOP_H)}" relatw="1" image="chd.streak" ghost="1"/>
</groupdef>
"""
def title_group(prefix):
    # same object ids the stock titlebar script expects: it measures the text and keeps it centred on resize
    return f"""<groupdef id="chd.title.{prefix}">
  <group id="chd.streak.l" instanceid="wasabi.titlebar.streak.left" x="0" y="0" w="{n(60)}" h="{n(TOP_H)}"/>
  <text id="window.titlebar.title" x="{n(64)}" y="0" w="{n(100)}" h="{n(TOP_H)}" default="{TITLES[prefix]}" font="Arial" fontsize="{round(8.4 * S)}" bold="1" antialias="1" color="chd.titletext" valign="center" ghost="1"/>
  <layer id="window.titlebar.title.overlay" x="0" y="0" w="1" h="1" alpha="0" ghost="1"/>
  <group id="chd.streak.r" instanceid="wasabi.titlebar.streak.right" x="{n(170)}" y="0" w="{n(-170)}" relatw="1" h="{n(TOP_H)}"/>
  <layer id="mousetrap" x="0" y="0" w="0" h="0" relatw="1" relath="1" move="1"/>
  <script id="titlebar" file="scripts/titlebar.maki" param="wasabi.titlebar.streak.left;window.titlebar.title;wasabi.titlebar.streak.right"/>
</groupdef>
"""
def frame_xml(cid, name, guid, prefix, hb, comp, bottom, dx, dy, lw, lh, vis="1", holder=None):
    if holder is None:
        holder = (f'<component x="{n(SIDE_W)}" y="{n(TOP_H)}" w="{n(-2 * SIDE_W)}" h="{n(-(TOP_H + hb))}" '
                  f'relatw="1" relath="1" noshowcmdbar="1" {comp}/>')
    # NOTE: a layout without a background has an empty window region unless a child
    # contributes one, so the frame lives in a group with background + sysregion="1"
    # (same pattern as every stock frame in Winamp Modern / Bento).
    return title_group(prefix) + f"""<groupdef id="chd.frame.{prefix}" background="chd.black" sysregion="1">
  <layer x="0" y="0" w="0" h="0" relatw="1" relath="1" image="chd.black" sysregion="1"/>
  <layer x="0" y="0" image="chd.{prefix}.tl" move="1"/>
  <layer x="{n(8)}" y="0" w="{n(-32)}" h="{n(TOP_H)}" relatw="1" image="chd.{prefix}.t" move="1"/>
  <group id="chd.title.{prefix}" x="{n(5)}" y="0" w="{n(-27)}" relatw="1" h="{n(TOP_H)}"/>
  <layer x="{n(-24)}" y="0" relatx="1" image="chd.{prefix}.tr" move="1"/>
  <layer x="0" y="{n(TOP_H)}" w="{n(SIDE_W)}" h="{n(-(TOP_H + hb))}" relath="1" image="chd.{prefix}.l" resize="left"/>
  <layer x="{n(-SIDE_W)}" y="{n(TOP_H)}" w="{n(SIDE_W)}" h="{n(-(TOP_H + hb))}" relatx="1" relath="1" image="chd.{prefix}.r" resize="right"/>
  <layer x="0" y="{n(-hb)}" relaty="1" image="chd.{prefix}.bl" move="1"/>
  <layer x="{n(SIDE_W)}" y="{n(-hb)}" w="{n(-(SIDE_W + 22))}" h="{n(hb)}" relaty="1" relatw="1" image="chd.{prefix}.b" move="1"/>
  <layer x="{n(-22)}" y="{n(-hb)}" relatx="1" relaty="1" image="chd.{prefix}.br"/>
  <layer x="{n(-14)}" y="{n(-14)}" w="{n(14)}" h="{n(14)}" relatx="1" relaty="1" resize="bottomright" rectrgn="1"/>
{btn("close", -15, 5.5, "sb.close", "CLOSE", tip="Close", relx=True)}
  {holder}
{bottom}
</groupdef>

<container id="{cid}" name="{name}" dynamic="1" component="guid:{guid}" default_x="{n(dx)}" default_y="{n(dy)}" default_visible="{vis}">
<layout id="normal" minimum_w="{n(275)}" minimum_h="{n(116)}" w="{n(lw)}" h="{n(lh)}">
  <group id="chd.frame.{prefix}" x="0" y="0" w="0" h="0" relatw="1" relath="1" sysregion="1"/>
</layout>
</container>

"""

def bbtn(id_, i, key, action, tip, hb=30):
    return btn(id_, SIDE_W + 2 + i * 30, -hb + 7, "tb." + key, action, tip=tip, rely=True)

pl_bottom = "\n".join([
    bbtn("pl.add", 0, "add", "PE_Add", "Add Files to Playlist"),
    bbtn("pl.rem", 1, "rem", "PE_Rem", "Remove Files from Playlist"),
    bbtn("pl.sel", 2, "sel", "PE_Sel", "Select Files in Playlist"),
    bbtn("pl.misc", 3, "misc", "PE_Misc", "Misc Actions"),
    f'  <layer x="{n(-143)}" y="{n(-23)}" relatx="1" relaty="1" image="chd.pl.info"/>',
    f'  <text id="PLTime" display="PE_Info" x="{n(-159)}" y="{n(-18)}" w="{n(120)}" h="{n(SH)}" relatx="1" relaty="1" font="chd.smallnum" fontsize="{n(SH)}" align="center" valign="top" color="chd.text" ghost="1"/>',
    btn("pl.list", -52, -23, "tb.list", "PE_List", tip="Manage Playlist", relx=True, rely=True),
])
vid_bottom = "\n".join([
    bbtn("vid.fs", 0, "full", "VID_FS", "Fullscreen"),
    bbtn("vid.1x", 1, "1x", "VID_1X", "Normal Size"),
    bbtn("vid.2x", 2, "2x", "VID_2X", "Double Size"),
    bbtn("vid.misc", 3, "misc", "VID_Misc", "Options"),
    f'  <text id="vidinfo" display="VID_Info" x="{n(134)}" y="{n(-23)}" w="{n(-160)}" h="{n(16)}" relatw="1" relaty="1" font="Arial Unicode MS" altfont="Arial" fontsize="{round(9.6 * S)}" bold="0" antialias="1" valign="center" color="chd.label" ghost="1"/>',
])
vis_bottom = "\n".join([
    bbtn("vis.fs", 0, "full", "VIS_FS", "Fullscreen"),
    bbtn("vis.prev", 1, "prev", "VIS_Prev", "Previous Visualization"),
    bbtn("vis.next", 2, "next", "VIS_Next", "Next Visualization"),
    bbtn("vis.menu", 3, "menu", "Vis_Menu", "Options"),
])
w("xml/windows.xml", STREAK_DEFS +
  frame_xml("Pledit", "Playlist Editor", PLG, "pl", 30, "", pl_bottom, 0, 232, 275, 232,
              holder=(f'<windowholder id="chd.pl.holder" x="{n(SIDE_W)}" y="{n(TOP_H)}" w="{n(-2 * SIDE_W)}" h="{n(-(TOP_H + 30))}" '
                      f'relatw="1" relath="1" autofocus="0" wantfocus="0" autoclose="1" autoopen="1" autoavailable="1" '
                      f'hold="guid:{PLG.lower()}"/>'))
  + frame_xml("MLibrary", "Media Library", "{6B0EDF80-C9A5-11D3-9F26-00C04F39FFC6}", "ml", 12,
              'autoopen="1" autoclose="0" param="guid:{6B0EDF80-C9A5-11D3-9F26-00C04F39FFC6}"', "", 275, 0, 400, 348, vis="@HAVE_LIBRARY@")
  + frame_xml("Video", "Video", "{F0816D7B-FFFC-4343-80F2-E8199AA15CC3}", "vid", 30,
              'autoopen="1" autoclose="1" param="{F0816D7B-FFFC-4343-80F2-E8199AA15CC3}"', vid_bottom, 275, 0, 320, 260, vis="0")
  + frame_xml("AVS", "Visualizations", "{0000000A-000C-0010-FF7B-01014263450C}", "vis", 30,
              'autoopen="1" autoclose="1" param="{0000000A-000C-0010-FF7B-01014263450C}"', vis_bottom, 275, 0, 320, 260, vis="0"))

w("skin.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<WasabiXML version="1.35">

  <skininfo>
    <version>1.24</version>
    <name>{NAME}</name>
    <comment>The Classic Winamp layout redrawn at {S}x for high-resolution displays ({round(275 * S)}x{round(116 * S)} main window).</comment>
    <author>Claude</author>
    <screenshot>screenshot.png</screenshot>
  </skininfo>

  <include file="xml/elements.xml"/>
  <include file="xml/player.xml"/>
  <include file="xml/eq.xml"/>
  <include file="xml/windows.xml"/>

</WasabiXML>
""")

# ---------------------------------------------------------------- preview / screenshot
# fractional scales give float pixel coordinates below; round them at the PIL boundary
_ac, _cr, _rs = Image.Image.alpha_composite, Image.Image.crop, Image.Image.resize
Image.Image.alpha_composite = lambda self, im, dest=(0, 0), source=(0, 0): _ac(self, im, tuple(round(v) for v in dest), source)
Image.Image.crop = lambda self, box=None: _cr(self, None if box is None else tuple(round(v) for v in box))
Image.Image.resize = lambda self, size, *a, **k: _rs(self, tuple(max(1, round(v)) for v in size), *a, **k)
def I(key): return IMAGES[key][3]
def paste(dst, key, x, y, ox=0, oy=0):
    im = I(key); dst.alpha_composite(im, (ox + round(x * S), oy + round(y * S)))

W, H = round(275 * S), round(116 * S)
pv = Image.new("RGBA", (W, H * 4), (0, 0, 0, 255))
paste(pv, "main.bg", 0, 0)
def fillrect(x, y, w, h, col):
    ImageDraw.Draw(pv).rectangle([round(x * S), round(y * S), round((x + w) * S) - 1, round((y + h) * S) - 1], fill=col)
fillrect(107.6, 60.6, 62.8, 4.3, mix(VAL_STOPS, 0.68)); fillrect(180.6, 60.6, 33.8, 4.3, mix(VAL_STOPS, 0.0))
paste(pv, "mask.vol", 107.6, 60.6); paste(pv, "mask.bal", 180.6, 60.6)
for key, x, y in (("sb.menu", 6, 3), ("sb.min", 244, 3), ("sb.shade", 254, 3), ("sb.close", 264, 3), ("st.play", 24, 28),
                  ("thumb.vol", 146, 57), ("thumb.vol", 190.5, 57), ("btn.eq.on", 219, 57), ("btn.pl.on", 243, 57),
                  ("thumb.seek", 90, 72), ("btn.prev", 16, 88), ("btn.play", 39, 88), ("btn.pause", 62, 88),
                  ("btn.stop", 85, 88), ("btn.next", 108, 88), ("btn.eject", 136, 89), ("btn.shuffle", 164, 89.5),
                  ("btn.repeat.on", 210, 89.5), ("btn.bolt", 255, 89.5)):
    paste(pv, key, x, y)
nf = I("numfont")
def digit(ch, x):
    idx = {":": 12, "-": 15}.get(ch, None)
    if idx is None: idx = int(ch)
    cell = nf.crop((idx * CW * S, CH * S, (idx + 1) * CW * S, 2 * CH * S))
    pv.alpha_composite(cell, (round(x * S), 26 * S))
x = 100 - (4 * CW + 6)
for ch in "02:47":
    digit(ch, x); x += 6 if ch == ":" else CW
d = ImageDraw.Draw(pv)
FONT_R = FONT.replace("-Bold", "-Regular") if os.path.exists(FONT.replace("-Bold", "-Regular")) else FONT
fs = ImageFont.truetype(FONT, FS_T); fs2 = ImageFont.truetype(FONT_R, round(7.8 * S)); fst = ImageFont.truetype(FONT_R, round(12 * S))
d.text((112 * S, 29.5 * S), "1. DJ Mike Llama - Llama Whippin' Intro (0:05)  ***  1. DJ", font=fst, fill=GREEN, anchor="lm")
d.rectangle([266 * S, 24 * S, 275 * S - 1, 36 * S], fill=None)
sn = I("smallnum")
def small(txt, right, y):
    x = right - len(txt) * SW
    for ch in txt:
        pv.alpha_composite(sn.crop((int(ch) * SW * S, SH * S, (int(ch) + 1) * SW * S, 2 * SH * S)), (round(x * S), round(y * S))); x += SW
small("128", 135, 43); small("44", 175, 43); paste(pv, "ch.stereo", 212, 41)
import random
random.seed(4)
for i in range(19):
    hgt = random.randint(2, 16)
    for j in range(hgt):
        col = mix([(0, (24, 200, 30)), (0.6, (222, 214, 40)), (1, (232, 50, 24))], j / 15)
        d.rectangle([(24 + i * 4) * S, (61 - j) * S, (24 + i * 4 + 3) * S - 1, (62 - j) * S - 1], fill=col)
# re-mask the title overflow
pv.alpha_composite(I("main.bg").crop((265 * S, 20 * S, W, 40 * S)), (265 * S, 20 * S))
# eq
paste(pv, "eq.bg", 0, 116)
for key, x, y in (("sb.close", 264, 3), ("eq.on.on", 14, 18), ("eq.auto", 42, 18), ("eq.presets", 217, 18)):
    paste(pv, key, x, 116 + y)
for i, x in enumerate(EQX):
    fillrect(x + 5.1, 116 + 38.6, 3.8, 61.8, mix(EQ_STOPS, 0.5 if i == 0 else 0.5 - ((i * 7) % 5 - 2) * 7 / 52))
    paste(pv, "thumb.eq", x + 1.5, 116 + 38 + (26 if i == 0 else 26 + 14 * ((i * 7) % 5 - 2) / 2))
# playlist frame
oy = 232
def tile(key, x0, y0, wpx, hpx):
    pv.alpha_composite(I(key).resize((max(1, wpx), max(1, hpx))), (x0, y0))
paste(pv, "pl.tl", 0, oy); tile("pl.t", 8 * S, oy * S, (275 - 32) * S, TOP_H * S); paste(pv, "pl.tr", 251, oy)
_ft = ImageFont.truetype(FONT, round(8.4 * S)); _tw = _ft.getlength("WINAMP PLAYLIST"); _tx = (W - _tw) / 2
tile("streak", 5 * S, oy * S, round(_tx) - 10 * S, TOP_H * S); tile("streak", round(_tx + _tw) + 5 * S, oy * S, W - 22 * S - round(_tx + _tw) - 5 * S, TOP_H * S)
ImageDraw.Draw(pv).text((_tx, (oy + TOP_H / 2 + 0.3) * S), "WINAMP PLAYLIST", font=_ft, fill=TTEXT, anchor="lm")
tile("pl.l", 0, (oy + TOP_H) * S, SIDE_W * S, (232 - TOP_H - 30) * S); tile("pl.r", (275 - SIDE_W) * S, (oy + TOP_H) * S, SIDE_W * S, (232 - TOP_H - 30) * S)
paste(pv, "pl.bl", 0, oy + 202); tile("pl.b", SIDE_W * S, (oy + 202) * S, (275 - SIDE_W - 22) * S, 30 * S); paste(pv, "pl.br", 253, oy + 202)
paste(pv, "sb.close", 260, oy + 5.5)
for i, k_ in enumerate(("add", "rem", "sel", "misc")):
    paste(pv, "tb." + k_, SIDE_W + 2 + i * 30, oy + 209)
paste(pv, "pl.info", 132, oy + 209); paste(pv, "tb.list", 223, oy + 209)
_pn = I("smallnum"); _t = "0:05/12:31"; _x = 176 - len(_t) * SW / 2
for _ch in _t:
    _i = {":": 12, "/": 21}.get(_ch); _i = int(_ch) if _i is None else _i
    pv.alpha_composite(_pn.crop((_i * SW * S, SH * S, (_i + 1) * SW * S, 2 * SH * S)), (round(_x * S), round((oy + 214) * S))); _x += SW
rows = ["1. DJ Mike Llama - Llama Whippin' Intro", "2. Second Track - In The Playlist", "3. Third Track - Another One"]
for i, r in enumerate(rows):
    yy = (oy + TOP_H + 3 + i * 11) * S
    if i == 0: d.rectangle([SIDE_W * S, yy - S, (275 - SIDE_W) * S - 1, yy + 10 * S], fill=(0, 0, 198))
    d.text(((SIDE_W + 3) * S, yy + 4.5 * S), r, font=fs, fill=(255, 255, 255) if i == 0 else GREEN, anchor="lm")
pv.save(os.path.join(OUT, f"preview_x{S}.png"))
sc = pv.convert("RGB"); sc.thumbnail((275 * 2, 464 * 2), Image.LANCZOS)
sc.save(os.path.join(ROOT, "screenshot.png"), optimize=True)

os.makedirs(os.path.join(ROOT, "scripts"), exist_ok=True)
for _m in ("songinfo.maki", "titlebar.maki"):
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", _m), os.path.join(ROOT, "scripts", _m))
# ---------------------------------------------------------------- package
wal = os.path.join(OUT, NAME + ".wal")
if os.path.exists(wal): os.remove(wal)
with zipfile.ZipFile(wal, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fns in os.walk(ROOT):
        for fn in sorted(fns):
            full = os.path.join(dp, fn)
            z.write(full, os.path.relpath(full, ROOT).replace(os.sep, "/"))
print(NAME, len(IMAGES), "images", os.path.getsize(wal), "bytes")
