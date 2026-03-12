"""Todoist Label Todo integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_TOKEN, CONF_LABELS, DOMAIN
from .coordinator import TodoistLabelCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["todo"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Todoist Label Todo from a config entry."""
    api_token = entry.data[CONF_API_TOKEN]
    labels = entry.options.get(CONF_LABELS, [])

    coordinators: dict[str, TodoistLabelCoordinator] = {}
    for label in labels:
        coordinator = TodoistLabelCoordinator(hass, api_token, label)
        await coordinator.async_config_entry_first_refresh()
        coordinators[label] = coordinator

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the entry when options change (e.g. labels added/removed)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
