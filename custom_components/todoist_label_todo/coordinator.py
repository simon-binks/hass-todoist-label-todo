"""DataUpdateCoordinator for Todoist Label Todo."""
from __future__ import annotations

import logging

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL, TODOIST_API_BASE

_LOGGER = logging.getLogger(__name__)


class TodoistLabelCoordinator(DataUpdateCoordinator[list[dict]]):
    """Coordinator to fetch tasks for a specific Todoist label."""

    def __init__(self, hass: HomeAssistant, api_token: str, label: str) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{label}",
            update_interval=SCAN_INTERVAL,
        )
        self._api_token = api_token
        self.label = label

    @property
    def _headers(self) -> dict[str, str]:
        """Return auth headers for the Todoist API."""
        return {"Authorization": f"Bearer {self._api_token}"}

    async def _async_update_data(self) -> list[dict]:
        """Fetch all tasks with the configured label from Todoist."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{TODOIST_API_BASE}/tasks/filter",
                headers=self._headers,
                params={"query": f"@{self.label}"},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                _LOGGER.debug("Todoist tasks/by_filter raw response: %s", data)
                return data if isinstance(data, list) else data.get("results", [])
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(
                f"Todoist API error {err.status}: {err.message}"
            ) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Todoist: {err}") from err

    async def async_close_task(self, task_id: str) -> None:
        """Mark a task as complete in Todoist."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{TODOIST_API_BASE}/tasks/{task_id}/close",
                headers=self._headers,
            ) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to close Todoist task %s: %s", task_id, err)
            raise

    async def async_reopen_task(self, task_id: str) -> None:
        """Mark a task as incomplete in Todoist."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                f"{TODOIST_API_BASE}/tasks/{task_id}/reopen",
                headers=self._headers,
            ) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to reopen Todoist task %s: %s", task_id, err)
            raise


async def fetch_labels(hass: HomeAssistant, api_token: str) -> list[str]:
    """Fetch all personal label names from Todoist. Used by config and options flows."""
    session = async_get_clientsession(hass)
    async with session.get(
        f"{TODOIST_API_BASE}/labels",
        headers={"Authorization": f"Bearer {api_token}"},
    ) as resp:
        _LOGGER.debug("Todoist /labels response status: %s", resp.status)
        resp.raise_for_status()
        data = await resp.json()
        _LOGGER.debug("Todoist /labels raw response: %s", data)
        items = data if isinstance(data, list) else data.get("results", [])
        return [label["name"] for label in items]
