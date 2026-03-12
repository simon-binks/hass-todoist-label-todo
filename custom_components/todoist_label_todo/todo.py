"""Todo platform for Todoist Label Todo."""
from __future__ import annotations

import logging

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TodoistLabelCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one todo entity per configured label."""
    coordinators: dict[str, TodoistLabelCoordinator] = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TodoistLabelTodoEntity(coordinator) for coordinator in coordinators.values()
    )


class TodoistLabelTodoEntity(CoordinatorEntity[TodoistLabelCoordinator], TodoListEntity):
    """A todo list entity backed by a Todoist label."""

    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM
    _attr_has_entity_name = True

    def __init__(self, coordinator: TodoistLabelCoordinator) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"todoist_label_{coordinator.label}"
        self._attr_name = coordinator.label

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return current todo items, mapped from Todoist tasks."""
        if not self.coordinator.data:
            return []
        return [
            TodoItem(
                uid=task["id"],
                summary=task["content"],
                status=(
                    TodoItemStatus.COMPLETED
                    if task.get("is_completed")
                    else TodoItemStatus.NEEDS_ACTION
                ),
            )
            for task in self.coordinator.data
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Handle a status change on a todo item."""
        if item.status == TodoItemStatus.COMPLETED:
            await self.coordinator.async_close_task(item.uid)
        elif item.status == TodoItemStatus.NEEDS_ACTION:
            await self.coordinator.async_reopen_task(item.uid)
        await self.coordinator.async_request_refresh()
