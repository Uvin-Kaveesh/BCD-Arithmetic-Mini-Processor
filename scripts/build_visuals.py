"""Build portfolio visuals from the project's recorded Proteus screenshots.

Requires Pillow. The GIF is an illustrated walkthrough, not a live capture.
"""

from pathlib import Path
import os
import shutil
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
NAVY = "#0b1220"
PANEL = "#142238"
TEXT = "#edf5ff"
MUTED = "#a6bbcf"
CYAN = "#59d8d0"
BLUE = "#6ca9ff"
AMBER = "#ffca72"


def font(size: int, bold: bool = False):
    names = (
        ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold else
        ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def rounded(draw, box, fill, outline=None, radius=24, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def circuit_panel(canvas, source, box):
    draw = ImageDraw.Draw(canvas)
    rounded(draw, box, PANEL, "#31506d", 25, 2)
    x0, y0, x1, y1 = box
    img = Image.open(IMAGES / source).convert("RGB")
    img = ImageOps.contain(img, (x1 - x0 - 44, y1 - y0 - 76), Image.Resampling.LANCZOS)
    canvas.paste(img, (x0 + (x1 - x0 - img.width) // 2, y0 + 46 + (y1 - y0 - 76 - img.height) // 2))
    draw.text((x0 + 22, y0 + 16), "PROTEUS SCHEMATIC", font=font(17, True), fill=MUTED)


def hero():
    im = Image.new("RGB", (1600, 650), NAVY)
    d = ImageDraw.Draw(im)
    d.ellipse((-270, -300, 470, 440), fill="#102f43")
    d.ellipse((1320, 380, 1800, 860), fill="#112c42")
    d.text((88, 72), "DIGITAL LOGIC  /  PROTEUS", font=font(24, True), fill=CYAN)
    d.text((88, 150), "BCD Arithmetic", font=font(68, True), fill=TEXT)
    d.text((88, 232), "Mini Processor", font=font(68, True), fill=TEXT)
    d.text((92, 345), "Two BCD inputs. Three arithmetic paths.", font=font(29), fill=MUTED)
    d.text((92, 385), "One selected decimal result.", font=font(29), fill=MUTED)
    chips = [("ADD", CYAN), ("SUBTRACT", BLUE), ("MULTIPLY", AMBER)]
    x = 88
    for label, color in chips:
        w = 70 + len(label) * 15
        rounded(d, (x, 493, x + w, 548), "#1b3045", color, 16)
        d.text((x + 26, 505), label, font=font(22, True), fill=color)
        x += w + 17
    circuit_panel(im, "main-circuit.png", (825, 67, 1536, 584))
    im.save(IMAGES / "hero.png", optimize=True)


def social_preview():
    source = Image.open(IMAGES / "hero.png").convert("RGB")
    source = source.resize((1280, 520), Image.Resampling.LANCZOS)
    preview = Image.new("RGB", (1280, 640), NAVY)
    preview.paste(source, (0, 60))
    preview.save(IMAGES / "social-preview.png", optimize=True)


def slide(kicker, title, detail, expression, source, color, step):
    im = Image.new("RGB", (1200, 675), NAVY)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 1200, 13), radius=0, fill=color)
    d.text((65, 48), kicker, font=font(19, True), fill=color)
    d.text((64, 110), title, font=font(50, True), fill=TEXT)
    for line_no, line in enumerate(textwrap.wrap(detail, width=39)):
        d.text((66, 190 + line_no * 33), line, font=font(23), fill=MUTED)
    rounded(d, (65, 263, 557, 407), PANEL, "#31506d", 24)
    d.text((91, 290), expression, font=font(48, True), fill=color)
    d.text((65, 537), f"{step:02d} / 04", font=font(18, True), fill=MUTED)
    d.text((65, 584), "Illustrated walkthrough from recorded project schematics", font=font(17), fill=MUTED)
    circuit_panel(im, source, (616, 43, 1152, 631))
    return im


def walkthrough():
    frames = [
        slide("01  /  INPUT AND CONTROL", "Select an operation", "Two single digit BCD operands enter the datapath.", "00  /  01  /  10", "main-circuit.png", CYAN, 1),
        slide("02  /  BCD ADDITION", "Correct the binary sum", "Add six when needed to form valid BCD digits.", "4 + 5 = 09", "bcd-adder.png", BLUE, 2),
        slide("03  /  SUBTRACTION", "Reuse the adder", "Two's complement supports A minus B and a sign signal.", "9 - 3 = 06", "main-circuit.png", CYAN, 3),
        slide("04  /  MULTIPLICATION", "Convert for display", "Partial products form binary; conversion yields BCD.", "7 x 8 = 56", "binary-multiplier.png", AMBER, 4),
    ]
    # A compact GIF works directly in GitHub's README. No simulated motion is implied.
    frames[0].save(
        IMAGES / "walkthrough.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[1800, 2200, 2200, 2600],
        loop=0,
        optimize=True,
        disposal=2,
    )


def video():
    ffmpeg = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ffmpeg:
        print("MP4 skipped: set FFMPEG_BIN to an FFmpeg executable to rebuild it")
        return
    subprocess.run(
        [
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(IMAGES / "walkthrough.gif"),
            "-vf", "fps=24,pad=1200:676:0:0,format=yuv420p",
            "-c:v", "mpeg4", "-q:v", "3",
            str(ROOT / "docs" / "visual-walkthrough.mp4"),
        ],
        check=True,
    )


if __name__ == "__main__":
    hero()
    social_preview()
    walkthrough()
    video()
    for name in ("hero.png", "social-preview.png", "walkthrough.gif"):
        p = IMAGES / name
        print(name, p.stat().st_size)

