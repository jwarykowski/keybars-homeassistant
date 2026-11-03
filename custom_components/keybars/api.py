"""Sending events to keybars Pro through its webhook address on the relay."""

from __future__ import annotations

import re

import aiohttp

# what the relay takes as an event name
EVENT = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class KeybarsError(Exception):
    """The relay didn't take the event; the message says why."""


class SecretNeeded(KeybarsError):
    """The webhook needs its secret, or was given the wrong one."""


class NotFound(KeybarsError):
    """No webhook at that address: it was removed, or mistyped."""


def event_name(prefix: str, event: str) -> str:
    """The event as rules see it: home.doorbell for doorbell, in lower case.

    An event already starting with the prefix keeps it once.
    """
    event = event.strip().lower()
    prefix = prefix.strip().strip(".").lower()
    if prefix and not event.startswith(prefix + "."):
        event = f"{prefix}.{event}"
    if not EVENT.match(event):
        raise KeybarsError(f'"{event}" isn\'t an event name: letters, digits, dots, dashes and underscores, up to 64')
    return event


async def send(
    session: aiohttp.ClientSession,
    address: str,
    secret: str | None,
    event: str,
    repo: str | None = None,
    branch: str | None = None,
) -> None:
    """Posts an event to the webhook address, raising KeybarsError when it isn't taken."""
    body: dict[str, str] = {"event": event}
    if repo:
        body["repo"] = repo
    if branch:
        body["branch"] = branch
    headers = {"Authorization": f"Bearer {secret}"} if secret else {}
    try:
        async with session.post(
            address.rstrip("/"), json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        ) as res:
            if res.status in (401, 403):
                raise SecretNeeded("the webhook needs its secret, or the secret is wrong")
            if res.status == 404:
                raise NotFound("there's no webhook at that address")
            if res.status >= 400:
                raise KeybarsError(f"the relay answered {res.status}: {(await res.text())[:200]}")
            if res.status == 202:
                raise KeybarsError(f'the relay ignored "{event}": not an event name it takes')
    except aiohttp.ClientError as err:
        raise KeybarsError(f"couldn't reach the relay: {err}") from err
    except TimeoutError as err:
        raise KeybarsError("the relay didn't answer in time") from err
