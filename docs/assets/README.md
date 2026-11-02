# Visual asset inventory and regeneration

The supplied VERIQTA mark is retained in brand/veriqta-supplied.png with its original pixel data and colour profile. Embedded EXIF/XMP metadata was removed during the pre-push privacy review; no visual redesign was made. It is user-supplied brand material; no independent trademark/brand licence was provided. Apache-2.0 for code does not grant endorsement or unrestricted rights in that supplied mark. Original project graphics are code-native SVG, distinct from the supplied company identity. Palette (#0b3029, #075745, #edf4ec, #fafcf8) is a restrained project treatment, not a claim of an official corporate standard.

| Files | Purpose / source / licence | Mode and capture version | Regenerate |
| --- | --- | --- | --- |
| brand/veriqta-supplied.png | User-supplied VERIQTA identity; rights reserved to respective owner | Brand, no investigation | Replace only with authorised original |
| brand/project-light.svg, project-dark.svg | Original project mark and wordmark; Apache-2.0 | Not a screenshot | Edit SVG source, verify contrast on light/dark surfaces |
| brand/hero.svg | Original README banner; Apache-2.0 | Not a screenshot | Edit SVG source; all essential text also in README |
| brand/social-preview.png | Raster rendering of original hero; Apache-2.0 | Not a product screenshot | `node scripts/render-brand.cjs` with sharp |
| diagrams/*.mmd, *.svg | Original editable diagram sources and GitHub-compatible SVGs; Apache-2.0 | Architecture, not evaluation data | Edit source and SVG together; verify against architecture.md |
| screenshots/overview.png | Real authenticated UI overview; Apache-2.0 | 0.1.0 local working tree, MOCK + fixture | capture.cjs |
| screenshots/report.png | Real Service selector report; Apache-2.0 | 0.1.0 local working tree, MOCK + fixture | capture.cjs |
| screenshots/evidence.png | Expanded real evidence panel; Apache-2.0 | 0.1.0 local working tree, MOCK + fixture | capture.cjs |
| screenshots/followup.png | Real linked follow-up and honest fixture limitation; Apache-2.0 | 0.1.0 local working tree, MOCK + fixture | capture.cjs |
| screenshots/mobile.png | Real narrow responsive layout; Apache-2.0 | 0.1.0 local working tree, MOCK + fixture | capture.cjs |
| demos/investigation.webm | Actual browser screen recording of the workflow; Apache-2.0 | 0.1.0 local working tree, MOCK + fixture | capture.cjs |
| demos/investigation.gif | Optimised sequence of genuine captured states; Apache-2.0 | MOCK + fixture, static fallback overview.png | `python scripts/assets.py` with Pillow |

The capture-manifest.json records capture timestamps, tool versions, a source fingerprint and SHA-256 hashes for the genuine screenshots/video/GIF. The source was an uncommitted 0.1.0 working tree, so no commit ID is invented. The storage-recovery diagram documents the offline lease/backup/restore sequence; it is an illustration, not test evidence.

## Capture procedure

Use Node 22+ and the pinned optional tooling (not application runtime dependencies):

```sh
pnpm install --frozen-lockfile --dir scripts/asset-tools
pnpm --dir scripts/asset-tools exec playwright install chromium
python3.12 -m venv .venv-assets
.venv-assets/bin/pip install -r scripts/asset-tools/requirements.lock
```

 Run a fresh server using a separate database (`KI_DATABASE=.capture/reports.db`), KI_PROVIDER=mock and KI_SOURCE=fixture. Store its generated team token in a private file excluded from Git. Set KI_CAPTURE_TOKEN_FILE to that file and run:

```sh
NODE_PATH="$PWD/scripts/asset-tools/node_modules" node scripts/capture.cjs
.venv-assets/bin/python scripts/assets.py
NODE_PATH="$PWD/scripts/asset-tools/node_modules" node scripts/check_readme.cjs
```

The capture script refuses non-mock/non-fixture configuration. Regenerate the manifest when regenerating assets. The script signs in with a password input, runs three scenarios, opens evidence, follows up, and records a narrow screen. It asserts browser errors and expected completion, and records only synthetic public example names. It does not imply actual cluster recovery or live-model quality. Reset the capture DB while the server is stopped for reproducibility. Do not use a real cluster or live provider for committed screenshots.

Inspect every PNG and the video for credentials/private data. Keep MOCK and fixture labels visible. Check at 1440px and 390px and inspect light/dark SVG variants; GitHub screenshots retain the application's light palette, with descriptive alt text. The hero/diagrams are light/dark-safe opaque graphics. Optimise PNGs and GIF palette; target a few hundred KB per screenshot and a few MB per recording. Never generate simulated product screenshots or leave blank media files. Social-preview upload is a GitHub owner setup task; this work does not change repository settings.

## Third-party technology marks

`third-party/python.svg`, `fastapi.svg`, `kubernetes.svg` and `sqlite.svg` come from the [Simple Icons collection](https://github.com/simple-icons/simple-icons), retrieved from its develop/icons directory on 2026-11-01. The collection distributes icon artwork under [CC0-1.0](https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md); underlying names and trademarks remain subject to their respective owners' rules. Source links: [Python](https://github.com/simple-icons/simple-icons/blob/develop/icons/python.svg), [FastAPI](https://github.com/simple-icons/simple-icons/blob/develop/icons/fastapi.svg), [Kubernetes](https://github.com/simple-icons/simple-icons/blob/develop/icons/kubernetes.svg), [SQLite](https://github.com/simple-icons/simple-icons/blob/develop/icons/sqlite.svg). No partnership or endorsement is implied. `brand/technology-strip.svg` incorporates these paths with plain technology labels and the project palette; regenerate with `node scripts/render-brand.cjs` using sharp. The same script rasterises social-preview.png. `scripts/assets.py` needs Pillow for GIF creation; these are optional authoring tools, not application runtime dependencies. Browser capture needs Playwright and Chromium as described above.

## Audit capture verification

The latest capture run uses the running 0.1.0 application with MOCK provider and synthetic fixture evidence. It waits for each newly submitted report ID, validates the JSON download, expands evidence using Enter, and verifies the follow-up explicitly cannot establish real recovery. `scripts/check_readme.cjs` renders README local images and navigation anchors in light/dark desktop and narrow layouts; real remote badges also loaded successfully; exact hosted GitHub rendering is unverified. Preview captures live under ignored `.capture/readme/`, not product screenshots. Application screenshots/video remain under this inventory's paths; GIF generation uses those genuine states.
