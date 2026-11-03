# keybars for Home Assistant

A HACS custom integration (`custom_components/keybars`) that sends events to
keybars Pro through its webhook address on the relay. README.md has the
detail; this file is what to keep in mind while working here.

## Commands

- `make venv` once (Home Assistant and its test harness, pinned in
  `requirements-test.txt`), then `make check`: ruff (lint and format),
  then pytest.
- Home Assistant needs a recent Python (2026.10 wants 3.14.2+); CI runs in
  the `python:3.14` image.

## Keep in mind

- It only sends: Home Assistant usually runs on another machine, and keybars
  Pro has no network API, so there's no state to read (lights, modes). A
  device with a switch and selects waits on keybars Pro growing a local API.
- The relay takes `{"event", "repo", "branch"}` as JSON with
  `Authorization: Bearer <secret>`; it answers 401 for the secret, 404 for
  an unknown address, 202 for an event it ignores (relay's
  `providers/webhook.ts`).
- Event names must match the relay's pattern (lower case, up to 64):
  `event_name` in `api.py` checks before sending.
- `home` is the default prefix because keybars Pro's Home Assistant guide
  uses that label for its rules; keep them in step.
- `strings.json` and `translations/en.json` are the same file.

## Related repos (in ~/development)

- `relay`: the webhook endpoint this posts to.
- `keybars-pro`: the Home Assistant guide (`alerts.ts`, label `home`) whose
  rules these events are for.
