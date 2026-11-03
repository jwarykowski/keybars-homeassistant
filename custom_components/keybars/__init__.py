"""keybars: send events from Home Assistant to keybars Pro's alert rules,
through the webhook address keybars Pro made on its relay."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .api import KeybarsError, event_name, send
from .const import CONF_ADDRESS, CONF_PREFIX, CONF_SECRET, DEFAULT_PREFIX, DOMAIN

PLATFORMS = [Platform.NOTIFY]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SEND_EVENT_SCHEMA = vol.Schema(
    {
        vol.Required("event"): cv.string,
        vol.Optional("repo"): cv.string,
        vol.Optional("branch"): cv.string,
    }
)


async def send_event(
    hass: HomeAssistant, entry: ConfigEntry, event: str, repo: str | None = None, branch: str | None = None
) -> None:
    """Sends an event through the entry's webhook, as Home Assistant errors."""
    try:
        name = event_name(entry.options.get(CONF_PREFIX, entry.data.get(CONF_PREFIX, DEFAULT_PREFIX)), event)
    except KeybarsError as err:
        raise ServiceValidationError(str(err)) from err
    try:
        await send(
            async_get_clientsession(hass), entry.data[CONF_ADDRESS], entry.data.get(CONF_SECRET), name, repo, branch
        )
    except KeybarsError as err:
        raise HomeAssistantError(f"keybars: {err}") from err


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Registers keybars.send_event."""

    async def handle(call: ServiceCall) -> None:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError("keybars isn't set up: add it under Settings, Devices & services")
        await send_event(hass, entries[0], call.data["event"], call.data.get("repo"), call.data.get("branch"))

    hass.services.async_register(DOMAIN, "send_event", handle, schema=SEND_EVENT_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
