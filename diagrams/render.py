"""Regenerate both original figures with Pillow and DejaVu Sans."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from conveyor import simulate

BG, INK, MUTE = "#f2f6fa", "#10243a", "#38556f"
BLUE, PALE, EDGE = "#174d85", "#dceafb", "#a9c4de"
RED, GREEN = "#8d2b29", "#155a3b"


def canvas(height, title, subtitle):
    im = Image.new("RGB", (1000, height), BG)
    d = ImageDraw.Draw(im)
    put(d, (44, 34), title, 42, bold=True)
    put(d, (46, 98), subtitle, 26, MUTE)
    return im, d


def put(d, xy, msg, size, color=INK, bold=False, anchor="lt"):
    font = ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    d.text(xy, msg, fill=color, font=font, anchor=anchor)


def arrow(d, x, y):
    d.line((x, y, x+39, y), fill=MUTE, width=4)
    d.polygon([(x+39, y), (x+27, y-7), (x+27, y+7)], fill=MUTE)


def save(im, name):
    im.save(HERE / f"{name}.webp", quality=85, method=6)


def snapshot(rows):
    im, d = canvas(395, "A full conveyor at tick 7", "Three zones occupied. A fourth package waits upstream.")
    _, blocked, slots, waiting, _ = rows[7]
    assert blocked and waiting == 1
    for i, box in enumerate(slots):
        x = 58 + 243*i
        d.rounded_rectangle((x, 173, x+188, 307), 17, fill=PALE, outline=EDGE, width=2)
        put(d, (x+94, 202), f"Zone {i+1}", 28, anchor="mt")
        put(d, (x+94, 252), f"Box {box}", 29, BLUE, True, anchor="mt")
        arrow(d, x+196, 241)
    put(d, (834, 225), "EXIT", 26, bold=True)
    put(d, (834, 265), "Blocked", 25, RED)
    put(d, (58, 341), "Upstream queue: box 4", 25, MUTE)
    save(im, "conveyor-zpa-full")


def restart(rows):
    im, d = canvas(550, "Restart after the exit opens", "State at the end of each tick. Empty zones are marked with a dot.")
    columns = [92, 253, 421, 581, 785]
    for x, label in zip(columns, ["Tick", "Zone 1", "Zone 2", "Zone 3", "Departed"]):
        put(d, (x, 167), label, 27, bold=True, anchor="mt")
    for n, (t, _, slots, _, departed) in enumerate(rows[7:13]):
        y = 214 + n*49
        if n % 2 == 0:
            d.rounded_rectangle((44, y-6, 943, y+35), 6, fill=PALE)
        for x, item in zip(columns, [t, *slots, departed]):
            put(d, (x, y), "·" if item is None else str(item), 28,
                GREEN if x == columns[-1] and item else INK, anchor="mt")
    save(im, "conveyor-zpa-restart")


if __name__ == "__main__":
    spec = json.loads((HERE.parent / "examples/blocked.json").read_text())
    results = simulate(**spec)
    snapshot(results)
    restart(results)
