"""Config flow for Todoist Label Todo."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_API_TOKEN, CONF_LABELS, DOMAIN
from .coordinator import fetch_labels

_LOGGER = logging.getLogger(__name__)


class TodoistLabelTodoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise."""
        self._api_token: str | None = None
        self._available_labels: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Ask for the Todoist API token and validate it."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_token = user_input[CONF_API_TOKEN]
            try:
                labels = await fetch_labels(self.hass, api_token)
            except aiohttp.ClientResponseError as err:
                errors["base"] = "invalid_auth" if err.status == 401 else "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            else:
                if not labels:
                    errors["base"] = "no_labels"
                else:
                    self._api_token = api_token
                    self._available_labels = labels
                    return await self.async_step_labels()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )

    async def async_step_labels(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Select which labels to sync."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected = user_input.get(CONF_LABELS, [])
            if not selected:
                errors["base"] = "no_labels_selected"
            else:
                await self._async_set_unique_id_and_abort_if_exists()
                return self.async_create_entry(
                    title="Todoist Label Todo",
                    data={CONF_API_TOKEN: self._api_token},
                    options={CONF_LABELS: selected},
                )

        return self.async_show_form(
            step_id="labels",
            data_schema=vol.Schema({
                vol.Required(CONF_LABELS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=self._available_labels,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }),
            errors=errors,
        )

    async def _async_set_unique_id_and_abort_if_exists(self) -> None:
        """Prevent duplicate config entries."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return TodoistLabelTodoOptionsFlow(config_entry)


class TodoistLabelTodoOptionsFlow(OptionsFlow):
    """Handle the options flow for adding/removing labels."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialise."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options form."""
        errors: dict[str, str] = {}
        api_token = self._config_entry.data[CONF_API_TOKEN]
        current_labels = self._config_entry.options.get(CONF_LABELS, [])

        if user_input is not None:
            selected = user_input.get(CONF_LABELS, [])
            if not selected:
                errors["base"] = "no_labels_selected"
            else:
                return self.async_create_entry(data={CONF_LABELS: selected})

        try:
            available_labels = await fetch_labels(self.hass, api_token)
        except aiohttp.ClientError:
            # Fall back to current labels if we can't reach Todoist
            available_labels = current_labels

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_LABELS, default=current_labels): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=available_labels,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }),
            errors=errors,
        )
