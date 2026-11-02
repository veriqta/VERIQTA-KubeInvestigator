"""Resolve the existing action release tags to immutable commits; never runs actions."""

import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = list((root / ".github/workflows").glob("*.yml"))
resolved = {}
for file in files:
    for repo, tag in re.findall(r"uses: ([\w.-]+/[\w.-]+)@([^\s#]+)", file.read_text()):
        if re.fullmatch(r"[0-9a-f]{40}", tag):
            continue
        key = repo + "@" + tag
        if key in resolved:
            continue
        output = subprocess.check_output(
            [
                "git",
                "ls-remote",
                "https://github.com/" + repo + ".git",
                "refs/tags/" + tag,
                "refs/tags/" + tag + "^{}",
            ],
            text=True,
            timeout=60,
        )
        refs = dict(line.split()[::-1] for line in output.splitlines())
        commit = refs.get("refs/tags/" + tag + "^{}", refs.get("refs/tags/" + tag))
        if not commit or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise RuntimeError("Cannot resolve action: " + key)
        resolved[key] = commit
for file in files:
    text = file.read_text()
    for key, commit in resolved.items():
        text = text.replace(
            "uses: " + key + "\n",
            "uses: " + key.split("@")[0] + "@" + commit + " # " + key.split("@")[1] + "\n",
        )
    file.write_text(text)
record = root / ".github/action-pins.json"
previous = json.loads(record.read_text()) if record.exists() else {}
previous.update(resolved)
record.write_text(json.dumps(previous, indent=2) + "\n")
print(f"Pinned {len(resolved)} action references; no workflow executed.")
