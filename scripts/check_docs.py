"""Check repository-relative Markdown links, assets and accidental secret patterns."""

import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
errors = []
for file in [
    root / "README.md",
    *root.glob("docs/**/*.md"),
    *root.glob("examples/*.md"),
    root / "CONTRIBUTING.md",
    root / "SECURITY.md",
]:
    for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", file.read_text()):
        if target.startswith(("http:", "https:", "#", "mailto:")):
            continue
        target = target.split("#")[0]
        if target and not (file.parent / target).exists():
            errors.append(f"{file.relative_to(root)}: missing {target}")
for file in root.glob("docs/assets/**/*.svg"):
    try:
        ET.parse(file)
    except ET.ParseError:
        errors.append(f"Malformed SVG: {file}")
for file in root.glob("docs/assets/**/*"):
    if file.is_file() and file.stat().st_size == 0:
        errors.append(f"Empty asset: {file}")
# This is a supplemental source check, not a replacement for gitleaks/history review.
for base in ["src", "tests", "examples", "docs"]:
    for file in (root / base).rglob("*"):
        if file.suffix not in {".py", ".js", ".md", ".yaml", ".json", ".html"}:
            continue
        text = file.read_text()
        if re.search(r"sk-[A-Za-z0-9]{20,}", text):
            errors.append(f"Possible provider credential: {file}")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("Relative links, SVG/XML, nonempty assets and supplemental credential-pattern checks passed.")
