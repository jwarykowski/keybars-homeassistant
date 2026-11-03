"""notify.keybars: a notify entity whose message is the event to send."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import send_event
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    add([KeybarsNotify(entry)])


class KeybarsNotify(NotifyEntity):
    """Sends its message, an event name such as doorbell, to keybars Pro.

    A title, when given, goes as the event's repository, so a rule can light
    something different for, say, one room.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "keybars"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_notify"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "keybars Pro",
            "manufacturer": "keybars",
            "configuration_url": "https://keybars.app/pro/",
        }

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        await send_event(self.hass, self._entry, message, repo=title)
