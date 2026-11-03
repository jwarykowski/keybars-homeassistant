"""Lets Home Assistant load custom_components/keybars in the tests."""

import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield
