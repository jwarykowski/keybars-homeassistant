"""keybars in a test Home Assistant, against a mocked relay."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.keybars.api import KeybarsError, event_name
from custom_components.keybars.const import DOMAIN

ADDRESS = "https://relay.keybars.app/h/abc123"


def test_event_names():
    assert event_name("home", "doorbell") == "home.doorbell"
    assert event_name("home", "Home.Washing.Done ") == "home.washing.done"
    assert event_name("", "doorbell") == "doorbell"
    assert event_name(".home.", "doorbell") == "home.doorbell"
    with pytest.raises(KeybarsError):
        event_name("home", "door bell")
    with pytest.raises(KeybarsError):
        event_name("home", "x" * 70)


async def start(hass: HomeAssistant, aioclient_mock, secret: str | None = "s3cret", prefix="home") -> MockConfigEntry:
    aioclient_mock.post(ADDRESS, json={"event": "x", "delivered": 1})
    data = {"address": ADDRESS, "prefix": prefix}
    if secret:
        data["secret"] = secret
    entry = MockConfigEntry(domain=DOMAIN, data=data, unique_id=ADDRESS, title="keybars Pro")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def last(aioclient_mock):
    method, url, data, headers = aioclient_mock.mock_calls[-1][:4]
    return method, str(url), data, headers


async def test_setup(hass: HomeAssistant, aioclient_mock):
    aioclient_mock.post(ADDRESS, json={"event": "home.test", "delivered": 1})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"address": ADDRESS + "/", "secret": " s3cret ", "prefix": "home"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"address": ADDRESS, "prefix": "home", "secret": "s3cret"}
    method, url, data, headers = last(aioclient_mock)
    assert (method, url, data) == ("POST", ADDRESS, {"event": "home.test"})
    assert headers["Authorization"] == "Bearer s3cret"


@pytest.mark.parametrize(
    ("status", "field", "error"),
    [(401, "secret", "secret_needed"), (404, "address", "not_found"), (500, "base", "cannot_connect")],
)
async def test_setup_errors(hass: HomeAssistant, aioclient_mock, status, field, error):
    aioclient_mock.post(ADDRESS, status=status, json={"error": "no"})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"address": ADDRESS})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {field: error}


async def test_setup_wants_a_webhook_address(hass: HomeAssistant, aioclient_mock):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"address": "http://example.com"})
    assert result["errors"] == {"address": "not_an_address"}
    assert aioclient_mock.call_count == 0


async def test_one_entry(hass: HomeAssistant, aioclient_mock):
    await start(hass, aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT


async def test_send_event(hass: HomeAssistant, aioclient_mock):
    await start(hass, aioclient_mock)
    await hass.services.async_call(DOMAIN, "send_event", {"event": "doorbell", "repo": "front door"}, blocking=True)
    method, url, data, headers = last(aioclient_mock)
    assert data == {"event": "home.doorbell", "repo": "front door"}
    assert headers["Authorization"] == "Bearer s3cret"


async def test_no_secret_no_header(hass: HomeAssistant, aioclient_mock):
    await start(hass, aioclient_mock, secret=None)
    await hass.services.async_call(DOMAIN, "send_event", {"event": "doorbell"}, blocking=True)
    assert "Authorization" not in (last(aioclient_mock)[3] or {})


async def test_notify(hass: HomeAssistant, aioclient_mock):
    await start(hass, aioclient_mock)
    entity = next(s.entity_id for s in hass.states.async_all("notify"))
    assert entity == "notify.keybars_pro"
    await hass.services.async_call(
        "notify", "send_message", {"entity_id": entity, "message": "washing.done", "title": "laundry"}, blocking=True
    )
    assert last(aioclient_mock)[2] == {"event": "home.washing.done", "repo": "laundry"}


async def test_prefix_option(hass: HomeAssistant, aioclient_mock):
    entry = await start(hass, aioclient_mock)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"prefix": "flat."})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    await hass.services.async_call(DOMAIN, "send_event", {"event": "doorbell"}, blocking=True)
    assert last(aioclient_mock)[2] == {"event": "flat.doorbell"}


async def test_errors(hass: HomeAssistant, aioclient_mock):
    await start(hass, aioclient_mock)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "send_event", {"event": "door bell"}, blocking=True)
    aioclient_mock.clear_requests()
    aioclient_mock.post(ADDRESS, status=401, json={"error": "secret"})
    with pytest.raises(HomeAssistantError, match="secret"):
        await hass.services.async_call(DOMAIN, "send_event", {"event": "doorbell"}, blocking=True)


async def test_unload(hass: HomeAssistant, aioclient_mock):
    entry = await start(hass, aioclient_mock)
    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ServiceValidationError, match="isn't set up"):
        await hass.services.async_call(DOMAIN, "send_event", {"event": "doorbell"}, blocking=True)
