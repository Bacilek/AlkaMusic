"""Draws the app icon (a cute stoat) -> assets/icon.ico and assets/icon.png.

Run: .venv\\Scripts\\python assets\\make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

S = 1024
HERE = Path(__file__).parent

BG = "#CFEBDD"
FUR = "#A8683A"
FUR_DARK = "#8A5129"
CREAM = "#FFF6E8"
PINK = "#F2A7A7"
EYE = "#2A1A12"
NOSE = "#5A2E22"
TAIL_TIP = "#2A1A12"


def ellipse(d, cx, cy, rx, ry, fill):
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill)


def draw():
    img = Image.new("RGBA", (S, S), BG)
    d = ImageDraw.Draw(img)

    # tail curling up on the right, with the black tip every stoat has
    box, w = (640, 740, 940, 1040), 84
    d.arc(box, start=270, end=90, fill=FUR, width=w)
    d.arc(box, start=270, end=330, fill=TAIL_TIP, width=w)
    ellipse(d, 790, 782, w // 2, w // 2, TAIL_TIP)  # round tail end

    # long slender neck/body with the white bib down the front
    d.rounded_rectangle((330, 560, 694, 1150), radius=180, fill=FUR)
    d.rounded_rectangle((420, 600, 604, 1150), radius=92, fill=CREAM)

    # small round ears set low on the sides
    for cx in (268, 756):
        ellipse(d, cx, 330, 78, 74, FUR_DARK)
        ellipse(d, cx, 336, 42, 40, PINK)

    # wide, flat head
    ellipse(d, 512, 470, 300, 225, FUR)

    # white upper lip, cheeks and chin
    ellipse(d, 512, 600, 170, 115, CREAM)
    ellipse(d, 400, 565, 95, 70, CREAM)
    ellipse(d, 624, 565, 95, 70, CREAM)

    # blush (soft)
    blush = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blush)
    ellipse(bd, 318, 555, 50, 28, (242, 150, 150, 170))
    ellipse(bd, 706, 555, 50, 28, (242, 150, 150, 170))
    img.alpha_composite(blush.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)

    # eyes with highlights
    for cx in (392, 632):
        ellipse(d, cx, 455, 46, 52, EYE)
        ellipse(d, cx - 15, 436, 17, 17, "white")
        ellipse(d, cx + 17, 476, 8, 8, "white")

    # nose + mouth
    d.rounded_rectangle((477, 535, 547, 576), radius=20, fill=NOSE)
    ellipse(d, 500, 547, 9, 6, "#8C5A4C")
    d.line((512, 576, 512, 602), fill=NOSE, width=9)
    d.arc((458, 572, 514, 626), start=20, end=160, fill=NOSE, width=9)
    d.arc((510, 572, 566, 626), start=20, end=160, fill=NOSE, width=9)

    # whiskers
    for side in (-1, 1):
        for dy, tilt in ((-12, -30), (14, 0), (40, 30)):
            x0 = 512 + side * 120
            d.line((x0, 585 + dy, x0 + side * 170, 585 + dy + tilt), fill="#C9A88C", width=6)

    # rounded square mask
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=220, fill=255)
    img.putalpha(mask)
    return img


if __name__ == "__main__":
    icon = draw().resize((256, 256), Image.LANCZOS)
    icon.save(HERE / "icon.png")
    icon.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
