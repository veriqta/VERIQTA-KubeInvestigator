"""Render original SVG social art and an honest slideshow of real captured states."""

import hashlib
import json
from pathlib import Path
from PIL import Image, __version__ as pillow_version

root = Path(__file__).resolve().parents[1]
frames = []
for name in ["overview", "report", "evidence", "followup"]:
    with Image.open(root / f"docs/assets/screenshots/{name}.png") as image:
        image.thumbnail((960, 1000))
        frame = Image.new("RGB", (960, 1000), "#f5f7f5")
        frame.paste(image, ((960 - image.width) // 2, 0))
        frames.append(frame.quantize(colors=96))
frames[0].save(
    root / "docs/assets/demos/investigation.gif",
    save_all=True,
    append_images=frames[1:],
    duration=[1800, 2200, 2200, 2200],
    loop=0,
    optimize=True,
)
# Keep the derivative GIF tied to the captured source states.
manifest_path = root / "docs/assets/capture-manifest.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    relative = "demos/investigation.gif"
    manifest["assets"] = [asset for asset in manifest["assets"] if asset["file"] != relative]
    manifest["assets"].append(
        {
            "file": relative,
            "sha256": hashlib.sha256((root / "docs/assets" / relative).read_bytes()).hexdigest(),
        }
    )
    manifest.setdefault("authoring_tools", {})["Pillow"] = pillow_version
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
# Social art SVG-to-PNG is rendered by render-brand.cjs.
print("Generated real-capture demonstration GIF.")
