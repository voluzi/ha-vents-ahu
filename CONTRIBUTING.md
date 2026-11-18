# Contributing to Vents AHU

[Search existing issues](https://github.com/voluzi/ha-vents-ahu/issues) before starting. For a
new bug, include the software versions, the device model and firmware if
relevant, and a minimal reproduction. See [SECURITY.md](SECURITY.md) for
vulnerability reports.

## Development

Run these commands from the repository root:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements_test.txt aiovents==0.1.0
ruff check .
ruff format --check .
mypy --strict custom_components
pytest -q
```

Tests use a simulated client; no physical device is needed. The default harness
targets Home Assistant 2026.11.2. CI also checks 2025.4.4 and 2026.2.3.

## Releases

Set the integration version in `manifest.json` to match the release tag, with
no leading `v` in the manifest. The release workflow packages the tracked
integration files, including the brand images, as a ZIP attached to the
GitHub release.

## Brand images

Replace the placeholders under `custom_components/vents_ahu/brand/`. Supply a
256 × 256 pixel `icon.png` and a `logo.png` that preserves the brand's aspect
ratio, preferably landscape, with its shorter side between 128 and 256 pixels.
Optional high resolution files are `icon@2x.png` (512 × 512) and `logo@2x.png`
(shorter side 256–512 pixels). Use the same sizes for dark theme variants:
`dark_icon.png`, `dark_logo.png`, `dark_icon@2x.png`, and `dark_logo@2x.png`.
Use optimized PNGs with tightly trimmed edges; transparency is preferred.
See the [Home Assistant brand specification](https://contributors.home-assistant.io/core/integrations/brands/).

## Pull requests

Keep changes focused. Include a regression test for a behavior change when
practical, and update the README and changelog when users need to know about
the change. Describe what changed and how you verified it.

Use synthetic or redacted logs, configuration and fixtures. Remove private
addresses, hostnames, device identifiers, credentials and location information.
