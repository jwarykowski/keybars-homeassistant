# keybars for Home Assistant

A [Home Assistant](https://www.home-assistant.io) integration for
[keybars Pro](https://keybars.app/pro/): any automation can light your
keyboard. The doorbell rang, the washing's done, someone's home.

It sends events to keybars Pro's alert rules through the webhook address
keybars Pro makes on its relay, so it works wherever Home Assistant runs:
a Raspberry Pi, a NAS, the cloud. No YAML.

- **`keybars.send_event`**: an action that sends an event, e.g. `doorbell`,
  which goes as `home.doorbell`. Optionally with a repository and branch,
  for rules that name one (a room, say).
- **`notify.keybars_pro`**: a notify entity; its message is the event, its
  title the repository.

## requirements

- keybars Pro with a licence, and its Home Assistant connection (or Any
  webhook) added under Connections
- Home Assistant 2024.6 or later

## install

With [HACS](https://hacs.xyz): HACS, the menu, **Custom repositories**, add
`https://github.com/jwarykowski/keybars-homeassistant` as an Integration,
then download **keybars** and restart Home Assistant.

Without HACS: copy `custom_components/keybars` into your configuration's
`custom_components` folder and restart.

Then **Settings**, **Devices & services**, **Add integration**, **keybars**,
and paste the webhook address (and secret, if keybars Pro shows one) from
keybars Pro's Home Assistant page. A test event checks them.

## use

In an automation:

```yaml
actions:
  - action: keybars.send_event
    data:
      event: doorbell
```

or

```yaml
actions:
  - action: notify.send_message
    target:
      entity_id: notify.keybars_pro
    data:
      message: washing.done
      title: laundry
```

Then light something for it in keybars Pro: its Home Assistant page sets
up rules for `home.doorbell` and `home.washing.done`, and any rule can use
an event of your own.

Events go out as `<prefix>.<event>`. The prefix is `home`, as keybars Pro's
Home Assistant rules expect; change it under the integration's
**Configure**.

## development

```sh
make venv    # Home Assistant and its test harness, in .venv
make check   # ruff, then pytest
```

The tests run the integration in a test Home Assistant
(`pytest-homeassistant-custom-component`) against a mocked relay.

## licence

MIT
