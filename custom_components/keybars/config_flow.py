"""Setting keybars up: the webhook address from keybars Pro, and its secret."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
import voluptuous as vol

from .api import KeybarsError, NotFound, SecretNeeded, event_name, send
from .const import CONF_ADDRESS, CONF_PREFIX, CONF_SECRET, DEFAULT_PREFIX, DOMAIN

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
        vol.Optional(CONF_SECRET): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        vol.Optional(CONF_PREFIX, default=DEFAULT_PREFIX): str,
    }
)


class KeybarsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().rstrip("/")
            secret = (user_input.get(CONF_SECRET) or "").strip() or None
            prefix = user_input.get(CONF_PREFIX, DEFAULT_PREFIX).strip().strip(".").lower()
            if not address.startswith("https://") or "/h/" not in address:
                errors[CONF_ADDRESS] = "not_an_address"
            else:
                try:
                    # a test event checks the address and secret
                    await send(async_get_clientsession(self.hass), address, secret, event_name(prefix, "test"))
                except SecretNeeded:
                    errors[CONF_SECRET] = "secret_needed"
                except NotFound:
                    errors[CONF_ADDRESS] = "not_found"
                except KeybarsError:
                    errors["base"] = "cannot_connect"
            if not errors:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                data = {CONF_ADDRESS: address, CONF_PREFIX: prefix}
                if secret:
                    data[CONF_SECRET] = secret
                return self.async_create_entry(title="keybars Pro", data=data)
        return self.async_show_form(
            step_id="user", data_schema=self.add_suggested_values_to_schema(SCHEMA, user_input), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return KeybarsOptionsFlow()


class KeybarsOptionsFlow(OptionsFlow):
    """Changes the prefix events go out with."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_PREFIX: user_input[CONF_PREFIX].strip().strip(".").lower()})
        prefix = self.config_entry.options.get(CONF_PREFIX, self.config_entry.data.get(CONF_PREFIX, DEFAULT_PREFIX))
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema({vol.Optional(CONF_PREFIX, default=prefix): str})
        )
