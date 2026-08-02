from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "14_qa/workbook_renders"
out = ROOT / "14_qa/workbook_contact_sheets"
if out.exists():
    for existing in out.glob("*.png"): existing.unlink()
out.mkdir(parents=True, exist_ok=True)
files = sorted(source.glob("*.png"))
font = ImageFont.load_default()
for page, start in enumerate(range(0, len(files), 4), 1):
    group = files[start:start+4]
    canvas = Image.new("RGB", (1800, 1300), "#D9E2E8")
    draw = ImageDraw.Draw(canvas)
    for idx, path in enumerate(group):
        image = Image.open(path).convert("RGB")
        image.thumbnail((860, 570))
        x = 30 + (idx % 2) * 890
        y = 45 + (idx // 2) * 625
        draw.rectangle((x-6, y-26, x+866, y+582), fill="white", outline="#526875", width=2)
        draw.text((x, y-20), path.stem, fill="#12304A", font=font)
        canvas.paste(image, (x, y))
    canvas.save(out / f"workbook-contact-{page:02d}.png")
print(f"Created {(len(files)+3)//4} contact sheets for {len(files)} workbook renders")
