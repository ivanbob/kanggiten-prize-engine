"""Export the official Kanggiten mark from Kangitten logobook.pdf."""
from __future__ import annotations

import os

import fitz
from PIL import Image

PDF = r"C:\Users\Public\Downloads\Zcode projects\Payout_system\Design\Kangitten logobook.pdf"
WEB = r"C:\Users\Public\Downloads\Zcode projects\Payout_system\web"
ASSETS = os.path.join(WEB, "assets")
os.makedirs(WEB, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

VIOLET = (120, 29, 255, 255)  # #781DFF


def hex_fill(fill):
    if not fill:
        return None
    r, g, b = fill[:3]
    return "#{:02X}{:02X}{:02X}".format(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def item_to_d(item) -> str:
    kind = item[0]
    if kind == "l":
        p0, p1 = item[1], item[2]
        return f"L {p1.x:.3f} {p1.y:.3f}"
    if kind == "c":
        # cubic: start, c1, c2, end — pymupdf gives (p1, p2, p3) after implicit current point
        pts = item[1:]
        if len(pts) == 4:
            _, c1, c2, end = pts
        else:
            c1, c2, end = pts
        return f"C {c1.x:.3f} {c1.y:.3f} {c2.x:.3f} {c2.y:.3f} {end.x:.3f} {end.y:.3f}"
    if kind == "re":
        r = item[1]
        return f"M {r.x0:.3f} {r.y0:.3f} H {r.x1:.3f} V {r.y1:.3f} H {r.x0:.3f} Z"
    if kind == "qu":
        c, end = item[1], item[2]
        return f"Q {c.x:.3f} {c.y:.3f} {end.x:.3f} {end.y:.3f}"
    return ""


def drawings_to_svg(page, fills, bbox, out_path, pad=4):
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    parts = []
    for d in page.get_drawings():
        fill = hex_fill(d.get("fill"))
        if fill not in fills:
            continue
        r = d["rect"]
        if r.x1 < x0 or r.x0 > x1 or r.y1 < y0 or r.y0 > y1:
            continue
        items = d.get("items") or []
        if not items:
            continue
        first = items[0]
        if first[0] == "l":
            start = first[1]
            dcmd = [f"M {start.x:.3f} {start.y:.3f}"]
        elif first[0] == "c":
            start = first[1]
            dcmd = [f"M {start.x:.3f} {start.y:.3f}"]
        else:
            dcmd = []
        for it in items:
            dcmd.append(item_to_d(it))
        dcmd.append("Z")
        parts.append(" ".join(dcmd))
    if not parts:
        print("no paths for", out_path)
        return
    vb = f"{x0 - pad} {y0 - pad} {w + 2 * pad} {h + 2 * pad}"
    paths = "\n".join(
        f'  <path fill="#781DFF" d="{p}"/>' for p in parts
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" fill="none">
{paths}
</svg>
'''
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("svg", out_path, "paths", len(parts))


def make_transparent_mark(src, dest, size=256):
    im = Image.open(src).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r > 235 and g > 235 and b > 235:
                px[x, y] = (0, 0, 0, 0)
            elif r > 70 and r < 190 and g < 90 and b > 170:
                px[x, y] = VIOLET
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    im.save(dest)
    print("png", dest, im.size)


def crop_lockup(page, dest, clip, matrix=fitz.Matrix(4, 4)):
    pix = page.get_pixmap(matrix=matrix, clip=fitz.Rect(*clip), alpha=True)
    pix.save(dest)
    print("crop", dest, pix.width, pix.height)


def main():
    doc = fitz.open(PDF)
    p4 = doc[3]
    p8 = doc[7]

    # Mark-only from page 4 (already rasterized once).
    src_mark = os.path.join(ASSETS, "logo-mark-from-p04.png")
    make_transparent_mark(src_mark, os.path.join(WEB, "logo-mark.png"), 256)
    make_transparent_mark(src_mark, os.path.join(WEB, "favicon.png"), 64)

    # Vector mark from purple leftover paths (circle minus chevrons).
    drawings_to_svg(
        p4,
        {"#771CFF", "#781DFF"},
        (479.0, 360.0, 659.0, 540.0),
        os.path.join(WEB, "logo-mark.svg"),
    )

    # Horizontal lockup: mark + wordmark.
    crop_lockup(p4, os.path.join(ASSETS, "logo-horizontal-lockup.png"), (470, 350, 1440, 550))

    # Avatar (first dark circle on page 8) — keep as reference.
    crop_lockup(p8, os.path.join(ASSETS, "logo-avatar-dark.png"), (360, 280, 720, 720))


if __name__ == "__main__":
    main()
