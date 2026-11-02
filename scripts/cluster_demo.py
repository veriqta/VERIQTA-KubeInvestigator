"""Create an explicitly static GIF sequence from genuine cluster browser captures."""

import hashlib
import json
from pathlib import Path

from PIL import Image, __version__

ROOT = Path(__file__).resolve().parents[1] / "docs/assets/cluster"
manifest = json.loads((ROOT / "manifest.json").read_text())
assert manifest["source"] == "kubernetes" and manifest["provider"] == "mock"
frames = []
for name in ["overview.png", "report.png", "evidence.png", "followup.png"]:
    recorded = next(row["sha256"] for row in manifest["assets"] if row["file"] == name)
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == recorded
    with Image.open(ROOT / name) as image:
        image.thumbnail((960, 1000))
        frame = Image.new("RGB", (960, 1000), "#f5f7f5")
        frame.paste(image, ((960 - image.width) // 2, 0))
        frames.append(frame.quantize(colors=96))
frames[0].save(
    ROOT / "investigation.gif",
    save_all=True,
    append_images=frames[1:],
    duration=[1600, 2200, 2200, 3200],
    loop=0,
    optimize=True,
)
manifest["assets"] = [row for row in manifest["assets"] if row["file"] != "investigation.gif"]
manifest["assets"].append(
    {
        "file": "investigation.gif",
        "sha256": hashlib.sha256((ROOT / "investigation.gif").read_bytes()).hexdigest(),
        "description": "Static sequence of genuine browser screenshots; not a continuous recording",
    }
)
manifest["gif_authoring"] = {
    "Pillow": __version__,
    "source_frames": ["overview.png", "report.png", "evidence.png", "followup.png"],
}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Generated honest static sequence from verified real-cluster captures.")
