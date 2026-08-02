from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "14_qa/pdf_contact_sheets"
if out.exists():
    for existing in out.glob("*.png"): existing.unlink()
out.mkdir(parents=True, exist_ok=True)
font = ImageFont.load_default()


def contacts(source: Path, prefix: str, per_page: int, cols: int, rows: int) -> None:
    files = sorted(source.glob("*.png"))
    for page, start in enumerate(range(0, len(files), per_page), 1):
        group = files[start:start+per_page]
        canvas = Image.new("RGB", (1800, 1200), "#D9E2E8")
        draw = ImageDraw.Draw(canvas)
        cell_w, cell_h = 1760 // cols, 1140 // rows
        for idx, path in enumerate(group):
            image = Image.open(path).convert("RGB")
            image.thumbnail((cell_w-30, cell_h-45))
            x = 20 + (idx % cols) * cell_w
            y = 35 + (idx // cols) * cell_h
            draw.rectangle((x-5, y-23, x+cell_w-12, y+cell_h-12), fill="white", outline="#526875", width=2)
            draw.text((x, y-18), path.stem, fill="#12304A", font=font)
            canvas.paste(image, (x, y))
        canvas.save(out / f"{prefix}-contact-{page:02d}.png")


contacts(ROOT / "14_qa/pdf_renders/qet_baseline", "qet-baseline", 6, 3, 2)
contacts(ROOT / "14_qa/pdf_renders/release_d", "release-evidence", 6, 3, 2)
print("Created PDF contact sheets")
