"""Generate the deterministic filing-derived raster used by OCR tests."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "ocr_fixture" / "filing_table_scan.png"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def centered(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.FreeTypeFont) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((1600 - (box[2] - box[0])) / 2, y), text, font=font, fill="#161616")


def main() -> None:
    image = Image.new("L", (1600, 1000), color=252)
    draw = ImageDraw.Draw(image)
    centered(draw, 55, "APPLE INC.", ImageFont.truetype(FONT_BOLD, 48))
    centered(
        draw,
        125,
        "CONSOLIDATED STATEMENTS OF OPERATIONS",
        ImageFont.truetype(FONT, 35),
    )
    centered(draw, 185, "USD millions - Fiscal year 2025", ImageFont.truetype(FONT, 28))
    draw.line((180, 270, 1420, 270), fill=25, width=3)
    body = ImageFont.truetype(FONT, 36)
    for y, label, value in (
        (325, "Total net sales", "416,161"),
        (435, "Operating income", "133,050"),
        (545, "Net income", "112,010"),
    ):
        draw.text((230, y), label, font=body, fill=20)
        box = draw.textbbox((0, 0), value, font=body)
        draw.text((1350 - (box[2] - box[0]), y), value, font=body, fill=20)
    draw.line((180, 640, 1420, 640), fill=25, width=3)
    centered(
        draw,
        700,
        "Source: Apple Inc. 2025 Form 10-K, page 28; SEC EDGAR",
        ImageFont.truetype(FONT, 25),
    )
    centered(
        draw,
        760,
        "Rasterized evaluation fixture - not the complete filing page",
        ImageFont.truetype(FONT, 22),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
